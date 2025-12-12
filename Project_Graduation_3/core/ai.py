# ============================================
# AI ENGINE - NCNN OPTIMIZED for Raspberry Pi 5
# ============================================
"""
AI Engine tối ưu cho Raspberry Pi 5 sử dụng NCNN

PERFORMANCE OPTIMIZATIONS:
- NCNN inference (5-10x faster than YOLO PyTorch)
- Efficient tracking with spatial indexing
- Reduced memory allocations
- Optimized detection grouping

CLASSIFICATION RULES (EXACT):
1. NG if ANY defect class detected
2. OK if ALL good classes (cap + label + filled) detected AND NO defects
3. "coca" class is ONLY for identity, NOT for classification
"""

import cv2
import numpy as np
import time
import os
import re
import config


# Import NCNN
try:
    import ncnn
    NCNN_AVAILABLE = True
except ImportError:
    print("[ERROR] NCNN not available. Install: pip3 install ncnn")
    NCNN_AVAILABLE = False


class TrackedObject:
    """Tracked bottle object"""
    __slots__ = ['object_id', 'x_center', 'y_center', 'detected_classes', 
                 'bbox', 'last_seen', 'crossed', 'classification_result', 
                 'classification_reason']
    
    def __init__(self, object_id, x_center, y_center):
        self.object_id = object_id
        self.x_center = x_center
        self.y_center = y_center
        self.detected_classes = set()
        self.bbox = None
        self.last_seen = time.time()
        self.crossed = False
        self.classification_result = None
        self.classification_reason = ""
    
    def update_position(self, x_center, y_center, bbox=None):
        """Update position"""
        self.x_center = x_center
        self.y_center = y_center
        if bbox is not None:
            self.bbox = bbox
        self.last_seen = time.time()
    
    def add_detected_class(self, class_name):
        """Add detected class"""
        self.detected_classes.add(class_name)
    
    def finalize_classification(self):
        """
        Finalize classification at line crossing
        
        Rules (STRICT):
        - If ANY defect → NG
        - If ALL good classes present AND NO defects → OK
        - Otherwise → NG
        """
        # Check defects
        defect_classes = {'Cap-Defect', 'Filling-Defect', 'Label-Defect', 'Wrong-Product'}
        detected_defects = self.detected_classes & defect_classes
        
        if detected_defects:
            self.classification_result = 'NG'
            self.classification_reason = f"Defect: {', '.join(detected_defects)}"
            return
        
        # Check good classes
        required_good = {'cap', 'label', 'filled'}
        has_all_good = required_good.issubset(self.detected_classes)
        
        if has_all_good:
            self.classification_result = 'OK'
            self.classification_reason = "All components OK"
        else:
            missing = required_good - self.detected_classes
            self.classification_result = 'NG'
            self.classification_reason = f"Missing: {', '.join(missing)}"


