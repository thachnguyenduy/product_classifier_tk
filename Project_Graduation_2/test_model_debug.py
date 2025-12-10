#!/usr/bin/env python3
"""
Debug version - Test nhiều cách parse YOLO output khác nhau
"""

import cv2
import numpy as np
import time
import os
import ncnn

MODEL_PATH = "model/best_ncnn_model"
MODEL_PARAM = os.path.join(MODEL_PATH, "model.ncnn.param")
MODEL_BIN = os.path.join(MODEL_PATH, "model.ncnn.bin")

INPUT_SIZE = 640
CONFIDENCE_THRESHOLD = 0.3  # Giảm xuống để dễ thấy detections

CLASS_NAMES = [
    'Cap-Defect', 'Filling-Defect', 'Label-Defect', 'Wrong-Product',
    'cap', 'coca', 'filled', 'label'
]

def load_model():
    """Load NCNN model"""
    if not os.path.exists(MODEL_PARAM) or not os.path.exists(MODEL_BIN):
        print(f"❌ Model files not found!")
        return None
    
    net = ncnn.Net()
    net.opt.use_vulkan_compute = False
    net.opt.num_threads = 4
    
    ret_param = net.load_param(MODEL_PARAM)
    ret_model = net.load_model(MODEL_BIN)
    
    if ret_param != 0 or ret_model != 0:
        print(f"❌ Failed to load model!")
        return None
    
    print(f"✓ Model loaded")
    return net


def parse_method_1(output, img_w, img_h):
    """Method 1: YOLOv8 standard format (x,y,w,h normalized)"""
    detections = []
    out_np = np.array(output)
    
    if len(out_np.shape) == 3:
        out_np = out_np[0]
    
    if out_np.shape[0] < out_np.shape[1]:
        out_np = out_np.T
    
    for detection in out_np:
        if len(detection) < 4 + len(CLASS_NAMES):
            continue
        
        # Tọa độ đã normalized (0-640)
        x_center = detection[0]
        y_center = detection[1]
        width = detection[2]
        height = detection[3]
        
        class_scores = detection[4:4 + len(CLASS_NAMES)]
        class_id = np.argmax(class_scores)
        confidence = class_scores[class_id]
        
        if confidence > CONFIDENCE_THRESHOLD:
            # Scale to image size
            x_center = x_center * img_w / INPUT_SIZE
            y_center = y_center * img_h / INPUT_SIZE
            width = width * img_w / INPUT_SIZE
            height = height * img_h / INPUT_SIZE
            
            x1 = int(x_center - width / 2)
            y1 = int(y_center - height / 2)
            x2 = int(x_center + width / 2)
            y2 = int(y_center + height / 2)
            
            x1 = max(0, min(x1, img_w))
            y1 = max(0, min(y1, img_h))
            x2 = max(0, min(x2, img_w))
            y2 = max(0, min(y2, img_h))
            
            if x2 > x1 and y2 > y1:
                detections.append({
                    'class_id': int(class_id),
                    'class_name': CLASS_NAMES[class_id],
                    'confidence': float(confidence),
                    'bbox': [x1, y1, x2, y2]
                })
    
    return detections


def parse_method_2(output, img_w, img_h):
    """Method 2: Coordinates already in pixel space"""
    detections = []
    out_np = np.array(output)
    
    if len(out_np.shape) == 3:
        out_np = out_np[0]
    
    if out_np.shape[0] < out_np.shape[1]:
        out_np = out_np.T
    
    for detection in out_np:
        if len(detection) < 4 + len(CLASS_NAMES):
            continue
        
        # Tọa độ đã là pixel (trong ảnh 640x640)
        x_center = detection[0]
        y_center = detection[1]
        width = detection[2]
        height = detection[3]
        
        class_scores = detection[4:4 + len(CLASS_NAMES)]
        class_id = np.argmax(class_scores)
        confidence = class_scores[class_id]
        
        if confidence > CONFIDENCE_THRESHOLD:
            # Không cần scale, chỉ convert to corners
            x1 = int(x_center - width / 2)
            y1 = int(y_center - height / 2)
            x2 = int(x_center + width / 2)
            y2 = int(y_center + height / 2)
            
            # Scale to original image size
            scale_x = img_w / INPUT_SIZE
            scale_y = img_h / INPUT_SIZE
            
            x1 = int(x1 * scale_x)
            y1 = int(y1 * scale_y)
            x2 = int(x2 * scale_x)
            y2 = int(y2 * scale_y)
            
            x1 = max(0, min(x1, img_w))
            y1 = max(0, min(y1, img_h))
            x2 = max(0, min(x2, img_w))
            y2 = max(0, min(y2, img_h))
            
            if x2 > x1 and y2 > y1:
                detections.append({
                    'class_id': int(class_id),
                    'class_name': CLASS_NAMES[class_id],
                    'confidence': float(confidence),
                    'bbox': [x1, y1, x2, y2]
                })
    
    return detections


