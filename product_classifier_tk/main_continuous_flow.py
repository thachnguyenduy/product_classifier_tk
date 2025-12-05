#!/usr/bin/env python3
"""
================================================================================
Coca-Cola Bottle Defect Detection System - Raspberry Pi 5 Controller
================================================================================

Hardware:
  - Raspberry Pi 5 (8GB RAM)
  - USB Webcam (horizontal view of conveyor belt)
  - Arduino Uno (via USB Serial)
  
Features:
  - Continuous flow detection (conveyor never stops for capture)
  - Burst capture: 5 frames when bottle detected
  - Voting mechanism: ≥3/5 frames with same defect → confirmed defect
  - Time-stamped ejection: calculated delay for precise rejection
  - Real-time OpenCV dashboard with live feed + statistics

Defect Classes:
  - no_cap: Missing bottle cap
  - low_level: Liquid level too low
  - no_label: Missing label
  - not_coke: Wrong product (not Coca-Cola)

================================================================================
"""

import cv2
import numpy as np
import serial
import threading
import time
import queue
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from ultralytics import YOLO


# ============================================================================
# ======================== CONFIGURATION SECTION =============================
# ============================================================================

class Config:
    """
    Centralized configuration for easy calibration.
    Adjust these values based on your physical setup.
    """
    
    # ==================== Serial Communication ====================
    SERIAL_PORT = "/dev/ttyACM0"  # Arduino USB port (Linux/Pi)
    # SERIAL_PORT = "COM3"  # Uncomment for Windows
    SERIAL_BAUD = 115200
    SERIAL_TIMEOUT = 1.0
    
    # ====================== Camera Settings =======================
    CAMERA_INDEX = 0  # USB camera index
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    CAMERA_FPS = 30
    
    # =================== AI Model Configuration ===================
    MODEL_PATH = "model/my_model.pt"  # YOLOv8 model path
    # MODEL_PATH = "model/best_ncnn_model"  # Uncomment for NCNN format
    CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence for detection
    
    # ==================== Defect Class Names ======================
    DEFECT_CLASSES = {
        "no_cap": "Thiếu nắp",
        "low_level": "Mức nước thấp",
        "no_label": "Thiếu nhãn",
        "not_coke": "Sai sản phẩm"
    }
    
    # ================= Burst Capture Configuration ================
    BURST_COUNT = 5  # Number of frames to capture per bottle
    BURST_INTERVAL = 0.05  # Seconds between burst captures (50ms)
    DELAY_SENSOR_TO_CAPTURE = 0.2  # Delay from sensor detect to first capture (200ms)
    
    # =================== Voting Mechanism =========================
    VOTING_THRESHOLD = 3  # Minimum votes (out of 5) to confirm defect
    
    # =============== Physical Timing (CALIBRATE!) =================
    # Time from capture moment to rejection point (seconds)
    # This depends on:
    #   - Conveyor belt speed
    #   - Distance from camera to ejector
    # IMPORTANT: Measure and calibrate this value!
    PHYSICAL_DELAY = 2.0  # Example: 2 seconds travel time
    
    # =================== Dashboard Settings =======================
    DASHBOARD_WIDTH = 1280
    DASHBOARD_HEIGHT = 720
    
    # Layout dimensions
    LIVE_FEED_X = 0
    LIVE_FEED_Y = 0
    LIVE_FEED_W = 640
    LIVE_FEED_H = 480
    
    DEFECT_IMAGE_X = 640
    DEFECT_IMAGE_Y = 0
    DEFECT_IMAGE_W = 640
    DEFECT_IMAGE_H = 480
    
    STATS_Y = 480
    STATS_H = 240
    
    # Colors (BGR)
    COLOR_BACKGROUND = (40, 40, 40)
    COLOR_TEXT = (255, 255, 255)
    COLOR_GOOD = (0, 255, 0)
    COLOR_DEFECT = (0, 0, 255)
    COLOR_WARNING = (0, 165, 255)
    
    # =================== Debug/Logging ============================
    SAVE_DEFECT_IMAGES = True  # Save defect images to disk
    DEFECT_SAVE_PATH = "captures/defects"
    DEBUG_MODE = True  # Print verbose logs