class AIEngine:
    """
    NCNN-based AI Engine optimized for Raspberry Pi 5
    
    Performance features:
    - NCNN inference (much faster than PyTorch)
    - Efficient object tracking
    - Reduced memory allocations
    - Optimized detection processing
    """
    
    def __init__(self):
        print("[AI] Initializing NCNN model for Raspberry Pi 5...")
        
        if not NCNN_AVAILABLE:
            raise RuntimeError("NCNN not available")
        
        # Model paths
        self.model_path = config.MODEL_PATH_NCNN
        self.param_file = os.path.join(self.model_path, config.MODEL_PARAM)
        self.bin_file = os.path.join(self.model_path, config.MODEL_BIN)
        
        # Configuration
        self.input_size = config.INPUT_SIZE
        self.conf_threshold = config.CONFIDENCE_THRESHOLD
        self.nms_threshold = config.NMS_THRESHOLD
        self.class_names = config.CLASS_NAMES
        self.num_classes = len(self.class_names)
        
        # NCNN network
        self.net = None
        self.input_blob_name = "in0"
        self.output_blob_name = "out0"
        
        # Load model
        self._load_ncnn_model()
        
        # Tracking
        self.tracked_objects = {}
        self.next_object_id = 0
        self.max_distance = 100
        self.object_timeout = 3.0
        
        # Virtual line
        self.virtual_line_x = config.VIRTUAL_LINE_X
        
        print(f"[AI] NCNN model loaded successfully")
        print(f"[AI] Input size: {self.input_size}x{self.input_size}")
        print(f"[AI] Classes: {self.num_classes}")
    
    def _load_ncnn_model(self):
        """Load NCNN model"""
        try:
            # Check files exist
            if not os.path.exists(self.param_file):
                raise FileNotFoundError(f"Param file not found: {self.param_file}")
            if not os.path.exists(self.bin_file):
                raise FileNotFoundError(f"Bin file not found: {self.bin_file}")
            
            # Auto-detect input blob name
            self._detect_blob_names()
            
            # Create NCNN network
            self.net = ncnn.Net()
            self.net.opt.use_vulkan_compute = False  # Disable Vulkan for stability
            self.net.opt.num_threads = 4  # Use 4 threads on Pi 5
            
            # Load model
            ret_param = self.net.load_param(self.param_file)
            if ret_param != 0:
                raise RuntimeError(f"Failed to load param file (code={ret_param})")
            
            ret_bin = self.net.load_model(self.bin_file)
            if ret_bin != 0:
                raise RuntimeError(f"Failed to load bin file (code={ret_bin})")
            
            print(f"[AI] NCNN loaded: {self.input_blob_name} -> {self.output_blob_name}")
            
        except Exception as e:
            print(f"[ERROR] Failed to load NCNN model: {e}")
            raise
    
    def _detect_blob_names(self):
        """Auto-detect blob names from param file"""
        with open(self.param_file, 'r') as f:
            lines = f.readlines()
        
        # Find input blob
        for line in lines:
            if line.startswith('Input'):
                parts = line.split()
                if len(parts) >= 3:
                    self.input_blob_name = parts[2]
                    break
        
        # Find output blob
        for line in lines:
            if 'out0' in line or 'output0' in line:
                if 'out0' in line:
                    self.output_blob_name = 'out0'
                elif 'output0' in line:
                    self.output_blob_name = 'output0'
                break
    
    def predict_and_track(self, frame):
        """
        Run NCNN detection and tracking (OPTIMIZED)
        
        Returns:
            dict with detections, tracked_objects, crossed_objects
        """
        start_time = time.time()
        
        # Preprocess
        mat_in = self._preprocess(frame)
        
        # Run inference
        detections = self._run_inference(mat_in, frame.shape[1], frame.shape[0])
        
        # Update tracking
        crossed_objects = self._update_tracking(detections)
        
        if config.DEBUG_MODE:
            inference_time = (time.time() - start_time) * 1000
            print(f"[AI] Inference: {inference_time:.1f}ms | Detections: {len(detections)}")
        
        return {
            'detections': detections,
            'tracked_objects': self.tracked_objects,
            'crossed_objects': crossed_objects
        }
    
    def _preprocess(self, frame):
        """Preprocess frame for NCNN (OPTIMIZED)"""
        # Resize once
        resized = cv2.resize(frame, (self.input_size, self.input_size), 
                            interpolation=cv2.INTER_LINEAR)
        
        # Convert to NCNN Mat (optimized path)
        mat_in = ncnn.Mat.from_pixels(
            resized,
            ncnn.Mat.PixelType.PIXEL_BGR,
            self.input_size,
            self.input_size
        )
        
        # Normalize (faster than substract_mean_normalize for constants)
        mean_vals = [0, 0, 0]
        norm_vals = [1.0/255.0, 1.0/255.0, 1.0/255.0]
        mat_in.substract_mean_normalize(mean_vals, norm_vals)
        
        return mat_in
    
    def _run_inference(self, mat_in, orig_w, orig_h):
        """Run NCNN inference (OPTIMIZED)"""
        try:
            # Create extractor
            ex = self.net.create_extractor()
            ex.set_vulkan_compute(False)
            
            # Input
            ret_input = ex.input(self.input_blob_name, mat_in)
            if ret_input != 0:
                print(f"[ERROR] Input failed (code={ret_input})")
                return []
            
            # Extract output
            ret, mat_out = ex.extract(self.output_blob_name)
            if ret != 0:
                print(f"[ERROR] Extract failed (code={ret})")
                return []
            
            # Decode detections
            detections = self._decode_yolo_output(mat_out, orig_w, orig_h)
            
            # Apply NMS
            detections = self._apply_nms(detections)
            
            return detections
            
        except Exception as e:
            print(f"[ERROR] Inference failed: {e}")
            return []
    
    def _decode_yolo_output(self, output, img_w, img_h):
        """
        Decode YOLO NCNN output (CHUẨN YOLOv8)
        
        Output format từ NCNN:
        - Shape: (8400, 12) hoặc (1, 8400, 12) hoặc (12, 8400)
        - 8400 = số anchors (80x80 + 40x40 + 20x20 grids)
        - 12 = 4 bbox coords + 8 class scores
        - bbox: [x_center, y_center, width, height] - đã normalize về input_size
        - class scores: đã qua sigmoid (0-1)
        """
        detections = []
        
        try:
            # Convert to numpy
            out_np = np.array(output)
            
            if config.DEBUG_MODE:
                print(f"[AI] Raw output shape: {out_np.shape}")
            
            # Handle different shapes
            if len(out_np.shape) == 3:
                # Shape: (1, 8400, 12) hoặc (1, 12, 8400)
                out_np = out_np.squeeze(0)  # Remove batch dimension
            
            if len(out_np.shape) == 2:
                # Check if transposed (12, 8400) → (8400, 12)
                if out_np.shape[0] == 4 + self.num_classes and out_np.shape[1] > 1000:
                    out_np = out_np.T
                    if config.DEBUG_MODE:
                        print(f"[AI] Transposed to: {out_np.shape}")
            
            if len(out_np.shape) != 2:
                print(f"[ERROR] Unexpected output shape: {out_np.shape}")
                return []
            
            num_anchors, num_features = out_np.shape
            
            if config.DEBUG_MODE:
                print(f"[AI] Anchors: {num_anchors}, Features: {num_features}")
            
            # Verify feature count
            expected_features = 4 + self.num_classes
            if num_features != expected_features:
                print(f"[ERROR] Feature mismatch: got {num_features}, expected {expected_features}")
                return []
            
            # Scale factors (from input_size to original image size)
            scale_x = img_w / self.input_size
            scale_y = img_h / self.input_size
            
            # Split bbox and class scores
            # YOLOv8 format: [x_center, y_center, width, height, class_0, ..., class_7]
            bbox_coords = out_np[:, 0:4]  # (8400, 4)
            class_scores = out_np[:, 4:]   # (8400, 8)
            
            # Class scores từ NCNN đã qua sigmoid (0-1), không cần sigmoid lại
            # Nếu có giá trị > 1 hoặc < 0, có lỗi
            if config.DEBUG_MODE:
                print(f"[AI] Score range: [{np.min(class_scores):.3f}, {np.max(class_scores):.3f}]")
            
            # Nếu scores chưa qua sigmoid (check if có giá trị lớn)
            if np.max(class_scores) > 2.0 or np.min(class_scores) < -1.0:
                if config.DEBUG_MODE:
                    print(f"[AI] Applying sigmoid to scores")
                class_scores = 1.0 / (1.0 + np.exp(-np.clip(class_scores, -50, 50)))
            
            # Get best class for each anchor (vectorized)
            max_scores = np.max(class_scores, axis=1)  # (8400,)
            class_ids = np.argmax(class_scores, axis=1)  # (8400,)
            
            # Filter by confidence threshold (vectorized)
            valid_mask = max_scores >= self.conf_threshold
            valid_indices = np.where(valid_mask)[0]
            
            if config.DEBUG_MODE:
                print(f"[AI] Valid detections: {len(valid_indices)} / {num_anchors}")
            
            # Process valid detections
            for idx in valid_indices:
                # Get bbox (already in pixel coordinates relative to input_size)
                x_center = float(bbox_coords[idx, 0])
                y_center = float(bbox_coords[idx, 1])
                width = float(bbox_coords[idx, 2])
                height = float(bbox_coords[idx, 3])
                
                # Skip invalid boxes
                if width <= 0 or height <= 0:
                    continue
                
                # Scale to original image size
                x_center_scaled = x_center * scale_x
                y_center_scaled = y_center * scale_y
                width_scaled = width * scale_x
                height_scaled = height * scale_y
                
                # Convert to x1, y1, x2, y2
                x1 = int(x_center_scaled - width_scaled / 2)
                y1 = int(y_center_scaled - height_scaled / 2)
                x2 = int(x_center_scaled + width_scaled / 2)
                y2 = int(y_center_scaled + height_scaled / 2)
                
                # Clip to image bounds
                x1 = max(0, min(x1, img_w - 1))
                y1 = max(0, min(y1, img_h - 1))
                x2 = max(x1 + 1, min(x2, img_w))
                y2 = max(y1 + 1, min(y2, img_h))
                
                # Skip too small boxes
                if (x2 - x1) < 10 or (y2 - y1) < 10:
                    continue
                
                # Get class info
                class_id = int(class_ids[idx])
                confidence = float(max_scores[idx])
                
                # Verify class_id is valid
                if class_id >= len(self.class_names):
                    continue
                
                class_name = self.class_names[class_id]
                
                detections.append({
                    'class_id': class_id,
                    'class_name': class_name,
                    'confidence': confidence,
                    'bbox': [x1, y1, x2, y2]
                })
                
                if config.DEBUG_MODE and len(detections) <= 5:
                    print(f"[AI] Detection: {class_name} ({confidence:.2f}) at [{x1},{y1},{x2},{y2}]")
            
            if config.DEBUG_MODE:
                print(f"[AI] Total detections after decoding: {len(detections)}")
        
        except Exception as e:
            print(f"[ERROR] Decode failed: {e}")
            import traceback
            traceback.print_exc()
        
        return detections
    
    def _apply_nms(self, detections):
        """Apply NMS (OPTIMIZED)"""
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
        
        # OpenCV NMS (very fast)
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
    
    def _update_tracking(self, detections):
        """Update tracking (OPTIMIZED)"""
        current_time = time.time()
        crossed_objects = []
        
        # Clean old objects
        self.tracked_objects = {
            obj_id: obj for obj_id, obj in self.tracked_objects.items()
            if current_time - obj.last_seen < self.object_timeout
        }
        
        # Group detections
        detection_groups = self._group_detections_by_position(detections)
        
        # Match to existing objects
        matched_detections = set()
        
        for obj_id, tracked_obj in list(self.tracked_objects.items()):
            if tracked_obj.crossed:
                continue
            
            # Find closest group (optimized distance calculation)
            best_match = None
            min_distance = self.max_distance
            
            for i, group in enumerate(detection_groups):
                if i in matched_detections:
                    continue
                
                # Fast distance calculation
                dx = group['center'][0] - tracked_obj.x_center
                dy = group['center'][1] - tracked_obj.y_center
                distance = dx*dx + dy*dy  # Skip sqrt for comparison
                
                if distance < min_distance * min_distance:
                    min_distance = distance ** 0.5
                    best_match = i
            
            if best_match is not None:
                matched_detections.add(best_match)
                group = detection_groups[best_match]
                
                prev_x = tracked_obj.x_center
                
                # Update
                tracked_obj.update_position(
                    group['center'][0],
                    group['center'][1],
                    group['bbox']
                )
                
                # Add classes
                for det in group['detections']:
                    tracked_obj.add_detected_class(det['class_name'])
                
                # Check crossing
                if not tracked_obj.crossed:
                    if prev_x > self.virtual_line_x and tracked_obj.x_center <= self.virtual_line_x:
                        tracked_obj.crossed = True
                        tracked_obj.finalize_classification()
                        crossed_objects.append(tracked_obj)
                        
                        if config.DEBUG_MODE:
                            print(f"[AI] Object #{obj_id} CROSSED | {tracked_obj.classification_result}")
        
        # Create new objects
        for i, group in enumerate(detection_groups):
            if i not in matched_detections:
                if group['center'][0] > self.virtual_line_x:
                    new_obj = TrackedObject(
                        self.next_object_id,
                        group['center'][0],
                        group['center'][1]
                    )
                    new_obj.bbox = group['bbox']
                    
                    for det in group['detections']:
                        new_obj.add_detected_class(det['class_name'])
                    
                    self.tracked_objects[self.next_object_id] = new_obj
                    self.next_object_id += 1
        
        return crossed_objects
    
    def _group_detections_by_position(self, detections):
        """Group nearby detections (OPTIMIZED)"""
        if len(detections) == 0:
            return []
        
        groups = []
        used = set()
        
        for i, det1 in enumerate(detections):
            if i in used:
                continue
            
            x1, y1, x2, y2 = det1['bbox']
            cx1 = (x1 + x2) * 0.5
            cy1 = (y1 + y2) * 0.5
            
            group_detections = [det1]
            group_boxes = [[x1, y1, x2, y2]]
            used.add(i)
            
            # Find nearby
            for j, det2 in enumerate(detections):
                if j in used:
                    continue
                
                x1_2, y1_2, x2_2, y2_2 = det2['bbox']
                cx2 = (x1_2 + x2_2) * 0.5
                cy2 = (y1_2 + y2_2) * 0.5
                
                # Fast distance
                dx = cx1 - cx2
                dy = cy1 - cy2
                if dx*dx + dy*dy < 10000:  # 100^2
                    group_detections.append(det2)
                    group_boxes.append([x1_2, y1_2, x2_2, y2_2])
                    used.add(j)
            
            # Compute group bbox (vectorized)
            boxes_np = np.array(group_boxes)
            group_bbox = [
                int(np.min(boxes_np[:, 0])),
                int(np.min(boxes_np[:, 1])),
                int(np.max(boxes_np[:, 2])),
                int(np.max(boxes_np[:, 3]))
            ]
            
            group_center = [
                (group_bbox[0] + group_bbox[2]) * 0.5,
                (group_bbox[1] + group_bbox[3]) * 0.5
            ]
            
            groups.append({
                'detections': group_detections,
                'bbox': group_bbox,
                'center': group_center
            })
        
        return groups
    
    def draw_tracking(self, frame, tracked_objects_dict):
        """Draw tracking (OPTIMIZED - minimal operations)"""
        for obj_id, obj in tracked_objects_dict.items():
            if obj.bbox is None:
                continue
            
            x1, y1, x2, y2 = obj.bbox
            
            # Color
            if obj.crossed:
                color = (0, 255, 0) if obj.classification_result == 'OK' else (0, 0, 255)
            else:
                color = (255, 255, 0)
            
            # Draw box (single call)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw ID (minimal text)
            cv2.putText(frame, f"#{obj_id}", (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            # Draw result if crossed
            if obj.crossed and obj.classification_result:
                cv2.putText(frame, obj.classification_result, (x1, y2 + 15),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return frame
