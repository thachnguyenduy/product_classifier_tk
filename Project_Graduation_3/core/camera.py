# ============================================
# CAMERA MODULE - Threaded Video Capture
# ============================================

import cv2
import threading
import time
import numpy as np
import config


class Camera:
    """
    Threaded camera capture for smooth video streaming
    """
    
    def __init__(self):
        self.camera_id = config.CAMERA_ID
        self.width = config.CAMERA_WIDTH
        self.height = config.CAMERA_HEIGHT
        
        self.cap = None
        self.frame = None
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        
        self._open_camera()
    
    def _open_camera(self):
        """Open and configure camera"""
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            
            if not self.cap.isOpened():
                print(f"[ERROR] Cannot open camera {self.camera_id}")
                return False
            
            # Configure
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
            
            # Manual exposure (reduce motion blur)
            if not config.CAMERA_AUTO_EXPOSURE:
                self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # Manual
                self.cap.set(cv2.CAP_PROP_EXPOSURE, config.CAMERA_EXPOSURE)
            
            print(f"[Camera] Opened successfully (ID: {self.camera_id}, {self.width}x{self.height})")
            return True
            
        except Exception as e:
            print(f"[ERROR] Camera init failed: {e}")
            return False
    
    def start(self):
        """Start capture thread"""
        if self.cap is None or not self.cap.isOpened():
            print("[ERROR] Camera not opened")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        print("[Camera] Capture thread started")
        return True
    
    def _capture_loop(self):
        """Continuous capture loop"""
        while self.running:
            ret, frame = self.cap.read()
            
            if ret:
                with self.lock:
                    self.frame = frame
            else:
                print("[WARNING] Failed to read frame")
                time.sleep(0.1)
    
    def get_frame(self):
        """Get latest frame (thread-safe)"""
        with self.lock:
            if self.frame is not None:
                return self.frame.copy()
            return None
    
    def stop(self):
        """Stop capture thread"""
        self.running = False
        if self.thread is not None:
            self.thread.join(timeout=2.0)
        
        if self.cap is not None:
            self.cap.release()
        
        print("[Camera] Stopped")
    
    def is_opened(self):
        """Check if camera is opened"""
        return self.cap is not None and self.cap.isOpened()


class DummyCamera:
    """
    Dummy camera for testing without hardware
    """
    
    def __init__(self):
        self.width = config.CAMERA_WIDTH
        self.height = config.CAMERA_HEIGHT
        self.running = False
        print("[Camera] Using DUMMY camera")
    
    def start(self):
        self.running = True
        return True
    
    def get_frame(self):
        """Generate dummy frame"""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Draw some fake content
        cv2.putText(frame, "DUMMY CAMERA", (200, 240), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        return frame
    
    def stop(self):
        self.running = False
    
    def is_opened(self):
        return True

