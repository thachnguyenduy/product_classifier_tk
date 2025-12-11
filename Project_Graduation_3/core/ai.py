import cv2
import numpy as np
import os
import time
import re

try:
    import ncnn
    NCNN_AVAILABLE = True
except ImportError:
    print("[ERROR] NCNN library not found. Please install: sudo apt-get install python3-ncnn")
    NCNN_AVAILABLE = False

import config


class AIEngine:
    def __init__(self):
        self.model_loaded = False
        self.net = None
        self.input_blob_name = None
        self.output_blob_names = []
        self.input_size = config.INPUT_SIZE
        
        self.conf_threshold = config.CONFIDENCE_THRESHOLD
        self.nms_threshold = config.NMS_THRESHOLD
        self.class_names = config.CLASS_NAMES
        self.num_classes = len(self.class_names)
        
        if NCNN_AVAILABLE:
            self._load_model()
        else:
            print("[ERROR] Cannot initialize AI engine without NCNN")
    
    def _load_model(self):
        try:
            param_path = os.path.join(config.MODEL_PATH, config.MODEL_PARAM)
            bin_path = os.path.join(config.MODEL_PATH, config.MODEL_BIN)
            
            if not os.path.exists(param_path):
                print(f"[ERROR] Model param file not found: {param_path}")
                return
            
            if not os.path.exists(bin_path):
                print(f"[ERROR] Model bin file not found: {bin_path}")
                return
            
            self._detect_blob_names(param_path)
            self._detect_input_size(param_path)
            
            self.net = ncnn.Net()
            self.net.opt.use_vulkan_compute = False
            self.net.opt.num_threads = 4
            
            ret_param = self.net.load_param(param_path)
            if ret_param != 0:
                print(f"[ERROR] Failed to load param file (code={ret_param})")
                return
            
            ret_bin = self.net.load_model(bin_path)
            if ret_bin != 0:
                print(f"[ERROR] Failed to load bin file (code={ret_bin})")
                return
            
            self.model_loaded = True
            print(f"[AI] Model loaded successfully")
            print(f"[AI] Input blob: {self.input_blob_name}, Output blobs: {self.output_blob_names}")
            print(f"[AI] Input size: {self.input_size}x{self.input_size}")
            
        except Exception as e:
            print(f"[ERROR] Exception loading model: {e}")
            import traceback
            traceback.print_exc()
    
    def _detect_blob_names(self, param_path):
        with open(param_path, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            if line.startswith('Input'):
                parts = line.split()
                if len(parts) >= 3:
                    self.input_blob_name = parts[2]
                    break
        
        if not self.input_blob_name:
            self.input_blob_name = 'in0'
        
        for line in lines:
            if 'out0' in line or 'output0' in line:
                if 'out0' in line:
                    self.output_blob_names.append('out0')
                if 'output0' in line:
                    self.output_blob_names.append('output0')
                break
        
        if not self.output_blob_names:
            self.output_blob_names = ['out0']
        
        if 'output1' in ''.join(lines):
            self.output_blob_names.append('output1')
    
    def _detect_input_size(self, param_path):
        with open(param_path, 'r') as f:
            content = f.read()
        
        match = re.search(r'Input.*?(\d+)\s+(\d+)', content)
        if match:
            w, h = int(match.group(1)), int(match.group(2))
            if w == h:
                self.input_size = w
                return
        
        match = re.search(r'0=(\d+).*?1=(\d+)', content)
        if match:
            w, h = int(match.group(1)), int(match.group(2))
            if w == h and w > 0:
                self.input_size = w
    
    def predict(self, frame):
        if not self.model_loaded:
            return {
                "detections": [],
                "annotated_image": frame.copy(),
                "result": "N",
                "reason": "Model not loaded",
                "processing_time_ms": 0
            }
        
        start_time = time.time()
        orig_h, orig_w = frame.shape[:2]
        
        mat_in = self._preprocess(frame)
        detections_raw = self._run_inference(mat_in, orig_w, orig_h)
        detections_filtered = self._apply_nms(detections_raw)
        
        result_dict = self._apply_sorting_logic(detections_filtered)
        annotated = self._draw_detections(frame.copy(), detections_filtered)
        
        result_dict['annotated_image'] = annotated
        result_dict['detections'] = [
            {"cls": d['class_id'], "conf": d['confidence'], "box": d['bbox']}
            for d in detections_filtered
        ]
        result_dict['processing_time_ms'] = (time.time() - start_time) * 1000
        
        return result_dict
    
    def _preprocess(self, frame):
        resized = cv2.resize(frame, (self.input_size, self.input_size))
        mat_in = ncnn.Mat.from_pixels(
            resized,
            ncnn.Mat.PixelType.PIXEL_BGR,
            self.input_size,
            self.input_size
        )
        mean_vals = [0, 0, 0]
        norm_vals = [1/255.0, 1/255.0, 1/255.0]
        mat_in.substract_mean_normalize(mean_vals, norm_vals)
        return mat_in
    
    def _run_inference(self, mat_in, orig_w, orig_h):
        try:
            if config.DEBUG_MODE:
                print(f"[AI] Inference: Starting...")
            
            ex = self.net.create_extractor()
            ex.set_vulkan_compute(False)
            
            if config.DEBUG_MODE:
                print(f"[AI] Inference: Input blob='{self.input_blob_name}'")
            
            ret_input = ex.input(self.input_blob_name, mat_in)
            if ret_input != 0:
                print(f"[ERROR] Input failed (code={ret_input})")
                return []
            
            if config.DEBUG_MODE:
                print(f"[AI] Inference: Input set successfully")
            
            all_detections = []
            
            for output_name in self.output_blob_names:
                if config.DEBUG_MODE:
                    print(f"[AI] Inference: Extracting output '{output_name}'...")
                
                ret, mat_out = ex.extract(output_name)
                if ret != 0:
                    if config.DEBUG_MODE:
                        print(f"[AI] Inference: Extract '{output_name}' failed (code={ret})")
                    continue
                
                if config.DEBUG_MODE:
                    print(f"[AI] Inference: Extract '{output_name}' successful")
                
                detections = self._decode_yolo_output(mat_out, orig_w, orig_h)
                all_detections.extend(detections)
            
            if not all_detections and self.output_blob_names:
                if config.DEBUG_MODE:
                    print(f"[AI] Inference: No detections, trying fallback...")
                ret, mat_out = ex.extract(self.output_blob_names[0])
                if ret == 0:
                    all_detections = self._decode_yolo_output(mat_out, orig_w, orig_h)
            
            if config.DEBUG_MODE:
                print(f"[AI] Inference: Total detections: {len(all_detections)}")
            
            return all_detections
            
        except Exception as e:
            print(f"[ERROR] Inference failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _decode_yolo_output(self, output, img_w, img_h):
        detections = []
        
        try:
            out_np = np.array(output)
            
            if config.DEBUG_MODE:
                print(f"[AI] Decode: Raw output shape={out_np.shape}, dtype={out_np.dtype}")
            
            if len(out_np.shape) == 3:
                out_np = out_np[0]
                if config.DEBUG_MODE:
                    print(f"[AI] Decode: Removed batch dim, shape={out_np.shape}")
            
            if len(out_np.shape) == 2:
                if out_np.shape[0] < out_np.shape[1]:
                    out_np = out_np.T
                    if config.DEBUG_MODE:
                        print(f"[AI] Decode: Transposed, shape={out_np.shape}")
            
            if len(out_np.shape) != 2:
                if config.DEBUG_MODE:
                    print(f"[AI] Decode: ERROR - Unexpected shape {out_np.shape}")
                return []
            
            num_anchors, num_features = out_np.shape
            
            if config.DEBUG_MODE:
                print(f"[AI] Decode: Processing {num_anchors} anchors, {num_features} features")
                print(f"[AI] Decode: Expected {4 + self.num_classes} features, got {num_features}")
            
            if num_features < 4 + self.num_classes:
                if config.DEBUG_MODE:
                    print(f"[AI] Decode: ERROR - Not enough features")
                return []
            
            scale_x = img_w / self.input_size
            scale_y = img_h / self.input_size
            
            if config.DEBUG_MODE:
                print(f"[AI] Decode: Scale factors: x={scale_x:.3f}, y={scale_y:.3f}")
                print(f"[AI] Decode: Confidence threshold: {self.conf_threshold}")
            
            valid_count = 0
            filtered_count = 0
            
            for i in range(min(num_anchors, 1000)):  # Limit to first 1000 for performance
                row = out_np[i]
                
                if len(row) < 4 + self.num_classes:
                    continue
                
                x_center = float(row[0])
                y_center = float(row[1])
                width = float(row[2])
                height = float(row[3])
                
                if width <= 0 or height <= 0:
                    continue
                
                class_scores_raw = row[4:4+self.num_classes]
                
                if len(class_scores_raw) < self.num_classes:
                    continue
                
                class_scores = class_scores_raw.copy()
                max_val = np.max(class_scores)
                min_val = np.min(class_scores)
                
                if config.DEBUG_MODE and valid_count < 3:
                    print(f"[AI] Decode: Sample #{valid_count}: scores range=[{min_val:.3f}, {max_val:.3f}]")
                
                if max_val > 5.0 or min_val < -5.0:
                    class_scores = 1.0 / (1.0 + np.exp(-np.clip(class_scores, -500, 500)))
                    if config.DEBUG_MODE and valid_count < 3:
                        print(f"[AI] Decode: Applied sigmoid (was logits)")
                
                class_id = int(np.argmax(class_scores))
                confidence = float(np.clip(class_scores[class_id], 0.0, 1.0))
                
                if config.DEBUG_MODE and valid_count < 3:
                    print(f"[AI] Decode: Best class: {self.class_names[class_id]} (id={class_id}), conf={confidence:.3f}")
                
                if confidence < self.conf_threshold:
                    filtered_count += 1
                    continue
                
                x_center_scaled = x_center * scale_x
                y_center_scaled = y_center * scale_y
                width_scaled = width * scale_x
                height_scaled = height * scale_y
                
                x1 = int(x_center_scaled - width_scaled / 2)
                y1 = int(y_center_scaled - height_scaled / 2)
                x2 = int(x_center_scaled + width_scaled / 2)
                y2 = int(y_center_scaled + height_scaled / 2)
                
                x1 = max(0, min(x1, img_w - 1))
                y1 = max(0, min(y1, img_h - 1))
                x2 = max(1, min(x2, img_w))
                y2 = max(1, min(y2, img_h))
                
                if x2 > x1 and y2 > y1 and (x2 - x1) >= 5 and (y2 - y1) >= 5:
                    detections.append({
                        'class_id': class_id,
                        'class_name': self.class_names[class_id],
                        'confidence': confidence,
                        'bbox': [x1, y1, x2, y2]
                    })
                    
                    if config.DEBUG_MODE:
                        print(f"[AI] Decode: ✅ Detection: {self.class_names[class_id]} ({confidence:.2f}) at [{x1}, {y1}, {x2}, {y2}]")
                
                valid_count += 1
            
            if config.DEBUG_MODE:
                print(f"[AI] Decode: Total valid: {valid_count}, Filtered by threshold: {filtered_count}, Final detections: {len(detections)}")
        
        except Exception as e:
            print(f"[ERROR] Decode failed: {e}")
            import traceback
            traceback.print_exc()
        
        return detections
    
    def _apply_nms(self, detections):
        if len(detections) == 0:
            return []
        
        boxes = []
        confidences = []
        class_ids = []
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            boxes.append([x1, y1, x2 - x1, y2 - y1])
            confidences.append(det['confidence'])
            class_ids.append(det['class_id'])
        
        indices = cv2.dnn.NMSBoxes(
            boxes,
            confidences,
            self.conf_threshold,
            self.nms_threshold
        )
        
        filtered = []
        if len(indices) > 0:
            for i in indices.flatten():
                filtered.append(detections[i])
        
        return filtered
    
    def _apply_sorting_logic(self, detections):
        result = {
            'result': 'O',
            'reason': 'Sản phẩm đạt chuẩn',
            'has_defects': False,
            'defects_found': [],
            'has_cap': False,
            'has_filled': False,
            'has_label': False
        }
        
        for det in detections:
            class_id = det['class_id']
            
            if class_id < 4:
                result['has_defects'] = True
                result['defects_found'].append(self.class_names[class_id])
            elif class_id == 4:
                result['has_cap'] = True
            elif class_id == 6:
                result['has_filled'] = True
            elif class_id == 7:
                result['has_label'] = True
        
        if result['has_defects']:
            result['result'] = 'N'
            result['reason'] = f"Phát hiện lỗi: {', '.join(result['defects_found'])}"
        elif not result['has_cap']:
            result['result'] = 'N'
            result['reason'] = "Thiếu nắp"
        elif not result['has_filled']:
            result['result'] = 'N'
            result['reason'] = "Thiếu chất lỏng"
        elif not result['has_label']:
            result['result'] = 'N'
            result['reason'] = "Thiếu nhãn"
        
        return result
    
    def _draw_detections(self, frame, detections):
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            class_name = det['class_name']
            confidence = det['confidence']
            class_id = det['class_id']
            
            if class_id < 4:
                color = (0, 0, 255)
            else:
                color = (0, 255, 0)
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            label = f"{class_name}: {confidence:.2f}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame, (x1, y1 - th - 4), (x1 + tw, y1), color, -1)
            cv2.putText(frame, label, (x1, y1 - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
