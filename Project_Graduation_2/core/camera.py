"""
Camera Handler for Coca-Cola Sorting System
Provides threaded video capture for real-time processing
"""

import cv2
import threading
import time
from datetime import datetime
import os


class Camera:
    """
    Threaded camera handler for continuous video capture
    Supports both USB cameras and Pi Camera
    """
    
    def __init__(self, camera_id=0, width=640, height=480):
        """
        Initialize camera
        
        Args:
            camera_id: Camera device ID (0 for default, or video path)
            width: Frame width
            height: Frame height
        """
        self.camera_id = camera_id
        self.width = width
        self.height = height
        
        self.cap = None
        self.frame = None
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        
        self.fps = 0
        self.frame_count = 0
        self.last_fps_time = time.time()
        
        print(f"[Camera] Initializing camera {camera_id}...")
    
    def start(self):
        """Start camera capture in separate thread"""
        if self.running:
            print("[Camera] Already running")
            return False
        
        # Open camera
        self.cap = cv2.VideoCapture(self.camera_id)
        
        if not self.cap.isOpened():
            print(f"[ERROR] Failed to open camera {self.camera_id}")
            return False
        
        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        # Set FPS (if supported)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Read first frame
        ret, self.frame = self.cap.read()
        if not ret or self.frame is None:
            print("[ERROR] Failed to read first frame")
            self.cap.release()
            return False
        
        # Start capture thread
        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()
        
        print(f"[Camera] Started successfully - Resolution: {self.width}x{self.height}")
        return True
    
    def _update(self):
        """Internal method to continuously read frames"""
        while self.running:
            ret, frame = self.cap.read()
            
            if ret and frame is not None:
                with self.lock:
                    self.frame = frame.copy()
                
                # Update FPS
                self.frame_count += 1
                current_time = time.time()
                elapsed = current_time - self.last_fps_time
                
                if elapsed >= 1.0:
                    self.fps = self.frame_count / elapsed
                    self.frame_count = 0
                    self.last_fps_time = current_time
            else:
                # Failed to read frame
                print("[WARNING] Failed to read frame from camera")
                time.sleep(0.1)
    
    def read(self):
        """
        Get current frame
        
        Returns:
            numpy.ndarray: Current frame (BGR format), or None if not available
        """
        with self.lock:
            if self.frame is not None:
                return self.frame.copy()
            return None
    
    def get_fps(self):
        """Get current FPS"""
        return self.fps
    
    def is_opened(self):
        """Check if camera is opened and running"""
        return self.running and self.cap is not None and self.cap.isOpened()
    
    def stop(self):
        """Stop camera capture"""
        if not self.running:
            return
        
        print("[Camera] Stopping...")
        self.running = False
        
        # Wait for thread to finish
        if self.thread is not None:
            self.thread.join(timeout=2.0)
        
        # Release camera
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        
        print("[Camera] Stopped")
    
    def capture_snapshot(self):
        """
        Capture a single snapshot for AI processing
        
        Returns:
            numpy.ndarray: Current frame
        """
        return self.read()
    
    def save_image(self, frame, save_dir, prefix="image"):
        """
        Save frame to disk
        
        Args:
            frame: Image to save
            save_dir: Directory to save to
            prefix: Filename prefix
        
        Returns:
            str: Path to saved image, or None if failed
        """
        try:
            # Create directory if needed
            os.makedirs(save_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{prefix}_{timestamp}.jpg"
            filepath = os.path.join(save_dir, filename)
            
            # Save image
            success = cv2.imwrite(filepath, frame)
            
            if success:
                print(f"[Camera] Image saved: {filepath}")
                return filepath
            else:
                print(f"[ERROR] Failed to save image: {filepath}")
                return None
                
        except Exception as e:
            print(f"[ERROR] Save image error: {e}")
            return None
    
    def __del__(self):
        """Cleanup on deletion"""
        self.stop()


class DummyCamera(Camera):
    """
    Dummy camera for testing without physical camera
    Generates synthetic frames with text
    """
    
    def __init__(self, width=640, height=480):
        super().__init__(camera_id=-1, width=width, height=height)
        self.use_dummy = True
        print("[Camera] Using DUMMY camera for testing")
    
    def start(self):
        """Start dummy camera"""
        if self.running:
            return False
        
        # Create initial dummy frame
        self.frame = self._generate_dummy_frame()
        
        # Start update thread
        self.running = True
        self.thread = threading.Thread(target=self._update_dummy, daemon=True)
        self.thread.start()
        
        print("[Camera] Dummy camera started")
        return True
    
    def _update_dummy(self):
        """Update dummy frames"""
        while self.running:
            with self.lock:
                self.frame = self._generate_dummy_frame()
            
            # Update FPS counter
            self.frame_count += 1
            current_time = time.time()
            elapsed = current_time - self.last_fps_time
            
            if elapsed >= 1.0:
                self.fps = self.frame_count / elapsed
                self.frame_count = 0
                self.last_fps_time = current_time
            
            time.sleep(1/30)  # Simulate 30 FPS
    
    def _generate_dummy_frame(self):
        """Generate a dummy frame with text"""
        import numpy as np
        
        # Create blank frame
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:] = (50, 50, 50)  # Dark gray
        
        # Add text
        text_lines = [
            "DUMMY CAMERA MODE",
            "For Testing Only",
            f"Time: {datetime.now().strftime('%H:%M:%S')}",
            f"FPS: {self.fps:.1f}"
        ]
        
        y_offset = 150
        for line in text_lines:
            cv2.putText(frame, line, (50, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            y_offset += 60
        
        # Add bottle outline
        cv2.rectangle(frame, (250, 200), (390, 420), (0, 255, 0), 2)
        cv2.putText(frame, "Bottle", (270, 440),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return frame
    
    def stop(self):
        """Stop dummy camera"""
        if not self.running:
            return
        
        self.running = False
        if self.thread is not None:
            self.thread.join(timeout=1.0)
        
        print("[Camera] Dummy camera stopped")

