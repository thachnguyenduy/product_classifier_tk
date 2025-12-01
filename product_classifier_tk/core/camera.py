"""Threaded camera capture for Tkinter UI."""
from __future__ import annotations

import threading
import time
from typing import Optional, Tuple

import cv2
import numpy as np

# Try to import picamera2 (for Raspberry Pi Camera Module)
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
    print("✅ picamera2 available")
except ImportError:
    PICAMERA2_AVAILABLE = False
    Picamera2 = None
    print("⚠️ picamera2 not available, using OpenCV")


class CameraStreamer:
    """Continuously reads frames from an attached camera in a background thread."""

    def __init__(self, camera_index: int = 0) -> None:
        self.camera_index = camera_index
        self.capture: Optional[cv2.VideoCapture] = None
        self.picam2: Optional[Picamera2] = None
        self.use_picamera2 = PICAMERA2_AVAILABLE
        self.running = False
        self.frame_lock = threading.Lock()
        self.latest_frame = None
        self.thread: Optional[threading.Thread] = None
        self._last_timestamp = time.time()
        self._fps = 0.0

    def start(self) -> bool:
        """Open the camera and begin background capture."""
        if self.running:
            return True

        print("🎥 Opening camera...")
        
        # Method 1: Try picamera2 first (for Raspberry Pi Camera Module)
        if self.use_picamera2:
            print("  Trying picamera2...")
            try:
                self.picam2 = Picamera2()
                
                # Simple configuration
                config = self.picam2.create_preview_configuration(
                    main={"size": (1280, 720), "format": "RGB888"}
                )
                self.picam2.configure(config)
                self.picam2.start()
                
                # Warm up
                time.sleep(2)
                
                # Test capture
                frame = self.picam2.capture_array()
                if frame is not None and frame.size > 0:
                    print(f"  ✅ picamera2 OK! Shape: {frame.shape}")
                    self.running = True
                    self.thread = threading.Thread(target=self._capture_loop_picamera2, daemon=True)
                    self.thread.start()
                    return True
                else:
                    print("  ❌ picamera2 no frame")
                    self.picam2.stop()
                    self.picam2 = None
                    
            except Exception as e:
                print(f"  ❌ picamera2 error: {e}")
                if self.picam2:
                    try:
                        self.picam2.stop()
                    except:
                        pass
                    self.picam2 = None
        
        # Method 2: Fallback to OpenCV
        print("  Trying OpenCV...")
        self.capture = cv2.VideoCapture(self.camera_index)
        
        if not self.capture.isOpened():
            print("  ❌ OpenCV failed")
            return False
        
        # Set resolution
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Test read
        ret, frame = self.capture.read()
        if not ret or frame is None:
            print("  ❌ OpenCV cannot read frame")
            self.capture.release()
            self.capture = None
            return False
        
        print(f"  ✅ OpenCV OK! Shape: {frame.shape}")
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        return True

    def _capture_loop_picamera2(self) -> None:
        """Capture loop for picamera2."""
        print("📹 picamera2 capture loop started")
        while self.running and self.picam2 is not None:
            try:
                # Capture frame (RGB format)
                frame = self.picam2.capture_array()
                
                if frame is not None and frame.size > 0:
                    # Convert RGB to BGR for OpenCV compatibility
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    
                    with self.frame_lock:
                        self.latest_frame = frame_bgr
                    
                    # Calculate FPS
                    now = time.time()
                    dt = now - self._last_timestamp
                    if dt > 0:
                        self._fps = 1.0 / dt
                    self._last_timestamp = now
                    
            except Exception as e:
                print(f"⚠️ Capture error: {e}")
                time.sleep(0.05)
        
        print("📹 picamera2 capture loop stopped")
        self._release_capture()

    def _capture_loop(self) -> None:
        """Continuously read frames while running is True (OpenCV)."""
        print("📹 OpenCV capture loop started")
        while self.running and self.capture is not None:
            ret, frame = self.capture.read()
            if not ret or frame is None:
                time.sleep(0.05)
                continue

            with self.frame_lock:
                self.latest_frame = frame

            # Calculate FPS
            now = time.time()
            dt = now - self._last_timestamp
            if dt > 0:
                self._fps = 1.0 / dt
            self._last_timestamp = now

        print("📹 OpenCV capture loop stopped")
        self._release_capture()

    def get_frame(self) -> Tuple[Optional[any], float]:
        """Return the latest frame and FPS estimate."""
        with self.frame_lock:
            frame = None if self.latest_frame is None else self.latest_frame.copy()
        return frame, self._fps

    def stop(self) -> None:
        """Stop streaming and free camera resources."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self._release_capture()

    def _release_capture(self) -> None:
        if self.capture is not None:
            self.capture.release()
            self.capture = None
        if self.picam2 is not None:
            try:
                self.picam2.stop()
            except:
                pass
            self.picam2 = None

