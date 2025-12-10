#!/usr/bin/env python3
"""
Test Model Live - Coca-Cola Sorting System
Hiển thị camera và vẽ bounding boxes real-time từ model NCNN
"""

import cv2
import numpy as np
import time
import os
import ncnn

# Kiểm tra NCNN
try:
    import ncnn
    NCNN_AVAILABLE = True
    print("✓ NCNN available")
except ImportError:
    NCNN_AVAILABLE = False
    print("✗ NCNN not available - Install ncnn-python")
    print("  This script requires NCNN to run")
    exit(1)

# ============================================
# CẤU HÌNH MODEL
# ============================================
MODEL_PATH = "model/best_ncnn_model"
MODEL_PARAM = os.path.join(MODEL_PATH, "model.ncnn.param")
MODEL_BIN = os.path.join(MODEL_PATH, "model.ncnn.bin")

INPUT_SIZE = 640  # Model YOLO 640x640
CONFIDENCE_THRESHOLD = 0.5  # Ngưỡng confidence
NMS_THRESHOLD = 0.45  # Non-Maximum Suppression threshold

# Tên các class (0-7)
CLASS_NAMES = [
    'Cap-Defect',       # 0
    'Filling-Defect',   # 1
    'Label-Defect',     # 2
    'Wrong-Product',    # 3
    'cap',              # 4
    'coca',             # 5
    'filled',           # 6
    'label'             # 7
]

# Màu sắc cho từng loại (BGR format)
DEFECT_COLOR = (0, 0, 255)      # Đỏ cho defects (0-3)
COMPONENT_COLOR = (0, 255, 0)   # Xanh lá cho components (4-7)

# Màu chi tiết cho từng class
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


# ============================================
# HÀM XỬ LÝ
# ============================================

def load_model():
    """Load NCNN model"""
    if not os.path.exists(MODEL_PARAM) or not os.path.exists(MODEL_BIN):
        print(f"❌ Model files not found!")
        print(f"   Param: {MODEL_PARAM}")
        print(f"   Bin: {MODEL_BIN}")
        return None
    
    net = ncnn.Net()
    
    # Cấu hình NCNN
    net.opt.use_vulkan_compute = False  # Tắt Vulkan nếu không hỗ trợ
    net.opt.num_threads = 4  # Số threads
    
    # Load model
    ret_param = net.load_param(MODEL_PARAM)
    ret_model = net.load_model(MODEL_BIN)
    
    if ret_param != 0 or ret_model != 0:
        print(f"❌ Failed to load model!")
        return None
    
    print(f"✓ Model loaded successfully")
    return net


def preprocess_frame(frame):
    """
    Tiền xử lý frame cho NCNN
    Resize về 640x640 và normalize
    """
    # Resize
    img = cv2.resize(frame, (INPUT_SIZE, INPUT_SIZE))
    
    # Convert BGR to RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    return img_rgb


