#!/usr/bin/env python3
"""
================================================================================
Coca-Cola Bottle Defect Detection System - Raspberry Pi 5 Controller
Tkinter GUI Version
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
  - Tkinter GUI with live feed + statistics

================================================================================
"""

import cv2
import numpy as np
import serial
import threading
import time
import queue
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from ultralytics import YOLO


# ============================================================================
# ======================== CONFIGURATION SECTION =============================
# ============================================================================

class Config:
    """Centralized configuration for easy calibration."""
    
    # ==================== Serial Communication ====================
    SERIAL_PORT = "/dev/ttyACM0"  # Arduino USB port (Linux/Pi)
    # SERIAL_PORT = "COM3"  # Uncomment for Windows
    SERIAL_BAUD = 115200
    SERIAL_TIMEOUT = 1.0
    
    # ====================== Camera Settings =======================
    CAMERA_INDEX = 0
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    CAMERA_FPS = 30
    
    # =================== AI Model Configuration ===================
    MODEL_PATH = "model/best_ncnn_model"
    CONFIDENCE_THRESHOLD = 0.5
    
    # ==================== Defect Class Names ======================
    DEFECT_CLASSES = {
        "no_cap": "Thiếu nắp",
        "low_level": "Mức nước thấp",
        "no_label": "Thiếu nhãn",
        "not_coke": "Sai sản phẩm"
    }
    
    # ================= Burst Capture Configuration ================
    BURST_COUNT = 5
    BURST_INTERVAL = 0.05  # 50ms
    DELAY_SENSOR_TO_CAPTURE = 0.2  # 200ms
    
    # =================== Voting Mechanism =========================
    VOTING_THRESHOLD = 3
    
    # =============== Physical Timing (CALIBRATE!) =================
    PHYSICAL_DELAY = 2.0  # seconds
    
    # =================== Save Settings ============================
    SAVE_DEFECT_IMAGES = True
    DEFECT_SAVE_PATH = "captures/defects"
    DEBUG_MODE = True


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
    """Handles serial communication with Arduino."""
    
    def __init__(self, port=Config.SERIAL_PORT, baud=Config.SERIAL_BAUD):
        self.port = port
        self.baud = baud
        self.serial_conn = None
        self.running = False
        self.read_thread = None
        self.detection_callback = None
        self._connect()
    
    def _connect(self):
        """Establish serial connection with Arduino."""
        try:
            self.serial_conn = serial.Serial(self.port, self.baud, timeout=Config.SERIAL_TIMEOUT)
            time.sleep(2.5)
            while self.serial_conn.in_waiting > 0:
                line = self.serial_conn.readline().decode().strip()
                print(f"[Arduino] {line}")
            print(f"✅ Connected to Arduino at {self.port}")
        except Exception as e:
            print(f"❌ Failed to connect to Arduino: {e}")
            self.serial_conn = None
    
    def start_listening(self, detection_callback):
        """Start listening for Arduino messages."""
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
                        if line == "DETECTED" and self.detection_callback:
                            threading.Thread(target=self.detection_callback, daemon=True).start()
                time.sleep(0.01)
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
        self.send_command("START_CONVEYOR")
    
    def stop_conveyor(self):
        self.send_command("STOP_CONVEYOR")
    
    def reject_bottle(self):
        self.send_command("REJECT")
    
    def stop(self):
        self.running = False
        if self.read_thread:
            self.read_thread.join(timeout=1.0)
        if self.serial_conn:
            self.stop_conveyor()
            time.sleep(0.5)
            self.serial_conn.close()


# ============================================================================
# ========================== CAMERA CAPTURE ==================================
# ============================================================================