# ============================================================================
# ========================== UTILITY FUNCTIONS ===============================
# ============================================================================

def ensure_directory(path):
    """Ensure directory exists."""
    Path(path).mkdir(parents=True, exist_ok=True)


def get_timestamp():
    """Get current timestamp string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_timestamp_filename():
    """Get timestamp suitable for filename."""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


# ============================================================================
# ========================= SERIAL COMMUNICATION =============================
# ============================================================================

class ArduinoController:
    """
    Handles serial communication with Arduino.
    Listens for DETECTED signals and sends commands.
    """
    
    def __init__(self, port=Config.SERIAL_PORT, baud=Config.SERIAL_BAUD):
        self.port = port
        self.baud = baud
        self.serial_conn = None
        self.running = False
        self.read_thread = None
        self.detection_callback = None
        
        # Connect to Arduino
        self._connect()
    
    def _connect(self):
        """Establish serial connection with Arduino."""
        try:
            self.serial_conn = serial.Serial(
                self.port,
                self.baud,
                timeout=Config.SERIAL_TIMEOUT
            )
            time.sleep(2.5)  # Wait for Arduino reset after serial open
            
            # Read startup message
            while self.serial_conn.in_waiting > 0:
                line = self.serial_conn.readline().decode().strip()
                print(f"[Arduino] {line}")
            
            print(f"✅ Connected to Arduino at {self.port}")
            
        except Exception as e:
            print(f"❌ Failed to connect to Arduino: {e}")
            self.serial_conn = None
    
    def start_listening(self, detection_callback):
        """
        Start listening for Arduino messages in background thread.
        
        Args:
            detection_callback: Function to call when DETECTED signal received
        """
        self.detection_callback = detection_callback
        self.running = True
        self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.read_thread.start()
        print("🎧 Listening for Arduino signals...")
    
    def _read_loop(self):
        """Background thread to read Arduino messages."""
        while self.running and self.serial_conn:
            try:
                if self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode().strip()
                    
                    if line:
                        if Config.DEBUG_MODE:
                            print(f"[Arduino] {line}")
                        
                        # Check for bottle detection signal
                        if line == "DETECTED":
                            if self.detection_callback:
                                # Call detection callback in new thread to avoid blocking
                                threading.Thread(
                                    target=self.detection_callback,
                                    daemon=True
                                ).start()
                
                time.sleep(0.01)  # Small delay to reduce CPU usage
                
            except Exception as e:
                print(f"[Arduino Read Error] {e}")
                time.sleep(0.1)
    
    def send_command(self, command):
        """Send command to Arduino."""
        if not self.serial_conn:
            print(f"[SIMULATED] Arduino command: {command}")
            return False
        
        try:
            self.serial_conn.write(f"{command}\n".encode())
            if Config.DEBUG_MODE:
                print(f"→ Sent to Arduino: {command}")
            return True
        except Exception as e:
            print(f"❌ Failed to send command '{command}': {e}")
            return False
    
    def start_conveyor(self):
        """Start conveyor belt."""
        self.send_command("START_CONVEYOR")
    
    def stop_conveyor(self):
        """Stop conveyor belt."""
        self.send_command("STOP_CONVEYOR")
    
    def reject_bottle(self):
        """Trigger bottle rejection."""
        self.send_command("REJECT")
    
    def ping(self):
        """Test Arduino connection."""
        self.send_command("PING")
    
    def get_status(self):
        """Request Arduino status."""
        self.send_command("STATUS")
    
    def stop(self):
        """Stop listening and close connection."""
        self.running = False
        if self.read_thread:
            self.read_thread.join(timeout=1.0)
        
        if self.serial_conn:
            self.stop_conveyor()
            time.sleep(0.5)
            self.serial_conn.close()
            print("🔌 Arduino connection closed")


# ============================================================================
# ========================== CAMERA CAPTURE ==================================
# ============================================================================

class CameraCapture:
    """
    USB camera capture with thread-safe frame access.
    """
    
    def __init__(self, index=Config.CAMERA_INDEX):
        self.index = index
        self.cap = None
        self.running = False
        self.thread = None
        self.frame_lock = threading.Lock()
        self.latest_frame = None
        self.fps = 0
        self.last_time = time.time()
    
    def start(self):
        """Open camera and start capture thread."""
        self.cap = cv2.VideoCapture(self.index)
        
        if not self.cap.isOpened():
            print(f"❌ Failed to open camera {self.index}")
            return False
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, Config.CAMERA_FPS)
        
        # Verify
        actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"📹 Camera opened: {actual_w}x{actual_h}")
        
        # Start capture thread
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        
        return True
    
    def _capture_loop(self):
        """Background thread for continuous frame capture."""
        while self.running:
            ret, frame = self.cap.read()
            
            if ret and frame is not None:
                with self.frame_lock:
                    self.latest_frame = frame.copy()
                
                # Calculate FPS
                now = time.time()
                dt = now - self.last_time
                if dt > 0:
                    self.fps = 1.0 / dt
                self.last_time = now
            
            time.sleep(0.001)
    
    def get_frame(self):
        """Get latest frame (thread-safe)."""
        with self.frame_lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy(), self.fps
        return None, 0
    
    def stop(self):
        """Stop capture and release camera."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        if self.cap:
            self.cap.release()
        print("📹 Camera released")