def parse_yolo_output(output, img_w, img_h):
    """
    Parse output từ YOLO model
    
    Args:
        output: NCNN output tensor
        img_w: Original image width
        img_h: Original image height
    
    Returns:
        List of detections: [(class_id, confidence, x, y, w, h), ...]
    """
    detections = []
    
    try:
        # Convert NCNN Mat to numpy
        out_np = np.array(output)
        
        # Debug: In shape để biết format
        print(f"[DEBUG] Output shape: {out_np.shape}")
        
        # YOLOv8 NCNN output thường có shape: (1, 84, 8400) hoặc (84, 8400)
        # 84 = 4 (bbox) + 80 (classes, nhưng ta chỉ dùng 8)
        # 8400 = số anchor boxes
        
        # Remove batch dimension nếu có
        if len(out_np.shape) == 3:
            out_np = out_np[0]
        
        # Nếu shape là (num_classes+4, num_boxes), transpose về (num_boxes, num_classes+4)
        if out_np.shape[0] < out_np.shape[1]:
            out_np = out_np.T
        
        print(f"[DEBUG] After transpose: {out_np.shape}")
        print(f"[DEBUG] Sample detection: {out_np[0][:12]}")  # In 12 giá trị đầu
        
        # Scale factors
        scale_x = img_w / INPUT_SIZE
        scale_y = img_h / INPUT_SIZE
        
        # Parse each detection
        num_detections = min(out_np.shape[0], 8400)  # Limit số detections
        
        for i in range(num_detections):
            detection = out_np[i]
            
            # YOLOv8 format: [x_center, y_center, width, height, class1_score, class2_score, ...]
            # Không có objectness score riêng
            
            if len(detection) < 4 + len(CLASS_NAMES):
                continue
            
            # Extract box coordinates (center format, normalized 0-1)
            x_center = detection[0] * scale_x
            y_center = detection[1] * scale_y
            width = detection[2] * scale_x
            height = detection[3] * scale_y
            
            # Class scores (chỉ lấy 8 classes đầu)
            class_scores = detection[4:4 + len(CLASS_NAMES)]
            
            # Get best class
            class_id = np.argmax(class_scores)
            confidence = class_scores[class_id]
            
            # Filter by threshold
            if confidence > CONFIDENCE_THRESHOLD:
                # Convert to corner format
                x1 = int(x_center - width / 2)
                y1 = int(y_center - height / 2)
                x2 = int(x_center + width / 2)
                y2 = int(y_center + height / 2)
                
                # Clamp to image boundaries
                x1 = max(0, min(x1, img_w))
                y1 = max(0, min(y1, img_h))
                x2 = max(0, min(x2, img_w))
                y2 = max(0, min(y2, img_h))
                
                # Chỉ thêm nếu box hợp lệ
                if x2 > x1 and y2 > y1:
                    detections.append({
                        'class_id': int(class_id),
                        'class_name': CLASS_NAMES[class_id],
                        'confidence': float(confidence),
                        'bbox': [x1, y1, x2, y2]
                    })
                    
                    # Debug: In detection đầu tiên
                    if len(detections) == 1:
                        print(f"[DEBUG] First detection: {CLASS_NAMES[class_id]} at ({x1},{y1})-({x2},{y2}), conf={confidence:.2f}")
    
    except Exception as e:
        print(f"⚠ Parse error: {e}")
        import traceback
        traceback.print_exc()
    
    return detections


def apply_nms(detections, iou_threshold=NMS_THRESHOLD):
    """
    Apply Non-Maximum Suppression to remove overlapping boxes
    """
    if len(detections) == 0:
        return []
    
    # Extract boxes and scores
    boxes = np.array([d['bbox'] for d in detections])
    scores = np.array([d['confidence'] for d in detections])
    
    # Compute areas
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    
    # Sort by score
    order = scores.argsort()[::-1]
    
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        
        # Compute IoU
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        
        w = np.maximum(0.0, xx2 - xx1 + 1)
        h = np.maximum(0.0, yy2 - yy1 + 1)
        inter = w * h
        
        iou = inter / (areas[i] + areas[order[1:]] - inter)
        
        # Keep boxes with IoU less than threshold
        inds = np.where(iou <= iou_threshold)[0]
        order = order[inds + 1]
    
    return [detections[i] for i in keep]


def draw_detections(frame, detections):
    """
    Vẽ bounding boxes và labels lên frame
    """
    for det in detections:
        class_id = det['class_id']
        class_name = det['class_name']
        confidence = det['confidence']
        x1, y1, x2, y2 = det['bbox']
        
        # Chọn màu
        color = CLASS_COLORS[class_id]
        
        # Vẽ box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # Tạo label
        label = f"{class_name}: {confidence:.2f}"
        
        # Tính kích thước text
        (text_width, text_height), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
        )
        
        # Vẽ background cho text
        cv2.rectangle(
            frame,
            (x1, y1 - text_height - 10),
            (x1 + text_width, y1),
            color,
            -1  # Filled
        )
        
        # Vẽ text
        cv2.putText(
            frame,
            label,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),  # Trắng
            2
        )
    
    return frame


