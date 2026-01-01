"""
Hardware Communication Handler for Coca-Cola Sorting System (CONTINUOUS MODE)
Fast serial communication with Arduino for real-time control
"""

import serial
import time
import threading


class HardwareController:
    """
    Serial communication handler for Arduino (CONTINUOUS MODE)
    Optimized for fast response - sends decision immediately after AI
    """
    
    def __init__(self, port="/dev/ttyUSB0", baudrate=9600, timeout=0.1):
        """
        Initialize hardware controller
        
        Args:
            port: Serial port
            baudrate: Communication speed
            timeout: Read timeout (short for fast response)
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
        Connect to Arduino
        
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
            self.serial.close()
            print("[Hardware] Disconnected from Arduino")
        
        self.connected = False
    
    def send_command(self, command):
        """
        Send command to Arduino (FAST - no waiting)
        
        Args:
            command: Single character command ('O' or 'N')
            
        Returns:
            bool: True if sent successfully
        """
        if not self.connected:
            print("[WARNING] Not connected to Arduino")
            return False
        
        try:
            with self.lock:
                self.serial.write(command.encode())
                self.serial.flush()  # Ensure immediate transmission
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to send command '{command}': {e}")
            return False
    
    def send_ok(self):
        """Send OK decision to Arduino"""
        return self.send_command('O')
    
    def send_ng(self):
        """Send NG decision to Arduino"""
        return self.send_command('N')
    
    def start_conveyor(self):
        """Start conveyor belt (relay ON)"""
        print("[Hardware] Starting conveyor belt...")
        return self.send_command('S')
    
    def stop_conveyor(self):
        """Stop conveyor belt (relay OFF)"""
        print("[Hardware] Stopping conveyor belt...")
        return self.send_command('P')
    
    def start_listening(self, detection_callback):
        """
        Start listening for detection signals from Arduino
        
        Args:
            detection_callback: Function to call when 'D' is received
        """
        if self.listening:
            print("[WARNING] Already listening")
            return
        
        self.detection_callback = detection_callback
        self.listening = True
        
        self.listener_thread = threading.Thread(
            target=self._listen_loop,
            daemon=True
        )
        self.listener_thread.start()
        
        print("[Hardware] Started listening for detections")
    
    def stop_listening(self):
        """Stop listening thread"""
        if not self.listening:
            return
        
        print("[Hardware] Stopping listener...")
        self.listening = False
        
        if self.listener_thread:
            self.listener_thread.join(timeout=2.0)
        
        print("[Hardware] Listener stopped")
    
    def _listen_loop(self):
        """
        Main listening loop (runs in separate thread)
        Continuously reads serial port for 'D' signals
        """
        print("[Hardware] Listener thread started")
        
        buffer = ""
        
        while self.listening and self.connected:
            try:
                if self.serial.in_waiting > 0:
                    # Read available data
                    data = self.serial.read(self.serial.in_waiting).decode('utf-8', errors='ignore')
                    buffer += data
                    
                    # Process complete lines
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        if line:
                            self._process_line(line)
                else:
                    # No data available, small sleep to prevent CPU overload
                    time.sleep(0.01)
                    
            except Exception as e:
                print(f"[ERROR] Listener error: {e}")
                time.sleep(0.1)
        
        print("[Hardware] Listener thread stopped")
    
    def _process_line(self, line):
        """
        Process a line received from Arduino
        
        Args:
            line: String line from serial
        """
        # Check for detection signal
        if line.startswith('D'):
            # Detection signal received
            if self.detection_callback:
                # Parse timestamp if included (format: "D,timestamp")
                parts = line.split(',')
                timestamp = int(parts[1]) if len(parts) > 1 else None
                
                # Call callback
                self.detection_callback(timestamp)
            else:
                print("[WARNING] Detection received but no callback set")
        
        # Print other messages (debug, statistics, etc.)
        elif line.startswith('[') or line.startswith('-'):
            # Arduino debug/status messages
            print(f"[Arduino] {line}")
        elif "detected" in line.lower() or "decision" in line.lower():
            # Important messages
            print(f"[Arduino] {line}")
    
    def is_connected(self):
        """Check if connected to Arduino"""
        return self.connected
    
    def is_listening(self):
        """Check if listening for detections"""
        return self.listening


class DummyHardwareController:
    """
    Dummy hardware controller for testing without Arduino
    Simulates detection signals at regular intervals
    """
    
    def __init__(self, port="/dev/ttyUSB0", baudrate=9600, timeout=0.1):
        """Initialize dummy hardware"""
        print("[Hardware] Initializing DUMMY hardware controller...")
        
        self.port = port
        self.connected = False
        self.listening = False
        self.detection_callback = None
        self.simulator_thread = None
    
    def connect(self):
        """Simulate connection"""
        self.connected = True
        print("[Hardware] DUMMY hardware connected")
        return True
    
    def disconnect(self):
        """Simulate disconnection"""
        self.stop_listening()
        self.connected = False
        print("[Hardware] DUMMY hardware disconnected")
    
    def send_command(self, command):
        """Simulate sending command"""
        print(f"[Hardware] DUMMY send: {command}")
        return True
    
    def send_ok(self):
        """Simulate OK"""
        return self.send_command('O')
    
    def send_ng(self):
        """Simulate NG"""
        return self.send_command('N')
    
    def start_conveyor(self):
        """Simulate start conveyor"""
        print("[Hardware] DUMMY conveyor started")
        return True
    
    def stop_conveyor(self):
        """Simulate stop conveyor"""
        print("[Hardware] DUMMY conveyor stopped")
        return True
    
    def start_listening(self, detection_callback):
        """Start simulating detections"""
        self.detection_callback = detection_callback
        self.listening = True
        
        self.simulator_thread = threading.Thread(
            target=self._simulate_detections,
            daemon=True
        )
        self.simulator_thread.start()
        
        print("[Hardware] DUMMY listening started (will simulate detections)")
    
    def stop_listening(self):
        """Stop simulation"""
        self.listening = False
        if self.simulator_thread:
            self.simulator_thread.join(timeout=2.0)
        print("[Hardware] DUMMY listening stopped")
    
    def _simulate_detections(self):
        """Simulate bottle detections every 3 seconds"""
        print("[Hardware] DUMMY simulator thread started")
        
        while self.listening:
            time.sleep(3.0)  # Simulate detection every 3 seconds
            
            if self.listening and self.detection_callback:
                print("[Hardware] DUMMY detection simulated")
                self.detection_callback(None)
        
        print("[Hardware] DUMMY simulator thread stopped")
    
    def is_connected(self):
        """Check dummy connection"""
        return self.connected
    
    def is_listening(self):
        """Check dummy listening"""
        return self.listening