# ============================================================================
# ============================ AI INFERENCE ==================================
# ============================================================================

class DefectDetector:
    """
    YOLOv8-based defect detection with voting mechanism.
    """
    
    def __init__(self, model_path=Config.MODEL_PATH):
        self.model_path = Path(model_path)
        
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        print(f"🧠 Loading YOLO model from {model_path}...")
        self.model = YOLO(str(self.model_path))
        print("✅ Model loaded successfully")
    
    def detect_single_frame(self, frame):
        """
        Run inference on a single frame.
        
        Returns:
            dict: {
                'has_defect': bool,
                'defect_type': str or None,
                'confidence': float,
                'detections': list of detection dicts
            }
        """
        results = self.model(frame, conf=Config.CONFIDENCE_THRESHOLD, verbose=False)
        
        if not results or len(results) == 0:
            return {
                'has_defect': False,
                'defect_type': None,
                'confidence': 0.0,
                'detections': []
            }
        
        result = results[0]
        detections = []
        defect_found = None
        max_confidence = 0.0
        
        if result.boxes is not None and len(result.boxes) > 0:
            boxes = result.boxes
            
            for idx in range(len(boxes)):
                bbox = boxes.xyxy[idx].cpu().numpy().astype(int).tolist()
                cls_id = int(boxes.cls[idx].item())
                conf = float(boxes.conf[idx].item())
                label = self.model.names.get(cls_id, f"class_{cls_id}")
                
                detection = {
                    'bbox': bbox,
                    'class_id': cls_id,
                    'confidence': conf,
                    'label': label
                }
                detections.append(detection)
                
                # Check if it's a defect class
                if label in Config.DEFECT_CLASSES:
                    defect_found = label
                    max_confidence = max(max_confidence, conf)
        
        return {
            'has_defect': defect_found is not None,
            'defect_type': defect_found,
            'confidence': max_confidence,
            'detections': detections
        }
    
    def detect_with_voting(self, frames):
        """
        Run detection on multiple frames and use voting mechanism.
        
        Args:
            frames: List of frames (numpy arrays)
        
        Returns:
            dict: {
                'is_defect': bool,
                'defect_type': str or None,
                'confidence': float,
                'vote_count': int,
                'frame_results': list of individual results,
                'best_frame_idx': int (frame with highest confidence)
            }
        """
        if not frames:
            return {
                'is_defect': False,
                'defect_type': None,
                'confidence': 0.0,
                'vote_count': 0,
                'frame_results': [],
                'best_frame_idx': -1
            }
        
        frame_results = []
        defect_votes = []
        
        # Process each frame
        for frame in frames:
            result = self.detect_single_frame(frame)
            frame_results.append(result)
            
            if result['has_defect']:
                defect_votes.append(result['defect_type'])
        
        # Voting logic
        if len(defect_votes) >= Config.VOTING_THRESHOLD:
            # Count votes for each defect type
            vote_counter = Counter(defect_votes)
            most_common_defect, vote_count = vote_counter.most_common(1)[0]
            
            # Find frame with highest confidence for this defect
            best_idx = -1
            best_conf = 0.0
            for idx, result in enumerate(frame_results):
                if result['defect_type'] == most_common_defect:
                    if result['confidence'] > best_conf:
                        best_conf = result['confidence']
                        best_idx = idx
            
            return {
                'is_defect': True,
                'defect_type': most_common_defect,
                'confidence': best_conf,
                'vote_count': vote_count,
                'frame_results': frame_results,
                'best_frame_idx': best_idx
            }
        
        # Not enough votes for defect → Good bottle
        return {
            'is_defect': False,
            'defect_type': None,
            'confidence': 0.0,
            'vote_count': len(defect_votes),
            'frame_results': frame_results,
            'best_frame_idx': -1
        }


