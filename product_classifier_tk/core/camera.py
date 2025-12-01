"""Threaded camera capture for Tkinter UI."""
from __future__ import annotations

import os
import platform
import subprocess
import threading
import time
from typing import Optional, Tuple

import cv2
import numpy as np


def is_raspberry_pi() -> bool:
    """Check if running on Raspberry Pi."""
    try:
        with open("/proc/device-tree/model", "r") as f:
            return "raspberry pi" in f.read().lower()
    except Exception:
        return False


# Try to import picamera2 (for Raspberry Pi Camera Module)
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False
    Picamera2 = None


class CameraStreamer:
    """Continuously reads frames from an attached camera in a background thread."""

    def __init__(self, camera_index: int = 0, use_picamera2: bool = True) -> None:
        self.camera_index = camera_index
        self.use_picamera2 = use_picamera2 and is_raspberry_pi() and PICAMERA2_AVAILABLE
        self.capture: Optional[cv2.VideoCapture] = None
        self.picam2: Optional[Picamera2] = None
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

        print(f"🎥 Opening camera (Raspberry Pi={is_raspberry_pi()}, picamera2={PICAMERA2_AVAILABLE})...")
        
        # Trên Raspberry Pi với picamera2
        if self.use_picamera2:
            print("  Using picamera2 for Pi Camera Module v2...")
            try:
                self.picam2 = Picamera2()
                
                # Configure camera
                config = self.picam2.create_preview_configuration(
                    main={"size": (1280, 720), "format": "RGB888"}
                )
                self.picam2.configure(config)
                
                # Start camera
                self.picam2.start()
                time.sleep(1)  # Warm up
                
                # Test capture
                frame = self.picam2.capture_array()
                if frame is not None:
                    print(f"  ✅ picamera2 success! Frame shape: {frame.shape}")
                    # Convert RGB to BGR for OpenCV compatibility
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    with self.frame_lock:
                        self.latest_frame = frame_bgr
                else:
                    print("  ❌ picamera2 cannot capture frame")
                    self.picam2.stop()
                    self.picam2 = None
                    return False
                
                self.running = True
                self.thread = threading.Thread(target=self._capture_loop_picamera2, daemon=True)
                self.thread.start()
                return True
                
            except Exception as e:
                print(f"  ❌ picamera2 failed: {e}")
                if self.picam2:
                    try:
                        self.picam2.stop()
                    except:
                        pass
                    self.picam2 = None
                return False
        
        # Fallback: OpenCV backends
        print("  Using OpenCV VideoCapture...")
        
        # Trên Raspberry Pi, thử V4L2
        if is_raspberry_pi():
            print("  Trying V4L2 backend...")
            self.capture = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
            
            if self.capture.isOpened():
                self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                self.capture.set(cv2.CAP_PROP_FPS, 30)
                
                ret, frame = self.capture.read()
                if ret and frame is not None:
                    print(f"  ✅ V4L2 success! Frame shape: {frame.shape}")
                else:
                    print("  ❌ V4L2 opened but cannot read")
                    self.capture.release()
                    self.capture = None
            else:
                print("  ❌ V4L2 failed")
                self.capture = None
        else:
            # Windows/Linux
            self.capture = cv2.VideoCapture(self.camera_index)
            if not self.capture.isOpened():
                print("  ❌ Cannot open camera")
                return False
            print("  ✅ Camera opened")

        if self.capture is None:
            print("  ❌ All methods failed")
            return False

        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        return True

    def _capture_loop_picamera2(self) -> None:
        """Capture loop for picamera2."""
        while self.running and self.picam2 is not None:
            try:
                frame = self.picam2.capture_array()
                if frame is not None:
                    # Convert RGB to BGR for OpenCV
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    
                    with self.frame_lock:
                        self.latest_frame = frame_bgr
                    
                    now = time.time()
                    dt = now - self._last_timestamp
                    if dt > 0:
                        self._fps = 1.0 / dt
                    self._last_timestamp = now
                else:
                    time.sleep(0.01)
            except Exception as e:
                print(f"Capture error: {e}")
                time.sleep(0.05)
        
        self._release_capture()

    def _capture_loop(self) -> None:
        """Continuously read frames while running is True (OpenCV)."""
        while self.running and self.capture is not None:
            ret, frame = self.capture.read()
            if not ret:
                time.sleep(0.05)
                continue

            with self.frame_lock:
                self.latest_frame = frame

            now = time.time()
            dt = now - self._last_timestamp
            if dt > 0:
                self._fps = 1.0 / dt
            self._last_timestamp = now

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