def parse_method_3(output, img_w, img_h):
    """Method 3: Using OpenCV DNN NMSBoxes"""
    detections = []
    out_np = np.array(output)
    
    if len(out_np.shape) == 3:
        out_np = out_np[0]
    
    if out_np.shape[0] < out_np.shape[1]:
        out_np = out_np.T
    
    boxes = []
    confidences = []
    class_ids = []
    
    for detection in out_np:
        if len(detection) < 4 + len(CLASS_NAMES):
            continue
        
        class_scores = detection[4:4 + len(CLASS_NAMES)]
        class_id = np.argmax(class_scores)
        confidence = class_scores[class_id]
        
        if confidence > CONFIDENCE_THRESHOLD:
            x_center = detection[0]
            y_center = detection[1]
            width = detection[2]
            height = detection[3]
            
            # Scale to original image
            scale_x = img_w / INPUT_SIZE
            scale_y = img_h / INPUT_SIZE
            
            x_center *= scale_x
            y_center *= scale_y
            width *= scale_x
            height *= scale_y
            
            x1 = int(x_center - width / 2)
            y1 = int(y_center - height / 2)
            
            boxes.append([x1, y1, int(width), int(height)])
            confidences.append(float(confidence))
            class_ids.append(int(class_id))
    
    # Apply NMS using OpenCV
    if len(boxes) > 0:
        indices = cv2.dnn.NMSBoxes(boxes, confidences, CONFIDENCE_THRESHOLD, 0.45)
        
        if len(indices) > 0:
            for i in indices.flatten():
                box = boxes[i]
                x1, y1, w, h = box
                x2 = x1 + w
                y2 = y1 + h
                
                x1 = max(0, min(x1, img_w))
                y1 = max(0, min(y1, img_h))
                x2 = max(0, min(x2, img_w))
                y2 = max(0, min(y2, img_h))
                
                if x2 > x1 and y2 > y1:
                    detections.append({
                        'class_id': class_ids[i],
                        'class_name': CLASS_NAMES[class_ids[i]],
                        'confidence': confidences[i],
                        'bbox': [x1, y1, x2, y2]
                    })
    
    return detections


def main():
    print("=" * 60)
    print("🔍 DEBUG MODE - Testing Multiple Parse Methods")
    print("=" * 60)
    print()
    
    net = load_model()
    if net is None:
        return
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot open camera!")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"✓ Camera: {actual_width}x{actual_height}")
    print()
    print("CONTROLS:")
    print("  1 - Method 1 (normalized coords)")
    print("  2 - Method 2 (pixel coords)")
    print("  3 - Method 3 (OpenCV NMS)")
    print("  Q - Quit")
    print("=" * 60)
    print()
    
    current_method = 1
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        
        # Preprocess
        img = cv2.resize(frame, (INPUT_SIZE, INPUT_SIZE))
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Create NCNN Mat
        mat_in = ncnn.Mat.from_pixels(
            img_rgb,
            ncnn.Mat.PixelType.PIXEL_RGB,
            INPUT_SIZE,
            INPUT_SIZE
        )
        
        mat_in.substract_mean_normalize([0, 0, 0], [1/255.0, 1/255.0, 1/255.0])
        
        # Inference
        with net.create_extractor() as ex:
            ex.input("in0", mat_in)
            ret, mat_out = ex.extract("out0")
        
        # Parse với method được chọn
        if current_method == 1:
            detections = parse_method_1(mat_out, actual_width, actual_height)
        elif current_method == 2:
            detections = parse_method_2(mat_out, actual_width, actual_height)
        else:
            detections = parse_method_3(mat_out, actual_width, actual_height)
        
        # Draw
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            color = (0, 255, 0)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            label = f"{det['class_name']}: {det['confidence']:.2f}"
            cv2.putText(frame, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Info
        cv2.rectangle(frame, (10, 10), (400, 100), (0, 0, 0), -1)
        cv2.putText(frame, f"Method: {current_method}", (20, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, f"Detections: {len(detections)}", (20, 65),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Press 1/2/3 to change method", (20, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        
        cv2.imshow('Debug Mode', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('Q'):
            break
        elif key == ord('1'):
            current_method = 1
            print(f"→ Switched to Method 1")
        elif key == ord('2'):
            current_method = 2
            print(f"→ Switched to Method 2")
        elif key == ord('3'):
            current_method = 3
            print(f"→ Switched to Method 3")
    
    cap.release()
    cv2.destroyAllWindows()
    print("Done!")


if __name__ == "__main__":
    main()

