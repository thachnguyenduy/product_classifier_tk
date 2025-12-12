# ============================================
# HARDWARE CONTROLLER - Serial Communication
# ============================================
"""
Serial communication with Arduino

Protocol:
- Raspberry Pi sends classification result to Arduino:
  - 'O' = OK product (servo allows bottle to pass)
  - 'N' = NG product (servo blocks bottle)
  - 'S' = Start conveyor
  - 'P' = Stop/Pause conveyor

- Arduino sends IR sensor trigger to Raspberry Pi:
  - 'T' = Bottle detected at IR sensor position

IMPORTANT:
- Classification is sent when bottle CROSSES the virtual line
- IR sensor detection happens later (physical sensor at servo position)
- Arduino reads LAST classification received and actuates servo accordingly
"""

import serial
import threading
import time
import config


class HardwareController:
    """
    Serial communication with Arduino
    
    Responsibilities:
    - Send classification results ('O' or 'N')
    - Send conveyor control commands ('S' or 'P')
    - Receive IR sensor triggers ('T')
    - Manage serial connection
    """
    
    def __init__(self):
        self.port = config.ARDUINO_PORT
        self.baudrate = config.ARDUINO_BAUDRATE
        self.timeout = config.ARDUINO_TIMEOUT
        
        self.serial = None
        self.connected = False
        self.listening = False
        self.thread = None
        
        self.trigger_callback = None
        self.last_classification = None  # Track last sent classification
        
        self._connect()
    
    def _connect(self):
        """Connect to Arduino"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            
            # Wait for Arduino to reset
            time.sleep(2)
            
            # Clear buffer
            if self.serial.in_waiting > 0:
                self.serial.read(self.serial.in_waiting)
            
            self.connected = True
            print(f"[Hardware] Connected to Arduino on {self.port}")
            print(f"[Hardware] Baudrate: {self.baudrate}")
            return True
            
        except serial.SerialException as e:
            print(f"[ERROR] Cannot connect to Arduino: {e}")
            print(f"[Hardware] Attempted port: {self.port}")
            print(f"[Hardware] Check connection and port configuration")
            self.connected = False
            return False
        except Exception as e:
            print(f"[ERROR] Hardware init failed: {e}")
            self.connected = False
            return False
    
    def start_listening(self, trigger_callback):
        """
        Start listening thread for IR sensor triggers
        
        Args:
            trigger_callback: Function to call when 'T' received from Arduino
        """
        if not self.connected:
            print("[ERROR] Cannot start listening: Not connected")
            return False
        
        self.trigger_callback = trigger_callback
        self.listening = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        print("[Hardware] Listening thread started")
        return True
    
    def _listen_loop(self):
        """Continuous listening loop"""
        while self.listening:
            try:
                if self.serial.in_waiting > 0:
                    data = self.serial.read(1).decode('utf-8', errors='ignore')
                    
                    if config.VERBOSE_LOGGING:
                        print(f"[Hardware] Received: '{data}'")
                    
                    # IR Sensor triggered
                    if data == config.CMD_TRIGGER:
                        print("[Hardware] IR sensor triggered!")
                        if self.trigger_callback:
                            self.trigger_callback()
                
                time.sleep(0.01)  # Small delay to prevent busy waiting
                    
            except Exception as e:
                if self.listening:  # Only log if still supposed to be listening
                    print(f"[ERROR] Serial read error: {e}")
                time.sleep(0.1)
    
    def send_classification(self, result):
        """
        Send classification result to Arduino
        
        Args:
            result: 'OK' or 'NG'
        
        Returns:
            bool: Success status
        """
        if result == 'OK':
            command = config.CMD_OK
        elif result == 'NG':
            command = config.CMD_NG
        else:
            print(f"[ERROR] Invalid classification result: {result}")
            return False
        
        success = self._send_command(command)
        if success:
            self.last_classification = result
            print(f"[Hardware] Sent classification: {result} ('{command}')")
        
        return success
    
    def start_conveyor(self):
        """Send start conveyor command"""
        success = self._send_command(config.CMD_START)
        if success:
            print("[Hardware] Conveyor START command sent")
        return success
    
    def stop_conveyor(self):
        """Send stop/pause conveyor command"""
        success = self._send_command(config.CMD_STOP)
        if success:
            print("[Hardware] Conveyor STOP command sent")
        return success
    
    def _send_command(self, cmd):
        """
        Send single character command to Arduino
        
        Args:
            cmd: Single character command string
        
        Returns:
            bool: Success status
        """
        if not self.connected:
            print("[ERROR] Cannot send command: Not connected")
            return False
        
        try:
            self.serial.write(cmd.encode('utf-8'))
            self.serial.flush()
            
            if config.VERBOSE_LOGGING:
                print(f"[Hardware] Sent command: '{cmd}'")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Send command failed: {e}")
            return False
    
    def stop(self):
        """Stop listening thread and close connection"""
        self.listening = False
        
        if self.thread is not None:
            self.thread.join(timeout=2.0)
        
        if self.serial is not None and self.serial.is_open:
            self.serial.close()
        
        self.connected = False
        print("[Hardware] Connection closed")
    
    def is_connected(self):
        """Check if connected to Arduino"""
        return self.connected


class DummyHardwareController:
    """
    Dummy hardware controller for testing without Arduino
    
    Simulates Arduino behavior for development and testing
    """
    
    def __init__(self):
        self.connected = True
        self.listening = False
        self.trigger_callback = None
        self.last_classification = None
        print("[Hardware] Using DUMMY hardware controller")
        print("[Hardware] No physical Arduino connected")
    
    def start_listening(self, trigger_callback):
        """Start dummy listening (simulates IR triggers)"""
        self.trigger_callback = trigger_callback
        self.listening = True
        
        # Simulate IR triggers every 5 seconds
        def simulate_triggers():
            while self.listening:
                time.sleep(5)
                if self.trigger_callback and self.listening:
                    print("[Hardware] DUMMY: IR sensor triggered!")
                    self.trigger_callback()
        
        threading.Thread(target=simulate_triggers, daemon=True).start()
        print("[Hardware] DUMMY: Listening started (triggers every 5s)")
        return True
    
    def send_classification(self, result):
        """Dummy send classification"""
        self.last_classification = result
        if result == 'OK':
            cmd = config.CMD_OK
        else:
            cmd = config.CMD_NG
        print(f"[Hardware] DUMMY: Classification sent: {result} ('{cmd}')")
        return True
    
    def start_conveyor(self):
        """Dummy start conveyor"""
        print("[Hardware] DUMMY: Conveyor STARTED")
        return True
    
    def stop_conveyor(self):
        """Dummy stop conveyor"""
        print("[Hardware] DUMMY: Conveyor STOPPED")
        return True
    
    def stop(self):
        """Dummy stop"""
        self.listening = False
        self.connected = False
        print("[Hardware] DUMMY: Stopped")
    
    def is_connected(self):
        """Always connected in dummy mode"""
        return True