def draw_info(frame, fps, num_detections):
    """
    Vẽ thông tin hệ thống lên frame
    """
    # Background cho info
    cv2.rectangle(frame, (10, 10), (300, 100), (0, 0, 0), -1)
    
    # FPS
    cv2.putText(
        frame,
        f"FPS: {fps:.1f}",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )
    
    # Số detections
    cv2.putText(
        frame,
        f"Detections: {num_detections}",
        (20, 65),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2
    )
    
    # Instructions
    cv2.putText(
        frame,
        "Press Q to quit",
        (20, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (200, 200, 200),
        1
    )
    
    return frame


def draw_class_legend(frame):
    """
    Vẽ legend các class ở góc phải
    """
    legend_x = frame.shape[1] - 200
    legend_y = 10
    
    # Background
    cv2.rectangle(
        frame,
        (legend_x, legend_y),
        (frame.shape[1] - 10, legend_y + 30 + len(CLASS_NAMES) * 25),
        (0, 0, 0),
        -1
    )
    
    # Title
    cv2.putText(
        frame,
        "Classes:",
        (legend_x + 10, legend_y + 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1
    )
    
    # Draw each class
    for i, class_name in enumerate(CLASS_NAMES):
        y = legend_y + 45 + i * 25
        color = CLASS_COLORS[i]
        
        # Color box
        cv2.rectangle(
            frame,
            (legend_x + 10, y - 10),
            (legend_x + 30, y + 5),
            color,
            -1
        )
        
        # Class name
        cv2.putText(
            frame,
            class_name,
            (legend_x + 35, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (255, 255, 255),
            1
        )
    
    return frame


# ============================================
# MAIN
# ============================================

def main():
    print("=" * 60)
    print("🥤 COCA-COLA MODEL TEST - LIVE DETECTION")
    print("=" * 60)
    print()
    
    # Load model
    print("Loading model...")
    net = load_model()
    if net is None:
        return
    
    print()
    
    # Mở camera
    print("Opening camera...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Cannot open camera!")
        print("   Try changing camera ID or check connection")
        return
    
    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"✓ Camera opened: {actual_width}x{actual_height}")
    print()
    print("=" * 60)
    print("CONTROLS:")
    print("  Q - Quit")
    print("  S - Save screenshot")
    print("  SPACE - Pause/Resume")
    print("=" * 60)
    print()
    
    # FPS counter
    fps = 0
    frame_count = 0
    start_time = time.time()
    
    paused = False
    screenshot_count = 0
    
    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                print("⚠ Failed to read frame")
                continue
            
            current_frame = frame.copy()
        else:
            # Use last frame when paused
            frame = current_frame.copy()
        
        # Measure inference time
        inf_start = time.time()
        
        # Preprocess
        img_preprocessed = preprocess_frame(frame)
        
        # Create NCNN Mat
        mat_in = ncnn.Mat.from_pixels(
            img_preprocessed,
            ncnn.Mat.PixelType.PIXEL_RGB,
            INPUT_SIZE,
            INPUT_SIZE
        )
        
        # Normalize (0-1 range)
        mat_in.substract_mean_normalize(
            [0, 0, 0],
            [1/255.0, 1/255.0, 1/255.0]
        )
        
        # Run inference
        with net.create_extractor() as ex:
            ex.input("in0", mat_in)
            ret, mat_out = ex.extract("out0")
        
        # Parse output
        detections = parse_yolo_output(mat_out, actual_width, actual_height)
        
        # Apply NMS
        detections = apply_nms(detections)
        
        inf_time = time.time() - inf_start
        
        # Draw detections
        frame = draw_detections(frame, detections)
        
        # Calculate FPS
        frame_count += 1
        elapsed = time.time() - start_time
        if elapsed >= 1.0:
            fps = frame_count / elapsed
            frame_count = 0
            start_time = time.time()
        
        # Draw info
        frame = draw_info(frame, fps, len(detections))
        frame = draw_class_legend(frame)
        
        # Draw inference time
        cv2.putText(
            frame,
            f"Inference: {inf_time*1000:.1f}ms",
            (10, frame.shape[0] - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2
        )
        
        # Draw paused indicator
        if paused:
            cv2.putText(
                frame,
                "PAUSED",
                (frame.shape[1]//2 - 80, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.5,
                (0, 0, 255),
                3
            )
        
        # Show frame
        cv2.imshow('Coca-Cola Model Test', frame)
        
        # Handle keyboard
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q') or key == ord('Q'):
            print("Quitting...")
            break
        elif key == ord('s') or key == ord('S'):
            screenshot_count += 1
            filename = f"screenshot_{screenshot_count:03d}.jpg"
            cv2.imwrite(filename, frame)
            print(f"📸 Screenshot saved: {filename}")
        elif key == ord(' '):
            paused = not paused
            print(f"{'⏸ Paused' if paused else '▶ Resumed'}")
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print()
    print("✓ Done!")


if __name__ == "__main__":
    main()

