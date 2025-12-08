#!/usr/bin/env python3
"""
Test YOLOv8 Model - Coca-Cola Sorting System
Hiển thị camera live và vẽ bounding boxes real-time
Dùng model best.pt
"""

import cv2
import numpy as np
import time
import os

# Kiểm tra YOLOv8
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
    print("✓ YOLOv8 (ultralytics) available")
except ImportError:
    YOLO_AVAILABLE = False
    print("✗ YOLOv8 not available - Install ultralytics")
    print("  Run: pip install ultralytics")
    exit(1)

# ============================================
# CẤU HÌNH
# ============================================
MODEL_PATH = "model/best.pt"
CAMERA_ID = 0

# Confidence threshold
CONFIDENCE_THRESHOLD = 0.5  # Có thể điều chỉnh (0.0 - 1.0)

# Tên các class (0-7)
CLASS_NAMES = [
    'Cap-Defect',       # 0 - Đỏ
    'Filling-Defect',   # 1 - Đỏ
    'Label-Defect',     # 2 - Đỏ
    'Wrong-Product',    # 3 - Đỏ
    'cap',              # 4 - Xanh
    'coca',             # 5 - Cyan
    'filled',           # 6 - Vàng
    'label'             # 7 - Magenta
]

# Màu cho từng class (BGR format)
CLASS_COLORS = [
    (0, 0, 255),      # 0: Cap-Defect - Đỏ
    (0, 0, 255),      # 1: Filling-Defect - Đỏ
    (0, 0, 255),      # 2: Label-Defect - Đỏ
    (0, 0, 255),      # 3: Wrong-Product - Đỏ
    (0, 255, 0),      # 4: cap - Xanh lá
    (255, 255, 0),    # 5: coca - Cyan
    (0, 255, 255),    # 6: filled - Vàng
    (255, 0, 255)     # 7: label - Magenta
]

# Defect classes
DEFECT_CLASSES = {0, 1, 2, 3}


# ============================================
# FUNCTIONS
# ============================================

def load_model():
    """Load YOLOv8 model"""
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model file not found: {MODEL_PATH}")
        print(f"   Please make sure model/best.pt exists")
        return None
    
    try:
        print(f"Loading YOLOv8 model from {MODEL_PATH}...")
        model = YOLO(MODEL_PATH)
        print(f"✓ Model loaded successfully!")
        return model
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return None


def draw_detections(frame, results):
    """
    Vẽ bounding boxes và labels lên frame
    
    Args:
        frame: OpenCV frame
        results: YOLOv8 results object
    
    Returns:
        annotated_frame: Frame with bounding boxes
        detection_count: Number of detections
        detection_info: List of detection info strings
    """
    detection_count = 0
    detection_info = []
    
    if results.boxes is None or len(results.boxes) == 0:
        return frame, 0, []
    
    for box in results.boxes:
        # Get box info
        x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
        confidence = float(box.conf[0])
        class_id = int(box.cls[0])
        
        if class_id >= len(CLASS_NAMES):
            continue
        
        class_name = CLASS_NAMES[class_id]
        color = CLASS_COLORS[class_id]
        
        # Vẽ bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # Tạo label
        label = f"{class_name}: {confidence:.2f}"
        
        # Tính kích thước text
        (text_width, text_height), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
        )
        
        # Vẽ background cho text
        cv2.rectangle(
            frame,
            (x1, y1 - text_height - 10),
            (x1 + text_width + 10, y1),
            color,
            -1  # Filled
        )
        
        # Vẽ text
        cv2.putText(
            frame,
            label,
            (x1 + 5, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),  # White
            2
        )
        
        detection_count += 1
        detection_info.append(f"{class_name}: {confidence:.2f}")
    
    return frame, detection_count, detection_info


