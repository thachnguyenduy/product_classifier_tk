"""USB Camera streaming module."""
import cv2
import os
import threading
import time


class CameraStreamer:
    """USB Camera streamer with auto-reconnect."""
    
    def __init__(self, camera_index=0, width=640, height=480):
        self.camera_index = camera_index
        self.width = width
        self.height = height

        self.capture = None
        self.running = False
        self.thread = None

        self.frame_lock = threading.Lock()
        self.latest_frame = None

        self._last_time = time.time()
        self._fps = 0

    def _open_camera(self):
        """Open USB camera with platform-specific backend."""
        try:
            # Windows: DSHOW, Linux/Pi: V4L2
            if os.name == 'nt':
                backend = cv2.CAP_DSHOW
                print(f"[Camera] Using DSHOW backend (Windows)")
            else:
                backend = cv2.CAP_V4L2
                print(f"[Camera] Using V4L2 backend (Linux/Pi)")
            
            cap = cv2.VideoCapture(self.camera_index, backend)

            # Fallback to default if failed
            if not cap.isOpened():
                print(f"[Camera] Backend failed, trying default...")
                cap = cv2.VideoCapture(self.camera_index)

            if not cap.isOpened():
                print(f"[Camera] Failed to open camera {self.camera_index}")
                return None

            # Set resolution
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Verify with test read
            ret, frame = cap.read()
            if ret and frame is not None:
                actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                print(f"[Camera] ✅ Opened camera {self.camera_index} ({actual_w}x{actual_h})")
                return cap
            else:
                print(f"[Camera] Camera opened but cannot read frame")
                cap.release()
                return None

        except Exception as e:
            print(f"[Camera] Error: {e}")
            return None

    def start(self):
        """Start camera streaming."""
        if self.running:
            return True

        self.capture = self._open_camera()
        if self.capture is None:
            return False

        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print("[Camera] Streaming started.")
        return True

    def _loop(self):
        """Main capture loop with auto-reconnect."""
        reconnect_delay = 0.5
        
        while self.running:
            # Check if capture is valid
            if self.capture is None:
                print("[Camera] Reconnecting...")
                time.sleep(reconnect_delay)
                self.capture = self._open_camera()
                continue

            # Read frame
            ret, frame = self.capture.read()

            if not ret or frame is None:
                print("[Camera] Frame read failed, reconnecting...")
                try:
                    self.capture.release()
                except:
                    pass
                self.capture = None
                time.sleep(reconnect_delay)
                continue

            # Store frame
            with self.frame_lock:
                self.latest_frame = frame

            # Calculate FPS
            now = time.time()
            dt = now - self._last_time
            if dt > 0:
                self._fps = 1.0 / dt
            self._last_time = now

            # Small delay to reduce CPU usage
            time.sleep(0.001)

    def get_frame(self):
        """Get the latest frame and FPS."""
        with self.frame_lock:
            if self.latest_frame is None:
                return None, 0
            return self.latest_frame.copy(), self._fps

    def stop(self):
        """Stop camera streaming."""
        print("[Camera] Stopping...")
        self.running = False
        
        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)

        # Release camera
        if self.capture:
            try:
                self.capture.release()
            except:
                pass
            self.capture = None

        self.latest_frame = None
        print("[Camera] ✅ Stopped.")
