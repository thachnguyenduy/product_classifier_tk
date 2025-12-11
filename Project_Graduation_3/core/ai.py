# ============================================
# AI ENGINE - NCNN with NMS
# ============================================

import cv2
import numpy as np
import os
import time

# Try to import ncnn, with graceful fallback
try:
    import ncnn
    NCNN_AVAILABLE = True
except ImportError:
    print("[WARNING] NCNN library not found. Using dummy fallback for UI testing.")
    NCNN_AVAILABLE = False

import config


class AIEngine:
    """
    AI Engine using NCNN for object detection with NMS
    """
    
    def __init__(self):
        self.model_loaded = False
        self.net = None
        
        # Load config
        self.input_size = config.INPUT_SIZE
        self.conf_threshold = config.CONFIDENCE_THRESHOLD
        self.nms_threshold = config.NMS_THRESHOLD
        self.class_names = config.CLASS_NAMES
        self.defect_classes = config.DEFECT_CLASSES
        self.required_components = config.REQUIRED_COMPONENTS
        
        if NCNN_AVAILABLE:
            self._load_model()
        else:
            print("[AI] Running in DUMMY mode (no NCNN)")
    
    def _load_model(self):
        """
        Load NCNN model from .param and .bin files
        """
        try:
            param_path = os.path.join(config.MODEL_PATH, config.MODEL_PARAM)
            bin_path = os.path.join(config.MODEL_PATH, config.MODEL_BIN)
            
            print(f"[AI] Loading model from: {config.MODEL_PATH}")
            print(f"[AI] Param: {config.MODEL_PARAM}")
            print(f"[AI] Bin: {config.MODEL_BIN}")
            
            if not os.path.exists(param_path):
                print(f"[ERROR] Model param file not found: {param_path}")
                return
            
            if not os.path.exists(bin_path):
                print(f"[ERROR] Model bin file not found: {bin_path}")
                return
            
            print(f"[AI] Files found:")
            print(f"  - {param_path} ({os.path.getsize(param_path) / 1024:.1f} KB)")
            print(f"  - {bin_path} ({os.path.getsize(bin_path) / 1024 / 1024:.1f} MB)")
            
            # Initialize NCNN network
            self.net = ncnn.Net()
            
            # Configure (disable Vulkan for stability)
            self.net.opt.use_vulkan_compute = False  # Use CPU for stability
            self.net.opt.num_threads = 4  # Use 4 threads
            
            print(f"[AI] NCNN configured (CPU mode, 4 threads)")
            
            # Load model
            print(f"[AI] Loading param file...")
            ret_param = self.net.load_param(param_path)
            
            if ret_param != 0:
                print(f"[ERROR] Failed to load param file (code={ret_param})")
                return
            
            print(f"[AI] Loading bin file...")
            ret_bin = self.net.load_model(bin_path)
            
            if ret_bin != 0:
                print(f"[ERROR] Failed to load bin file (code={ret_bin})")
                return
            
            self.model_loaded = True
            print(f"[AI] ✅ NCNN model loaded successfully!")
            print(f"[AI] Input size: {self.input_size}x{self.input_size}")
            print(f"[AI] Confidence threshold: {self.conf_threshold}")
            print(f"[AI] NMS threshold: {self.nms_threshold}")
            print(f"[AI] Input blob: 'in0', Output blob: 'out0'")
                
        except Exception as e:
            print(f"[ERROR] Exception loading NCNN model: {e}")
            import traceback
            traceback.print_exc()
    
    def predict(self, frame):
        """
        Run detection on a single frame
        
        Args:
            frame: Input image (numpy array)
            
        Returns:
            dict with:
                - result: 'O' (OK) or 'N' (NG)
                - reason: Explanation
                - detections: List of detected objects
                - annotated_image: Frame with bounding boxes
        """
        if not NCNN_AVAILABLE or not self.model_loaded:
            return self._dummy_predict(frame)
        
        start_time = time.time()
        
        # Store original dimensions
        orig_h, orig_w = frame.shape[:2]
        
        # Preprocess
        mat_in = self._preprocess(frame)
        
        # Run inference
        detections_raw = self._run_inference(mat_in, orig_w, orig_h)
        
        # Apply NMS (CRITICAL STEP)
        detections_filtered = self._apply_nms(detections_raw)
        
        if config.DEBUG_MODE:
            print(f"[AI] Raw detections: {len(detections_raw)}, After NMS: {len(detections_filtered)}")
        
        # Apply sorting logic
        result_dict = self._apply_sorting_logic(detections_filtered)
        
        # Draw detections on frame
        annotated = self._draw_detections(frame.copy(), detections_filtered)
        result_dict['annotated_image'] = annotated
        result_dict['detections'] = detections_filtered
        
        processing_time = (time.time() - start_time) * 1000
        result_dict['processing_time_ms'] = processing_time
        
        if config.VERBOSE_LOGGING:
            print(f"[AI] Result: {result_dict['result']} | Reason: {result_dict['reason']} | Time: {processing_time:.1f}ms")
        
        return result_dict
    
    def _preprocess(self, frame):
        """
        Preprocess frame for NCNN
        
        NCNN expects:
        - BGR format
        - 640x640 size
        - Mean subtraction & normalization
        """
        # Resize
        resized = cv2.resize(frame, (self.input_size, self.input_size))
        
        # Convert to ncnn.Mat
        mat_in = ncnn.Mat.from_pixels(
            resized,
            ncnn.Mat.PixelType.PIXEL_BGR,
            self.input_size,
            self.input_size
        )
        
        # Normalize (mean=0, norm=1/255)
        mean_vals = [0, 0, 0]
        norm_vals = [1/255.0, 1/255.0, 1/255.0]
        mat_in.substract_mean_normalize(mean_vals, norm_vals)
        
        return mat_in
    
    def _run_inference(self, mat_in, orig_w, orig_h):
        """
        Run NCNN inference
        
        Returns:
            List of raw detections (before NMS)
        """
        try:
            if config.DEBUG_MODE:
                print(f"[AI] Creating extractor...")
            
            # Create extractor
            ex = self.net.create_extractor()
            
            # Disable Vulkan if causing issues (use CPU)
            ex.set_vulkan_compute(False)  # Force CPU for stability
            
            if config.DEBUG_MODE:
                print(f"[AI] Setting input 'in0'...")
            
            # Input blob name
            ret_input = ex.input("in0", mat_in)
            
            if ret_input != 0:
                print(f"[ERROR] NCNN input failed with code {ret_input}")
                return []
            
            if config.DEBUG_MODE:
                print(f"[AI] Extracting output 'out0'...")
            
            # Extract output
            ret, mat_out = ex.extract("out0")
            
            if ret != 0:
                print(f"[ERROR] NCNN extract failed with code {ret}")
                return []
            
            if config.DEBUG_MODE:
                print(f"[AI] Output extracted successfully, parsing...")
            
            # Parse output
            detections = self._parse_ncnn_output(mat_out, orig_w, orig_h)
            
            return detections
            
        except Exception as e:
            print(f"[ERROR] NCNN inference failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_ncnn_output(self, output, img_w, img_h):
        """
        Parse NCNN output tensor
        
        YOLOv8 NCNN output format:
        - Shape: (1, 84, 8400) or (84, 8400)
        - 84 = 4 (bbox) + 80 (classes, but we only use 8)
        - 8400 = number of anchor boxes
        
        Format: [x_center, y_center, width, height, class1_score, class2_score, ...]
        """
        detections = []
        
        try:
            # Convert to numpy
            out_np = np.array(output)
            
            if config.DEBUG_MODE:
                print(f"[AI] NCNN output shape: {out_np.shape}")
            
            # Remove batch dimension if present
            if len(out_np.shape) == 3:
                out_np = out_np[0]
            
            # Transpose if needed: (84, 8400) -> (8400, 84)
            if out_np.shape[0] < out_np.shape[1]:
                out_np = out_np.T
                if config.DEBUG_MODE:
                    print(f"[AI] Transposed to: {out_np.shape}")
            
            num_detections = out_np.shape[0]
            num_classes = len(self.class_names)
            
            # Scale factors (input_size -> original size)
            scale_x = img_w / self.input_size
            scale_y = img_h / self.input_size
            
            # Process each detection
            for i in range(num_detections):
                detection = out_np[i]
                
                # Check format
                if len(detection) < 4 + num_classes:
                    continue
                
                # Extract bbox (center format, in input_size scale)
                x_center = detection[0] * scale_x
                y_center = detection[1] * scale_y
                width = detection[2] * scale_x
                height = detection[3] * scale_y
                
                # Extract class scores (only first 8 classes)
                class_scores = detection[4:4+num_classes]
                
                # Get best class
                class_id = int(np.argmax(class_scores))
                confidence = float(class_scores[class_id])
                
                # Filter by confidence
                if confidence > self.conf_threshold:
                    # Convert to corner format
                    x1 = int(x_center - width / 2)
                    y1 = int(y_center - height / 2)
                    x2 = int(x_center + width / 2)
                    y2 = int(y_center + height / 2)
                    
                    # Clamp to image bounds
                    x1 = max(0, min(x1, img_w))
                    y1 = max(0, min(y1, img_h))
                    x2 = max(0, min(x2, img_w))
                    y2 = max(0, min(y2, img_h))
                    
                    # Validate box
                    if x2 > x1 and y2 > y1:
                        detections.append({
                            'class_id': class_id,
                            'class_name': self.class_names[class_id],
                            'confidence': confidence,
                            'bbox': [x1, y1, x2, y2]
                        })
        
        except Exception as e:
            print(f"[ERROR] Parse NCNN output failed: {e}")
            if config.DEBUG_MODE:
                import traceback
                traceback.print_exc()
        
        return detections
    
    def _apply_nms(self, detections):
        """
        Apply Non-Maximum Suppression using OpenCV
        
        CRITICAL: This removes overlapping bounding boxes
        """
        if len(detections) == 0:
            return []
        
        # Extract boxes, scores, class_ids
        boxes = []
        confidences = []
        class_ids = []
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            boxes.append([x1, y1, x2 - x1, y2 - y1])  # Convert to [x, y, w, h]
            confidences.append(det['confidence'])
            class_ids.append(det['class_id'])
        
        # Apply cv2.dnn.NMSBoxes
        indices = cv2.dnn.NMSBoxes(
            boxes,
            confidences,
            self.conf_threshold,
            self.nms_threshold
        )
        
        # Filter detections
        filtered = []
        if len(indices) > 0:
            for i in indices.flatten():
                filtered.append(detections[i])
        
        return filtered
    
    def _apply_sorting_logic(self, detections):
        """
        Apply sorting logic to determine OK or NG
        
        Rules:
        - NG if any Defect (classes 0-3) detected
        - NG if any required component (cap, filled, label) is missing
        - OK otherwise
        """
        result = {
            'result': 'O',  # Default OK
            'reason': 'Sản phẩm đạt chuẩn',
            'has_defects': False,
            'defects_found': [],
            'has_cap': False,
            'has_filled': False,
            'has_label': False
        }
        
        # Check each detection
        for det in detections:
            class_id = det['class_id']
            class_name = det['class_name']
            
            # Check for defects
            if class_id in self.defect_classes:
                result['has_defects'] = True
                result['defects_found'].append(class_name)
            
            # Check for required components
            if class_id == self.required_components['cap']:
                result['has_cap'] = True
            elif class_id == self.required_components['filled']:
                result['has_filled'] = True
            elif class_id == self.required_components['label']:
                result['has_label'] = True
        
        # Determine NG conditions
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
        
        if config.DEBUG_MODE:
            print(f"[AI] Components: cap={result['has_cap']}, filled={result['has_filled']}, label={result['has_label']}")
            print(f"[AI] Defects: {result['defects_found']}")
        
        return result
    
    def _draw_detections(self, frame, detections):
        """
        Draw bounding boxes and labels on frame
        """
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            class_name = det['class_name']
            confidence = det['confidence']
            class_id = det['class_id']
            
            # Choose color (red for defects, green for good)
            if class_id in self.defect_classes:
                color = (0, 0, 255)  # Red
            else:
                color = (0, 255, 0)  # Green
            
            # Draw box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{class_name}: {confidence:.2f}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame, (x1, y1 - th - 4), (x1 + tw, y1), color, -1)
            cv2.putText(frame, label, (x1, y1 - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def _dummy_predict(self, frame):
        """
        Dummy prediction for testing UI without NCNN
        """
        import random
        
        result = 'O' if random.random() > 0.3 else 'N'
        reason = "OK" if result == 'O' else "Thiếu nhãn"
        
        return {
            'result': result,
            'reason': reason,
            'detections': [],
            'annotated_image': frame.copy(),
            'processing_time_ms': 50,
            'has_cap': True,
            'has_filled': True,
            'has_label': result == 'O',
            'has_defects': False,
            'defects_found': []
        }