class CameraCapture:
    """USB camera capture with thread-safe frame access."""
    
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
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, Config.CAMERA_FPS)
        
        actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"📹 Camera opened: {actual_w}x{actual_h}")
        
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
    """YOLOv8-based defect detection with voting mechanism."""
    
    def __init__(self, model_path=Config.MODEL_PATH):
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        print(f"🧠 Loading YOLO model from {model_path}...")
        self.model = YOLO(str(self.model_path))
        print("✅ Model loaded successfully")
    
    def detect_single_frame(self, frame):
        """Run inference on a single frame."""
        results = self.model(frame, conf=Config.CONFIDENCE_THRESHOLD, verbose=False)
        
        if not results or len(results) == 0:
            return {'has_defect': False, 'defect_type': None, 'confidence': 0.0, 'detections': []}
        
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
                
                detection = {'bbox': bbox, 'class_id': cls_id, 'confidence': conf, 'label': label}
                detections.append(detection)
                
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
        """Run detection on multiple frames and use voting mechanism."""
        if not frames:
            return {
                'is_defect': False, 'defect_type': None, 'confidence': 0.0,
                'vote_count': 0, 'frame_results': [], 'best_frame_idx': -1
            }
        
        frame_results = []
        defect_votes = []
        
        for frame in frames:
            result = self.detect_single_frame(frame)
            frame_results.append(result)
            if result['has_defect']:
                defect_votes.append(result['defect_type'])
        
        if len(defect_votes) >= Config.VOTING_THRESHOLD:
            vote_counter = Counter(defect_votes)
            most_common_defect, vote_count = vote_counter.most_common(1)[0]
            
            best_idx = -1
            best_conf = 0.0
            for idx, result in enumerate(frame_results):
                if result['defect_type'] == most_common_defect:
                    if result['confidence'] > best_conf:
                        best_conf = result['confidence']
                        best_idx = idx
            
            return {
                'is_defect': True, 'defect_type': most_common_defect,
                'confidence': best_conf, 'vote_count': vote_count,
                'frame_results': frame_results, 'best_frame_idx': best_idx
            }
        
        return {
            'is_defect': False, 'defect_type': None, 'confidence': 0.0,
            'vote_count': len(defect_votes), 'frame_results': frame_results, 'best_frame_idx': -1
        }


# ============================================================================
# ====================== TIMED EJECTION CONTROLLER ===========================
# ============================================================================

class EjectionScheduler:
    """Schedules bottle ejection at precise time."""
    
    def __init__(self, arduino_controller):
        self.arduino = arduino_controller
        self.pending_ejections = queue.PriorityQueue()
        self.running = False
        self.thread = None
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._ejection_loop, daemon=True)
        self.thread.start()
        print("⏰ Ejection scheduler started")
    
    def _ejection_loop(self):
        while self.running:
            try:
                try:
                    eject_time, bottle_id = self.pending_ejections.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                current_time = time.time()
                wait_time = eject_time - current_time
                
                if wait_time > 0:
                    time.sleep(wait_time)
                
                print(f"⚡ EJECTING bottle #{bottle_id} at {get_timestamp()}")
                self.arduino.reject_bottle()
            except Exception as e:
                print(f"[Ejection Error] {e}")
    
    def schedule_ejection(self, capture_timestamp, bottle_id):
        eject_time = capture_timestamp + Config.PHYSICAL_DELAY
        self.pending_ejections.put((eject_time, bottle_id))
        delay = eject_time - time.time()
        print(f"📅 Scheduled ejection for bottle #{bottle_id} in {delay:.2f}s")
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)


# ============================================================================
# =========================== STATISTICS TRACKER =============================
# ============================================================================

class Statistics:
    """Track system statistics."""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.total_bottles = 0
        self.total_defects = 0
        self.defect_counts = defaultdict(int)
        self.start_time = time.time()
    
    def record_bottle(self, is_defect, defect_type=None):
        with self.lock:
            self.total_bottles += 1
            if is_defect and defect_type:
                self.total_defects += 1
                self.defect_counts[defect_type] += 1
    
    def get_stats(self):
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
        with self.lock:
            self.total_bottles = 0
            self.total_defects = 0
            self.defect_counts.clear()
            self.start_time = time.time()


# ============================================================================
# ============================ TKINTER GUI ===================================
# ============================================================================

