"""
Camera Handler for Coca-Cola Sorting System (CONTINUOUS MODE)
Threaded camera capture with manual exposure control to reduce motion blur
"""

import cv2
import numpy as np
import threading
import time
from datetime import datetime
import config


class Camera:
    """
    Threaded camera handler with manual exposure control
    Optimized for continuous conveyor (moving objects)
    """
    
    def __init__(self, camera_id=0, width=640, height=480, fps=30, 
                 exposure=-4, auto_exposure=False):
        """
        Initialize camera
        
        Args:
            camera_id: Camera device ID (0, 1, 2, ...)
            width: Frame width
            height: Frame height
            fps: Target FPS
            exposure: Manual exposure value (negative = shorter exposure)
            auto_exposure: Enable auto exposure
        """
        print(f"[Camera] Initializing camera {camera_id}...")
        
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.fps = fps
        self.exposure = exposure
        self.auto_exposure = auto_exposure
        
        self.cap = None
        self.frame = None
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0
    
    def start(self):
        """
        Start camera capture thread
        
        Returns:
            bool: True if started successfully
        """
        try:
            # Open camera
            self.cap = cv2.VideoCapture(self.camera_id)
            
            if not self.cap.isOpened():
                print(f"[ERROR] Failed to open camera {self.camera_id}")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Set exposure (CRITICAL for moving conveyor)
            if not self.auto_exposure:
                # Disable auto exposure
                self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Manual mode
                self.cap.set(cv2.CAP_PROP_EXPOSURE, self.exposure)
                print(f"[Camera] Manual exposure set to {self.exposure}")
            else:
                self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)  # Auto mode
                print("[Camera] Auto exposure enabled")
            
            # Verify settings
            actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            actual_exposure = self.cap.get(cv2.CAP_PROP_EXPOSURE)
            
            print(f"[Camera] Resolution: {int(actual_width)}x{int(actual_height)}")
            print(f"[Camera] FPS: {actual_fps}")
            print(f"[Camera] Exposure: {actual_exposure}")
            
            # Read first frame
            ret, frame = self.cap.read()
            if not ret:
                print("[ERROR] Failed to read first frame")
                return False
            
            self.frame = frame
            
            # Start capture thread
            self.running = True
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            
            print("[Camera] Camera started successfully")
            return True
            
        except Exception as e:
            print(f"[ERROR] Camera initialization failed: {e}")
            return False
    
    def stop(self):
        """Stop camera capture"""
        print("[Camera] Stopping camera...")
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=2.0)
        
        if self.cap:
            self.cap.release()
        
        print("[Camera] Camera stopped")
    
    def _capture_loop(self):
        """Main capture loop (runs in separate thread)"""
        print("[Camera] Capture thread started")
        
        while self.running:
            try:
                ret, frame = self.cap.read()
                
                if ret:
                    with self.lock:
                        self.frame = frame
                        self.frame_count += 1
                    
                    # Calculate FPS
                    current_time = time.time()
                    if current_time - self.last_fps_time >= 1.0:
                        self.current_fps = self.frame_count / (current_time - self.last_fps_time)
                        self.frame_count = 0
                        self.last_fps_time = current_time
                else:
                    print("[WARNING] Failed to read frame")
                    time.sleep(0.1)
                
            except Exception as e:
                print(f"[ERROR] Capture loop error: {e}")
                time.sleep(0.1)
        
        print("[Camera] Capture thread stopped")
    
    def read_frame(self):
        """
        Get latest frame (thread-safe)
        
        Returns:
            numpy.ndarray: BGR frame or None
        """
        with self.lock:
            if self.frame is None:
                return None
            frame = self.frame.copy()

        # Apply ROI crop (left/right/top/bottom) then resize back to original size.
        # This reduces visible area without changing output resolution.
        try:
            if getattr(config, "ENABLE_ROI_CROP", False):
                left = int(getattr(config, "ROI_CROP_LEFT_PX", 0) or 0)
                right = int(getattr(config, "ROI_CROP_RIGHT_PX", 0) or 0)
                top = int(getattr(config, "ROI_CROP_TOP_PX", 0) or 0)
                bottom = int(getattr(config, "ROI_CROP_BOTTOM_PX", 0) or 0)

                left = max(0, left)
                right = max(0, right)
                top = max(0, top)
                bottom = max(0, bottom)

                h, w = frame.shape[:2]
                # Ensure we keep at least 1x1 pixels
                if (left + right) < (w - 1) and (top + bottom) < (h - 1):
                    cropped = frame[top:h - bottom, left:w - right]
                    if cropped is not None and cropped.shape[0] > 0 and cropped.shape[1] > 0:
                        frame = cv2.resize(cropped, (self.width, self.height))
        except Exception:
            # Never let ROI/crop break the main loop
            pass

        return frame
    
    def capture_snapshot(self):
        """
        Capture a snapshot (same as read_frame for continuous mode)
        
        Returns:
            numpy.ndarray: BGR frame or None
        """
        return self.read_frame()
    
    def save_image(self, image, directory, prefix="capture"):
        """
        Save image to disk
        
        Args:
            image: BGR image
            directory: Save directory
            prefix: Filename prefix
            
        Returns:
            str: Saved file path
        """
        import os
        
        # Create directory if needed
        os.makedirs(directory, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"{prefix}_{timestamp}.jpg"
        filepath = os.path.join(directory, filename)
        
        # Save image
        cv2.imwrite(filepath, image)
        
        return filepath
    
    def get_fps(self):
        """Get current FPS"""
        return self.current_fps
    
    def is_running(self):
        """Check if camera is running"""
        return self.running


class DummyCamera:
    """
    Dummy camera for testing without hardware
    Generates test images with random patterns
    """
    
    def __init__(self, width=640, height=480):
        """Initialize dummy camera"""
        print("[Camera] Initializing DUMMY camera...")
        
        self.width = width
        self.height = height
        self.running = False
        self.frame_count = 0
    
    def start(self):
        """Start dummy camera"""
        self.running = True
        print("[Camera] DUMMY camera started")
        return True
    
    def stop(self):
        """Stop dummy camera"""
        self.running = False
        print("[Camera] DUMMY camera stopped")
    
    def read_frame(self):
        """Generate dummy frame"""
        if not self.running:
            return None
        
        # Create test pattern
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Add some patterns
        cv2.rectangle(frame, (50, 50), (200, 200), (0, 255, 0), 2)
        cv2.circle(frame, (400, 300), 50, (255, 0, 0), -1)
        
        # Add text
        text = f"DUMMY FRAME {self.frame_count}"
        cv2.putText(frame, text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        self.frame_count += 1
        
        return frame
    
    def capture_snapshot(self):
        """Capture dummy snapshot"""
        return self.read_frame()
    
    def save_image(self, image, directory, prefix="capture"):
        """Save dummy image"""
        import os
        os.makedirs(directory, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"{prefix}_{timestamp}.jpg"
        filepath = os.path.join(directory, filename)
        
        cv2.imwrite(filepath, image)
        return filepath
    
    def get_fps(self):
        """Get dummy FPS"""
        return 30.0
    
    def is_running(self):
        """Check if dummy camera is running"""
        return self.running