# ============================================================================
# ====================== TIMED EJECTION CONTROLLER ===========================
# ============================================================================

class EjectionScheduler:
    """
    Schedules bottle ejection at precise time based on capture timestamp.
    Uses threading for non-blocking operation.
    """
    
    def __init__(self, arduino_controller):
        self.arduino = arduino_controller
        self.pending_ejections = queue.PriorityQueue()
        self.running = False
        self.thread = None
    
    def start(self):
        """Start ejection scheduler thread."""
        self.running = True
        self.thread = threading.Thread(target=self._ejection_loop, daemon=True)
        self.thread.start()
        print("⏰ Ejection scheduler started")
    
    def _ejection_loop(self):
        """Background thread that executes timed ejections."""
        while self.running:
            try:
                # Check if there's a pending ejection (with timeout to allow checking running flag)
                try:
                    eject_time, bottle_id = self.pending_ejections.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # Calculate wait time
                current_time = time.time()
                wait_time = eject_time - current_time
                
                if wait_time > 0:
                    time.sleep(wait_time)
                
                # Execute ejection
                print(f"⚡ EJECTING bottle #{bottle_id} at {get_timestamp()}")
                self.arduino.reject_bottle()
                
            except Exception as e:
                print(f"[Ejection Error] {e}")
    
    def schedule_ejection(self, capture_timestamp, bottle_id):
        """
        Schedule bottle ejection based on capture timestamp.
        
        Args:
            capture_timestamp: Time when bottle was captured (time.time())
            bottle_id: Unique identifier for this bottle
        """
        eject_time = capture_timestamp + Config.PHYSICAL_DELAY
        self.pending_ejections.put((eject_time, bottle_id))
        
        delay = eject_time - time.time()
        print(f"📅 Scheduled ejection for bottle #{bottle_id} in {delay:.2f}s")
    
    def stop(self):
        """Stop scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        print("⏰ Ejection scheduler stopped")


# ============================================================================
# =========================== STATISTICS TRACKER =============================
# ============================================================================

class Statistics:
    """
    Track system statistics (bottles processed, defects found, etc.)
    """
    
    def __init__(self):
        self.lock = threading.Lock()
        self.total_bottles = 0
        self.total_defects = 0
        self.defect_counts = defaultdict(int)
        self.start_time = time.time()
    
    def record_bottle(self, is_defect, defect_type=None):
        """Record a processed bottle."""
        with self.lock:
            self.total_bottles += 1
            
            if is_defect and defect_type:
                self.total_defects += 1
                self.defect_counts[defect_type] += 1
    
    def get_stats(self):
        """Get current statistics."""
        with self.lock:
            uptime = time.time() - self.start_time
            return {
                'total_bottles': self.total_bottles,
                'total_defects': self.total_defects,
                'total_good': self.total_bottles - self.total_defects,
                'defect_counts': dict(self.defect_counts),
                'uptime_seconds': uptime
            }
    
    def reset(self):
        """Reset statistics."""
        with self.lock:
            self.total_bottles = 0
            self.total_defects = 0
            self.defect_counts.clear()
            self.start_time = time.time()


# ============================================================================
# ============================ DASHBOARD UI ==================================
# ============================================================================

class Dashboard:
    """
    OpenCV-based dashboard for visualization.
    Layout: 1280x720
      - Top-Left: Live camera feed
      - Top-Right: Latest defect image
      - Bottom: Statistics
    """
    
    def __init__(self):
        self.canvas = np.zeros(
            (Config.DASHBOARD_HEIGHT, Config.DASHBOARD_WIDTH, 3),
            dtype=np.uint8
        )
        self.canvas[:] = Config.COLOR_BACKGROUND
        
        self.latest_defect_frame = None
        self.lock = threading.Lock()
    
    def update_live_feed(self, frame):
        """Update live camera feed."""
        # Resize to fit live feed area
        resized = cv2.resize(
            frame,
            (Config.LIVE_FEED_W, Config.LIVE_FEED_H)
        )
        
        with self.lock:
            self.canvas[
                Config.LIVE_FEED_Y:Config.LIVE_FEED_Y + Config.LIVE_FEED_H,
                Config.LIVE_FEED_X:Config.LIVE_FEED_X + Config.LIVE_FEED_W
            ] = resized
    
    def update_defect_image(self, frame, detections, defect_type):
        """Update defect image with bounding boxes."""
        annotated = frame.copy()
        
        # Draw bounding boxes
        for det in detections:
            bbox = det['bbox']
            label = det['label']
            conf = det['confidence']
            
            # Color: Red for defects
            color = Config.COLOR_DEFECT
            
            x1, y1, x2, y2 = bbox
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # Label
            text = f"{label} {conf:.2f}"
            cv2.putText(
                annotated, text, (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
            )
        
        # Add defect type label at top
        cv2.putText(
            annotated,
            f"DEFECT: {Config.DEFECT_CLASSES.get(defect_type, defect_type)}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, Config.COLOR_DEFECT, 2
        )
        
        # Resize and place in dashboard
        resized = cv2.resize(
            annotated,
            (Config.DEFECT_IMAGE_W, Config.DEFECT_IMAGE_H)
        )
        
        with self.lock:
            self.canvas[
                Config.DEFECT_IMAGE_Y:Config.DEFECT_IMAGE_Y + Config.DEFECT_IMAGE_H,
                Config.DEFECT_IMAGE_X:Config.DEFECT_IMAGE_X + Config.DEFECT_IMAGE_W
            ] = resized
            
            self.latest_defect_frame = annotated
    
    def update_statistics(self, stats):
        """Update statistics panel at bottom."""
        with self.lock:
            # Clear stats area
            self.canvas[
                Config.STATS_Y:Config.STATS_Y + Config.STATS_H,
                :
            ] = Config.COLOR_BACKGROUND
            
            # Draw statistics
            y_offset = Config.STATS_Y + 40
            line_height = 40
            
            # Total bottles
            text = f"Total Bottles: {stats['total_bottles']}"
            cv2.putText(
                self.canvas, text, (50, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, Config.COLOR_TEXT, 2
            )
            y_offset += line_height
            
            # Good bottles
            text = f"Good: {stats['total_good']}"
            cv2.putText(
                self.canvas, text, (50, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, Config.COLOR_GOOD, 2
            )
            
            # Defect bottles
            text = f"Defects: {stats['total_defects']}"
            cv2.putText(
                self.canvas, text, (400, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, Config.COLOR_DEFECT, 2
            )
            y_offset += line_height
            
            # Individual defect counts
            x_offset = 50
            for defect_type, vietnamese_name in Config.DEFECT_CLASSES.items():
                count = stats['defect_counts'].get(defect_type, 0)
                text = f"{vietnamese_name}: {count}"
                cv2.putText(
                    self.canvas, text, (x_offset, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, Config.COLOR_WARNING, 2
                )
                x_offset += 250
            
            # Uptime
            uptime_minutes = int(stats['uptime_seconds'] / 60)
            uptime_seconds = int(stats['uptime_seconds'] % 60)
            text = f"Uptime: {uptime_minutes}m {uptime_seconds}s"
            cv2.putText(
                self.canvas, text, (50, Config.STATS_Y + Config.STATS_H - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, Config.COLOR_TEXT, 1
            )
    
    def get_canvas(self):
        """Get current dashboard canvas."""
        with self.lock:
            return self.canvas.copy()
    
    def get_latest_defect_frame(self):
        """Get latest defect frame (for saving)."""
        with self.lock:
            if self.latest_defect_frame is not None:
                return self.latest_defect_frame.copy()
        return None


# ============================================================================
# ============================ MAIN SYSTEM ===================================
# ============================================================================

class BottleInspectionSystem:
    """
    Main system coordinator.
    """
    
    def __init__(self):
        print("="*80)
        print("🍾 Coca-Cola Bottle Defect Detection System")
        print("="*80)
        
        # Initialize components
        print("\n📦 Initializing components...")
        self.camera = CameraCapture()
        self.arduino = ArduinoController()
        self.detector = DefectDetector()
        self.ejection_scheduler = EjectionScheduler(self.arduino)
        self.statistics = Statistics()
        self.dashboard = Dashboard()
        
        # State
        self.running = False
        self.bottle_counter = 0
        
        # Ensure save directory exists
        if Config.SAVE_DEFECT_IMAGES:
            ensure_directory(Config.DEFECT_SAVE_PATH)
        
        print("✅ All components initialized\n")
    
    def on_bottle_detected(self):
        """
        Callback when Arduino detects a bottle.
        This is where the burst capture and processing happens.
        """
        self.bottle_counter += 1
        bottle_id = self.bottle_counter
        
        print(f"\n{'='*80}")
        print(f"🍾 BOTTLE #{bottle_id} DETECTED at {get_timestamp()}")
        print(f"{'='*80}")
        
        # Wait for bottle to reach optimal capture position
        time.sleep(Config.DELAY_SENSOR_TO_CAPTURE)
        
        # Record capture start timestamp (for ejection timing)
        capture_timestamp = time.time()
        
        # Burst capture: 5 frames
        print(f"📸 Burst capturing {Config.BURST_COUNT} frames...")
        frames = []
        for i in range(Config.BURST_COUNT):
            frame, _ = self.camera.get_frame()
            if frame is not None:
                frames.append(frame)
                print(f"   Frame {i+1}/{Config.BURST_COUNT} captured")
            
            if i < Config.BURST_COUNT - 1:
                time.sleep(Config.BURST_INTERVAL)
        
        if not frames:
            print("❌ No frames captured!")
            return
        
        # AI Processing with voting
        print(f"🧠 Running AI detection with voting mechanism...")
        detection_result = self.detector.detect_with_voting(frames)
        
        is_defect = detection_result['is_defect']
        defect_type = detection_result['defect_type']
        confidence = detection_result['confidence']
        vote_count = detection_result['vote_count']
        
        if is_defect:
            print(f"❌ DEFECT DETECTED: {defect_type}")
            print(f"   Votes: {vote_count}/{Config.BURST_COUNT}")
            print(f"   Confidence: {confidence:.2%}")
            
            # Schedule ejection
            self.ejection_scheduler.schedule_ejection(capture_timestamp, bottle_id)
            
            # Update dashboard with defect image
            best_idx = detection_result['best_frame_idx']
            if best_idx >= 0:
                best_frame = frames[best_idx]
                best_detections = detection_result['frame_results'][best_idx]['detections']
                self.dashboard.update_defect_image(best_frame, best_detections, defect_type)
                
                # Save defect image
                if Config.SAVE_DEFECT_IMAGES:
                    filename = f"defect_{bottle_id}_{defect_type}_{get_timestamp_filename()}.jpg"
                    save_path = Path(Config.DEFECT_SAVE_PATH) / filename
                    cv2.imwrite(str(save_path), best_frame)
                    print(f"💾 Defect image saved: {save_path}")
        else:
            print(f"✅ GOOD BOTTLE")
            print(f"   Defect votes: {vote_count}/{Config.BURST_COUNT} (below threshold)")
        
        # Update statistics
        self.statistics.record_bottle(is_defect, defect_type)
        
        print(f"{'='*80}\n")
    
    def run(self):
        """Main system loop."""
        print("\n🚀 Starting system...\n")
        
        # Start camera
        if not self.camera.start():
            print("❌ Failed to start camera. Exiting.")
            return
        
        # Start ejection scheduler
        self.ejection_scheduler.start()
        
        # Start Arduino listener
        self.arduino.start_listening(self.on_bottle_detected)
        
        # Start conveyor belt
        print("▶️  Starting conveyor belt...")
        self.arduino.start_conveyor()
        time.sleep(1.0)
        
        self.running = True
        print("\n✅ System running! Press 'q' to quit, 'r' to reset stats.\n")
        
        # Main display loop
        try:
            while self.running:
                # Get latest frame from camera
                frame, fps = self.camera.get_frame()
                
                if frame is not None:
                    # Update live feed on dashboard
                    self.dashboard.update_live_feed(frame)
                
                # Update statistics
                stats = self.statistics.get_stats()
                self.dashboard.update_statistics(stats)
                
                # Get dashboard canvas and display
                canvas = self.dashboard.get_canvas()
                
                # Add FPS counter
                fps_text = f"FPS: {fps:.1f}"
                cv2.putText(
                    canvas, fps_text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, Config.COLOR_GOOD, 2
                )
                
                cv2.imshow("Bottle Defect Detection System", canvas)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\n⏹️  Quit requested...")
                    break
                elif key == ord('r'):
                    print("\n🔄 Resetting statistics...")
                    self.statistics.reset()
        
        except KeyboardInterrupt:
            print("\n⏹️  Interrupted by user...")
        
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown of all components."""
        print("\n🛑 Shutting down system...")
        
        self.running = False
        
        # Stop conveyor
        self.arduino.stop_conveyor()
        time.sleep(0.5)
        
        # Stop components
        self.ejection_scheduler.stop()
        self.camera.stop()
        self.arduino.stop()
        
        # Close windows
        cv2.destroyAllWindows()
        
        # Print final statistics
        stats = self.statistics.get_stats()
        print("\n" + "="*80)
        print("📊 FINAL STATISTICS")
        print("="*80)
        print(f"Total Bottles Inspected: {stats['total_bottles']}")
        print(f"Good Bottles: {stats['total_good']}")
        print(f"Defective Bottles: {stats['total_defects']}")
        if stats['total_bottles'] > 0:
            defect_rate = (stats['total_defects'] / stats['total_bottles']) * 100
            print(f"Defect Rate: {defect_rate:.2f}%")
        print("\nDefect Breakdown:")
        for defect_type, vietnamese_name in Config.DEFECT_CLASSES.items():
            count = stats['defect_counts'].get(defect_type, 0)
            print(f"  - {vietnamese_name}: {count}")
        print("="*80)
        
        print("\n✅ System shutdown complete. Goodbye!\n")


# ============================================================================
# ================================= MAIN =====================================
# ============================================================================

def main():
    """Entry point."""
    try:
        system = BottleInspectionSystem()
        system.run()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