class BottleInspectionGUI(tk.Tk):
    """Main Tkinter GUI for bottle inspection system."""
    
    def __init__(self):
        super().__init__()
        
        self.title("🍾 Hệ Thống Kiểm Tra Lỗi Chai Coca-Cola")
        self.geometry("1400x850")
        self.configure(bg="#f0f0f0")
        
        print("="*80)
        print("🍾 Coca-Cola Bottle Defect Detection System - Tkinter Version")
        print("="*80)
        
        # Initialize components
        print("\n📦 Initializing components...")
        self.camera = CameraCapture()
        self.arduino = ArduinoController()
        self.detector = DefectDetector()
        self.ejection_scheduler = EjectionScheduler(self.arduino)
        self.statistics = Statistics()
        
        # State
        self.bottle_counter = 0
        self.conveyor_running = False
        self.camera_running = False
        
        # Image references
        self.live_photo = None
        self.defect_photo = None
        self.latest_defect_frame = None
        
        # Ensure save directory
        if Config.SAVE_DEFECT_IMAGES:
            ensure_directory(Config.DEFECT_SAVE_PATH)
        
        # Build UI
        self._build_ui()
        
        # Setup close handler
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        print("✅ All components initialized\n")
    
    def _build_ui(self):
        """Build Tkinter UI."""
        # === TOP FRAME: Live Feed + Defect Image ===
        top_frame = tk.Frame(self, bg="#f0f0f0")
        top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left: Live Feed
        left_frame = tk.Frame(top_frame, bg="#d0d0d0", width=640, height=480)
        left_frame.pack(side=tk.LEFT, padx=5)
        left_frame.pack_propagate(False)
        
        tk.Label(left_frame, text="📹 VIDEO TRỰC TIẾP", font=("Arial", 12, "bold"), 
                bg="#d0d0d0").pack(pady=5)
        self.lbl_live = tk.Label(left_frame, bg="#d0d0d0", text="Camera chưa bật")
        self.lbl_live.pack(fill=tk.BOTH, expand=True)
        
        # Right: Defect Image
        right_frame = tk.Frame(top_frame, bg="#d0d0d0", width=640, height=480)
        right_frame.pack(side=tk.LEFT, padx=5)
        right_frame.pack_propagate(False)
        
        tk.Label(right_frame, text="⚠️ CHAI LỖI GẦN NHẤT", font=("Arial", 12, "bold"),
                bg="#d0d0d0").pack(pady=5)
        self.lbl_defect = tk.Label(right_frame, bg="#d0d0d0", text="Chưa có chai lỗi")
        self.lbl_defect.pack(fill=tk.BOTH, expand=True)
        
        # === BOTTOM FRAME: Controls + Statistics ===
        bottom_frame = tk.Frame(self, bg="#e8f4f8", height=300)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        # Controls Section
        control_frame = tk.LabelFrame(bottom_frame, text="⚙️ ĐIỀU KHIỂN", 
                                     font=("Arial", 11, "bold"), bg="#e8f4f8")
        control_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)
        
        self.btn_camera = tk.Button(control_frame, text="▶️ BẬT CAMERA",
                                    font=("Arial", 11), width=20, height=2,
                                    bg="#90EE90", command=self._toggle_camera)
        self.btn_camera.pack(padx=10, pady=5)
        
        self.btn_conveyor = tk.Button(control_frame, text="▶️ CHẠY BĂNG CHUYỀN",
                                      font=("Arial", 11), width=20, height=2,
                                      bg="#87CEEB", command=self._toggle_conveyor)
        self.btn_conveyor.pack(padx=10, pady=5)
        
        tk.Button(control_frame, text="🔄 RESET THỐNG KÊ",
                 font=("Arial", 11), width=20, height=2,
                 bg="#FFD700", command=self._reset_stats).pack(padx=10, pady=5)
        
        tk.Button(control_frame, text="⏹️ THOÁT",
                 font=("Arial", 11), width=20, height=2,
                 bg="#FF6B6B", command=self._on_close).pack(padx=10, pady=5)
        
        # Statistics Section
        stats_frame = tk.LabelFrame(bottom_frame, text="📊 THỐNG KÊ",
                                   font=("Arial", 11, "bold"), bg="#e8f4f8")
        stats_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Stats labels
        self.lbl_total = tk.Label(stats_frame, text="Tổng số chai: 0",
                                 font=("Arial", 14, "bold"), bg="#e8f4f8")
        self.lbl_total.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        
        self.lbl_good = tk.Label(stats_frame, text="✅ Chai tốt: 0",
                                font=("Arial", 12), bg="#e8f4f8", fg="green")
        self.lbl_good.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        
        self.lbl_bad = tk.Label(stats_frame, text="❌ Chai lỗi: 0",
                               font=("Arial", 12), bg="#e8f4f8", fg="red")
        self.lbl_bad.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        # Individual defect counts
        tk.Label(stats_frame, text="Chi tiết lỗi:", font=("Arial", 11, "bold"),
                bg="#e8f4f8").grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        
        self.lbl_defect_details = tk.Label(stats_frame, text="",
                                          font=("Arial", 10), bg="#e8f4f8", justify=tk.LEFT)
        self.lbl_defect_details.grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        
        self.lbl_uptime = tk.Label(stats_frame, text="⏱️ Uptime: 0m 0s",
                                  font=("Arial", 10), bg="#e8f4f8")
        self.lbl_uptime.grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        
        self.lbl_fps = tk.Label(stats_frame, text="📹 FPS: 0.0",
                               font=("Arial", 10), bg="#e8f4f8")
        self.lbl_fps.grid(row=5, column=0, columnspan=2, sticky="w", padx=10, pady=5)
    
    def _toggle_camera(self):
        """Toggle camera on/off."""
        if not self.camera_running:
            if self.camera.start():
                self.camera_running = True
                self.btn_camera.config(text="⏸️ TẮT CAMERA", bg="#FFB6C1")
                self._update_live_feed()
                print("[UI] Camera ON")
            else:
                messagebox.showerror("Lỗi", "Không thể mở camera!")
        else:
            self.camera_running = False
            self.camera.stop()
            self.btn_camera.config(text="▶️ BẬT CAMERA", bg="#90EE90")
            self.lbl_live.config(image="", text="Camera đã tắt")
            print("[UI] Camera OFF")
    
    def _toggle_conveyor(self):
        """Toggle conveyor on/off."""
        if not self.conveyor_running:
            self.arduino.start_conveyor()
            self.conveyor_running = True
            self.btn_conveyor.config(text="⏸️ DỪNG BĂNG CHUYỀN", bg="#FF6B6B")
            
            # Start listening for bottle detection
            self.arduino.start_listening(self._on_bottle_detected)
            self.ejection_scheduler.start()
            print("[UI] Conveyor STARTED")
        else:
            self.arduino.stop_conveyor()
            self.conveyor_running = False
            self.btn_conveyor.config(text="▶️ CHẠY BĂNG CHUYỀN", bg="#87CEEB")
            print("[UI] Conveyor STOPPED")
    
    def _reset_stats(self):
        """Reset statistics."""
        if messagebox.askyesno("Xác nhận", "Reset tất cả thống kê?"):
            self.statistics.reset()
            self.bottle_counter = 0
            print("[UI] Statistics reset")
    
    def _on_bottle_detected(self):
        """Callback when Arduino detects a bottle."""
        self.bottle_counter += 1
        bottle_id = self.bottle_counter
        
        print(f"\n{'='*80}")
        print(f"🍾 BOTTLE #{bottle_id} DETECTED at {get_timestamp()}")
        print(f"{'='*80}")
        
        # Wait for bottle to reach camera
        time.sleep(Config.DELAY_SENSOR_TO_CAPTURE)
        
        # Burst capture
        capture_timestamp = time.time()
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
        
        # AI detection with voting
        print(f"🧠 Running AI detection with voting...")
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
            
            # Update defect image
            best_idx = detection_result['best_frame_idx']
            if best_idx >= 0:
                best_frame = frames[best_idx]
                best_detections = detection_result['frame_results'][best_idx]['detections']
                self._update_defect_image(best_frame, best_detections, defect_type)
                
                # Save image
                if Config.SAVE_DEFECT_IMAGES:
                    filename = f"defect_{bottle_id}_{defect_type}_{get_timestamp_filename()}.jpg"
                    save_path = Path(Config.DEFECT_SAVE_PATH) / filename
                    cv2.imwrite(str(save_path), best_frame)
                    print(f"💾 Saved: {save_path}")
        else:
            print(f"✅ GOOD BOTTLE")
            print(f"   Defect votes: {vote_count}/{Config.BURST_COUNT} (below threshold)")
        
        # Update statistics
        self.statistics.record_bottle(is_defect, defect_type)
        print(f"{'='*80}\n")
    
    def _update_live_feed(self):
        """Update live camera feed."""
        if self.camera_running:
            frame, fps = self.camera.get_frame()
            if frame is not None:
                # Resize for display
                display_frame = cv2.resize(frame, (620, 440))
                rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                photo = ImageTk.PhotoImage(img)
                
                self.lbl_live.config(image=photo, text="")
                self.live_photo = photo
                
                # Update FPS
                self.lbl_fps.config(text=f"📹 FPS: {fps:.1f}")
            
            # Update statistics
            stats = self.statistics.get_stats()
            self.lbl_total.config(text=f"Tổng số chai: {stats['total_bottles']}")
            self.lbl_good.config(text=f"✅ Chai tốt: {stats['total_good']}")
            self.lbl_bad.config(text=f"❌ Chai lỗi: {stats['total_defects']}")
            
            # Defect details
            details = []
            for defect_type, vietnamese_name in Config.DEFECT_CLASSES.items():
                count = stats['defect_counts'].get(defect_type, 0)
                details.append(f"  • {vietnamese_name}: {count}")
            self.lbl_defect_details.config(text="\n".join(details))
            
            # Uptime
            uptime_min = int(stats['uptime_seconds'] / 60)
            uptime_sec = int(stats['uptime_seconds'] % 60)
            self.lbl_uptime.config(text=f"⏱️ Uptime: {uptime_min}m {uptime_sec}s")
        
        # Schedule next update
        self.after(33, self._update_live_feed)  # ~30 FPS
    
    def _update_defect_image(self, frame, detections, defect_type):
        """Update defect image with bounding boxes."""
        annotated = frame.copy()
        
        # Draw bounding boxes
        for det in detections:
            bbox = det['bbox']
            label = det['label']
            conf = det['confidence']
            
            x1, y1, x2, y2 = bbox
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 2)
            text = f"{label} {conf:.2f}"
            cv2.putText(annotated, text, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # Add defect label
        cv2.putText(annotated, f"LOI: {Config.DEFECT_CLASSES.get(defect_type, defect_type)}",
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
        
        # Display
        display_frame = cv2.resize(annotated, (620, 440))
        rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        photo = ImageTk.PhotoImage(img)
        
        self.lbl_defect.config(image=photo, text="")
        self.defect_photo = photo
        self.latest_defect_frame = annotated
    
    def _on_close(self):
        """Clean shutdown."""
        print("\n🛑 Shutting down system...")
        
        self.camera_running = False
        if self.conveyor_running:
            self.arduino.stop_conveyor()
        
        self.ejection_scheduler.stop()
        self.camera.stop()
        self.arduino.stop()
        
        # Print final stats
        stats = self.statistics.get_stats()
        print("\n" + "="*80)
        print("📊 FINAL STATISTICS")
        print("="*80)
        print(f"Total Bottles: {stats['total_bottles']}")
        print(f"Good: {stats['total_good']}")
        print(f"Defects: {stats['total_defects']}")
        for defect_type, vietnamese_name in Config.DEFECT_CLASSES.items():
            count = stats['defect_counts'].get(defect_type, 0)
            print(f"  - {vietnamese_name}: {count}")
        print("="*80 + "\n")
        
        self.destroy()


# ============================================================================
# ================================= MAIN =====================================
# ============================================================================

def main():
    """Entry point."""
    try:
        app = BottleInspectionGUI()
        app.mainloop()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

