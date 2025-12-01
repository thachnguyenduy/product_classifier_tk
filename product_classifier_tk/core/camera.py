"""Threaded camera capture for Tkinter UI."""
from __future__ import annotations

import threading
import time
from typing import Optional, Tuple

import cv2


class CameraStreamer:
    """Continuously reads frames from an attached camera in a background thread."""

    def __init__(self, camera_index: int = 0) -> None:
        self.camera_index = camera_index
        self.capture: Optional[cv2.VideoCapture] = None
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

        self.capture = cv2.VideoCapture(self.camera_index)
        if not self.capture.isOpened():
            self.capture = None
            return False

        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        return True

    def _capture_loop(self) -> None:
        """Continuously read frames while running is True."""
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

