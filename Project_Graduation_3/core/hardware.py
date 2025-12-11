# ============================================
# HARDWARE CONTROLLER - Serial Communication
# ============================================

import serial
import threading
import time
import config


class HardwareController:
    """
    Serial communication with Arduino
    
    Protocol:
    - Receive 'T' from Arduino: IR sensor triggered
    - Send 'K' to Arduino: Kick command for NG bottle
    - Send 'O' to Arduino: OK bottle (optional)
    """
    
    def __init__(self):
        self.port = config.ARDUINO_PORT
        self.baudrate = config.ARDUINO_BAUDRATE
        self.timeout = config.ARDUINO_TIMEOUT
        
        self.serial = None
        self.connected = False
        self.listening = False
        self.thread = None
        
        self.trigger_callback = None  # Callback when 'T' received
        
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
            
            self.connected = True
            print(f"[Hardware] Connected to Arduino on {self.port}")
            return True
            
        except serial.SerialException as e:
            print(f"[ERROR] Cannot connect to Arduino: {e}")
            print(f"[Hardware] Make sure Arduino is connected to {self.port}")
            self.connected = False
            return False
        except Exception as e:
            print(f"[ERROR] Hardware init failed: {e}")
            self.connected = False
            return False
    
    def start_listening(self, trigger_callback):
        """
        Start listening thread
        
        Args:
            trigger_callback: Function to call when 'T' received
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
                    data = self.serial.read(1).decode('utf-8')
                    
                    if config.VERBOSE_LOGGING:
                        print(f"[Hardware] Received: '{data}'")
                    
                    # IR Sensor triggered
                    if data == config.CMD_TRIGGER:
                        if self.trigger_callback:
                            self.trigger_callback()
                    
            except Exception as e:
                print(f"[ERROR] Serial read error: {e}")
                time.sleep(0.1)
    
    def send_kick(self):
        """Send kick command to Arduino"""
        return self._send_command(config.CMD_KICK)
    
    def send_ok(self):
        """Send OK command to Arduino (optional)"""
        return self._send_command(config.CMD_OK)
    
    def _send_command(self, cmd):
        """Send single character command"""
        if not self.connected:
            print("[ERROR] Cannot send command: Not connected")
            return False
        
        try:
            self.serial.write(cmd.encode('utf-8'))
            self.serial.flush()
            
            if config.VERBOSE_LOGGING:
                print(f"[Hardware] Sent: '{cmd}'")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Send command failed: {e}")
            return False
    
    def stop(self):
        """Stop listening thread"""
        self.listening = False
        
        if self.thread is not None:
            self.thread.join(timeout=2.0)
        
        if self.serial is not None and self.serial.is_open:
            self.serial.close()
        
        self.connected = False
        print("[Hardware] Stopped")
    
    def is_connected(self):
        """Check if connected"""
        return self.connected


class DummyHardwareController:
    """
    Dummy hardware for testing without Arduino
    """
    
    def __init__(self):
        self.connected = True
        self.listening = False
        self.trigger_callback = None
        print("[Hardware] Using DUMMY hardware")
    
    def start_listening(self, trigger_callback):
        self.trigger_callback = trigger_callback
        self.listening = True
        
        # Simulate triggers every 5 seconds
        def simulate():
            while self.listening:
                time.sleep(5)
                if self.trigger_callback:
                    print("[Hardware] DUMMY trigger!")
                    self.trigger_callback()
        
        threading.Thread(target=simulate, daemon=True).start()
        return True
    
    def send_kick(self):
        print("[Hardware] DUMMY kick sent")
        return True
    
    def send_ok(self):
        print("[Hardware] DUMMY ok sent")
        return True
    
    def stop(self):
        self.listening = False
        self.connected = False
    
    def is_connected(self):
        return True