def draw_info_panel(frame, fps, detection_count, detection_info, conf_threshold):
    """Vẽ panel thông tin"""
    h, w = frame.shape[:2]
    
    # Background cho info panel
    panel_height = 150
    cv2.rectangle(frame, (10, 10), (400, panel_height), (0, 0, 0), -1)
    
    # FPS
    cv2.putText(frame, f"FPS: {fps:.1f}", (20, 35),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Detections count
    color = (0, 255, 255) if detection_count > 0 else (100, 100, 100)
    cv2.putText(frame, f"Detections: {detection_count}", (20, 65),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    
    # Confidence threshold
    cv2.putText(frame, f"Confidence: {conf_threshold:.2f}", (20, 95),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
    
    # Controls
    cv2.putText(frame, "Q:Quit | S:Save | +/-:Conf", (20, 125),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
    
    return frame


def draw_legend(frame):
    """Vẽ legend các class"""
    h, w = frame.shape[:2]
    legend_x = w - 220
    legend_y = 10
    
    # Background
    legend_height = 40 + len(CLASS_NAMES) * 30
    cv2.rectangle(frame, (legend_x, legend_y), 
                 (w - 10, legend_y + legend_height), (0, 0, 0), -1)
    
    # Title
    cv2.putText(frame, "Classes:", (legend_x + 10, legend_y + 25),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Draw each class
    for i, class_name in enumerate(CLASS_NAMES):
        y = legend_y + 50 + i * 30
        color = CLASS_COLORS[i]
        
        # Color box
        cv2.rectangle(frame, (legend_x + 10, y - 12), 
                     (legend_x + 35, y + 5), color, -1)
        
        # Class name
        cv2.putText(frame, class_name, (legend_x + 42, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    
    return frame


def draw_detection_list(frame, detection_info):
    """Vẽ danh sách detections bên dưới"""
    if not detection_info:
        return frame
    
    h, w = frame.shape[:2]
    
    # Background
    list_height = min(len(detection_info) * 25 + 40, 200)
    cv2.rectangle(frame, (10, h - list_height - 10), 
                 (450, h - 10), (0, 0, 0), -1)
    
    # Title
    cv2.putText(frame, "Detected Objects:", (20, h - list_height + 15),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # List items
    for i, info in enumerate(detection_info[:7]):  # Max 7 items
        y = h - list_height + 45 + i * 25
        cv2.putText(frame, f"• {info}", (30, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    
    if len(detection_info) > 7:
        cv2.putText(frame, f"... +{len(detection_info)-7} more", 
                   (30, h - list_height + 45 + 7 * 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
    
    return frame


def analyze_bottle(detection_info):
    """
    Phân tích chai dựa trên detections
    
    Returns:
        status: 'OK', 'NG', or 'Unknown'
        reason: Lý do
    """
    detected_classes = set()
    defects = []
    
    for info in detection_info:
        class_name = info.split(':')[0].strip()
        
        # Find class ID
        if class_name in CLASS_NAMES:
            class_id = CLASS_NAMES.index(class_name)
            detected_classes.add(class_id)
            
            # Check for defects
            if class_id in DEFECT_CLASSES:
                defects.append(class_name)
    
    # Check components
    has_cap = 4 in detected_classes
    has_filled = 6 in detected_classes
    has_label = 7 in detected_classes
    
    # Apply sorting logic
    if defects:
        return 'NG', f"Defects: {', '.join(defects)}"
    
    missing = []
    if not has_cap:
        missing.append('cap')
    if not has_filled:
        missing.append('filled')
    if not has_label:
        missing.append('label')
    
    if missing:
        return 'NG', f"Missing: {', '.join(missing)}"
    
    if has_cap and has_filled and has_label:
        return 'OK', "All components present"
    
    return 'Unknown', "Waiting for detection..."


def draw_status_indicator(frame, status, reason):
    """Vẽ status indicator"""
    h, w = frame.shape[:2]
    
    # Position at top center
    center_x = w // 2
    
    if status == 'OK':
        color = (0, 255, 0)
        text = "✓ OK"
    elif status == 'NG':
        color = (0, 0, 255)
        text = "✗ NG"
    else:
        color = (150, 150, 150)
        text = "?"
    
    # Background
    cv2.rectangle(frame, (center_x - 150, 10), 
                 (center_x + 150, 110), (0, 0, 0), -1)
    
    # Status text
    cv2.putText(frame, text, (center_x - 50, 60),
               cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)
    
    # Reason
    cv2.putText(frame, reason, (center_x - 140, 95),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    return frame


# ============================================
# MAIN
# ============================================

def main():
    print("=" * 60)
    print("🥤 TEST YOLOV8 MODEL - LIVE DETECTION")
    print("=" * 60)
    print()
    
    # Load model
    model = load_model()
    if model is None:
        return
    
    print()
    
    # Open camera
    print("Opening camera...")
    cap = cv2.VideoCapture(CAMERA_ID)
    
    if not cap.isOpened():
        print("❌ Cannot open camera!")
        print(f"   Try changing CAMERA_ID (current: {CAMERA_ID})")
        return
    
    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"✓ Camera opened: {actual_width}x{actual_height}")
    print()
    print("=" * 60)
    print("CONTROLS:")
    print("  Q - Quit")
    print("  S - Save screenshot")
    print("  + - Increase confidence threshold")
    print("  - - Decrease confidence threshold")
    print("  SPACE - Pause/Resume")
    print("=" * 60)
    print()
    
    # Variables
    fps = 0
    frame_count = 0
    start_time = time.time()
    
    paused = False
    current_frame = None
    screenshot_count = 0
    
    conf_threshold = CONFIDENCE_THRESHOLD
    
    print("🚀 System ready! Press Q to quit")
    print()
    
    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                print("⚠ Failed to read frame")
                continue
            current_frame = frame.copy()
        else:
            frame = current_frame.copy()
        
        # Run YOLOv8 inference
        results = model(frame, conf=conf_threshold, verbose=False)[0]
        
        # Draw detections
        frame, detection_count, detection_info = draw_detections(frame, results)
        
        # Analyze bottle status
        status, reason = analyze_bottle(detection_info)
        
        # Calculate FPS
        frame_count += 1
        elapsed = time.time() - start_time
        if elapsed >= 1.0:
            fps = frame_count / elapsed
            frame_count = 0
            start_time = time.time()
        
        # Draw UI elements
        frame = draw_info_panel(frame, fps, detection_count, detection_info, conf_threshold)
        frame = draw_legend(frame)
        frame = draw_detection_list(frame, detection_info)
        frame = draw_status_indicator(frame, status, reason)
        
        # Draw paused indicator
        if paused:
            h, w = frame.shape[:2]
            cv2.putText(frame, "⏸ PAUSED", (w//2 - 100, h - 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        
        # Show frame
        cv2.imshow('YOLOv8 Model Test - Coca-Cola', frame)
        
        # Handle keyboard
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q') or key == ord('Q'):
            print("Quitting...")
            break
        
        elif key == ord('s') or key == ord('S'):
            screenshot_count += 1
            filename = f"test_screenshot_{screenshot_count:03d}.jpg"
            cv2.imwrite(filename, frame)
            print(f"📸 Screenshot saved: {filename}")
        
        elif key == ord('+') or key == ord('='):
            conf_threshold = min(0.95, conf_threshold + 0.05)
            print(f"Confidence threshold: {conf_threshold:.2f}")
        
        elif key == ord('-') or key == ord('_'):
            conf_threshold = max(0.05, conf_threshold - 0.05)
            print(f"Confidence threshold: {conf_threshold:.2f}")
        
        elif key == ord(' '):
            paused = not paused
            status_text = "⏸ Paused" if paused else "▶ Resumed"
            print(status_text)
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print()
    print("✓ Done! Goodbye! 👋")


if __name__ == "__main__":
    main()

