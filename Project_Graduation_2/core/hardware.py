"""
Hardware Communication Handler for Coca-Cola Sorting System
Manages serial communication with Arduino Uno
"""

import serial
import time
import threading


class HardwareController:
    """
    Serial communication handler for Arduino
    Implements the communication protocol for conveyor control and sorting
    """
    
    def __init__(self, port="/dev/ttyUSB0", baudrate=9600, timeout=1):
        """
        Initialize hardware controller
        
        Args:
            port: Serial port (e.g., '/dev/ttyUSB0' on Linux, 'COM3' on Windows)
            baudrate: Serial communication speed
            timeout: Read timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        
        self.serial = None
        self.connected = False
        self.lock = threading.Lock()
        
        self.detection_callback = None
        self.listener_thread = None
        self.listening = False
        
        print(f"[Hardware] Initializing on {port} @ {baudrate} baud")
    
    def connect(self):
        """
        Connect to Arduino via serial port
        
        Returns:
            bool: True if connected successfully
        """
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            
            # Wait for Arduino to reset
            time.sleep(2)
            
            # Clear buffer
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            
            self.connected = True
            print(f"[Hardware] Connected to Arduino on {self.port}")
            
            return True
            
        except serial.SerialException as e:
            print(f"[ERROR] Failed to connect to Arduino: {e}")
            print(f"[INFO] Make sure Arduino is connected to {self.port}")
            self.connected = False
            return False
        except Exception as e:
            print(f"[ERROR] Unexpected error connecting to Arduino: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from Arduino"""
        self.stop_listening()
        
        if self.serial and self.serial.is_open:
            try:
                self.serial.close()
                print("[Hardware] Disconnected from Arduino")
            except Exception as e:
                print(f"[ERROR] Error disconnecting: {e}")
        
        self.connected = False
    
    def is_connected(self):
        """Check if connected to Arduino"""
        return self.connected and self.serial and self.serial.is_open
    
    def send_command(self, command):
        """
        Send command to Arduino
        
        Args:
            command: Single character command ('O', 'N', 'S', 'X')
                - 'O': OK result (pass bottle)
                - 'N': NG result (reject bottle)
                - 'S': Start system
                - 'X': Stop system
        
        Returns:
            bool: True if sent successfully
        """
        if not self.is_connected():
            print("[WARNING] Cannot send command - not connected")
            return False
        
        try:
            with self.lock:
                self.serial.write(command.encode())
                self.serial.flush()
            
            print(f"[Hardware] Sent command: {command}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to send command '{command}': {e}")
            return False
    
    def send_ok(self):
        """Send OK result to Arduino"""
        return self.send_command('O')
    
    def send_ng(self):
        """Send NG result to Arduino"""
        return self.send_command('N')
    
    def send_start(self):
        """Send start system command"""
        return self.send_command('S')
    
    def send_stop(self):
        """Send stop system command"""
        return self.send_command('X')
    
    def read_line(self):
        """
        Read a line from Arduino
        
        Returns:
            str: Line read, or None if failed/timeout
        """
        if not self.is_connected():
            return None
        
        try:
            with self.lock:
                if self.serial.in_waiting > 0:
                    line = self.serial.readline().decode('utf-8').strip()
                    return line
            return None
            
        except Exception as e:
            print(f"[ERROR] Failed to read from Arduino: {e}")
            return None
    
    def start_listening(self, detection_callback):
        """
        Start listening thread for Arduino messages
        
        Args:
            detection_callback: Function to call when 'D' is received
                                Should accept no parameters
        """
        if self.listening:
            print("[Hardware] Already listening")
            return
        
        if not self.is_connected():
            print("[ERROR] Cannot start listening - not connected")
            return
        
        self.detection_callback = detection_callback
        self.listening = True
        
        self.listener_thread = threading.Thread(target=self._listen, daemon=True)
        self.listener_thread.start()
        
        print("[Hardware] Started listening for Arduino messages")
    
    def _listen(self):
        """Internal method to continuously listen for Arduino messages"""
        while self.listening and self.is_connected():
            try:
                line = self.read_line()
                
                if line:
                    # Print debug messages
                    if line.startswith('[') or line.startswith('Coca') or line.startswith('Bottle'):
                        print(f"[Arduino] {line}")
                    
                    # Check for detection signal
                    if line == 'D':
                        print("[Hardware] Detection signal received from Arduino!")
                        if self.detection_callback:
                            try:
                                self.detection_callback()
                            except Exception as e:
                                print(f"[ERROR] Detection callback error: {e}")
                
                time.sleep(0.05)  # Small delay
                
            except Exception as e:
                print(f"[ERROR] Listening error: {e}")
                time.sleep(0.5)
    
    def stop_listening(self):
        """Stop listening thread"""
        if not self.listening:
            return
        
        print("[Hardware] Stopping listener...")
        self.listening = False
        
        if self.listener_thread:
            self.listener_thread.join(timeout=2.0)
        
        print("[Hardware] Listener stopped")
    
    def test_connection(self):
        """
        Test Arduino connection by reading initial messages
        
        Returns:
            bool: True if communication is working
        """
        if not self.is_connected():
            print("[ERROR] Not connected")
            return False
        
        print("[Hardware] Testing connection...")
        
        try:
            # Read a few lines to check communication
            for _ in range(5):
                line = self.read_line()
                if line:
                    print(f"[Arduino] {line}")
                time.sleep(0.2)
            
            print("[Hardware] Connection test complete")
            return True
            
        except Exception as e:
            print(f"[ERROR] Connection test failed: {e}")
            return False
    
    def __del__(self):
        """Cleanup on deletion"""
        self.disconnect()


class DummyHardwareController(HardwareController):
    """
    Dummy hardware controller for testing without Arduino
    Simulates Arduino behavior
    """
    
    def __init__(self):
        super().__init__(port="DUMMY")
        print("[Hardware] Using DUMMY controller for testing")
    
    def connect(self):
        """Simulate connection"""
        print("[Hardware] DUMMY mode - Simulating Arduino connection")
        self.connected = True
        return True
    
    def disconnect(self):
        """Simulate disconnection"""
        self.stop_listening()
        self.connected = False
        print("[Hardware] DUMMY mode - Disconnected")
    
    def send_command(self, command):
        """Simulate sending command"""
        print(f"[Hardware] DUMMY mode - Sent command: {command}")
        return True
    
    def start_listening(self, detection_callback):
        """Start simulated listening"""
        if self.listening:
            return
        
        self.detection_callback = detection_callback
        self.listening = True
        
        # Start thread that simulates detections every 5 seconds
        self.listener_thread = threading.Thread(target=self._simulate_detections, daemon=True)
        self.listener_thread.start()
        
        print("[Hardware] DUMMY mode - Simulating detections every 5 seconds")
    
    def _simulate_detections(self):
        """Simulate bottle detections for testing"""
        detection_count = 0
        
        while self.listening:
            time.sleep(5)  # Simulate detection every 5 seconds
            
            if self.listening and self.detection_callback:
                detection_count += 1
                print(f"[Hardware] DUMMY mode - Simulating detection #{detection_count}")
                
                try:
                    self.detection_callback()
                except Exception as e:
                    print(f"[ERROR] Detection callback error: {e}")
    
    def test_connection(self):
        """Simulate connection test"""
        print("[Hardware] DUMMY mode - Connection test passed")
        return True

