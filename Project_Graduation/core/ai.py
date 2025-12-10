"""
AI Engine for Coca-Cola Sorting System (CONTINUOUS MODE)
Uses NCNN for fast inference with proper NMS to handle overlapping boxes
"""

import cv2
import numpy as np
import time
import os
from pathlib import Path

try:
    import ncnn
    NCNN_AVAILABLE = True
except ImportError:
    NCNN_AVAILABLE = False
    print("[WARNING] NCNN not available. Install with: pip install ncnn")


class AIEngine:
    """
    AI Engine using NCNN model for bottle inspection
    Implements proper NMS using cv2.dnn.NMSBoxes
    """
    
    def __init__(self, model_path="model/best_ncnn_model", config=None):
        """
        Initialize AI Engine
        
        Args:
            model_path: Path to NCNN model folder
            config: Configuration module (optional)
        """
        print("[AI] Initializing AI Engine...")
        
        self.model_path = model_path
        self.net = None
        self.model_loaded = False
        
        # Load configuration
        if config is None:
            try:
                import config as cfg
                self.config = cfg
            except ImportError:
                print("[WARNING] config.py not found, using defaults")
                self.config = None
        else:
            self.config = config
        
        # Get configuration values
        self.confidence_threshold = getattr(self.config, 'CONFIDENCE_THRESHOLD', 0.5)
        self.nms_threshold = getattr(self.config, 'NMS_THRESHOLD', 0.45)
        self.class_names = getattr(self.config, 'CLASS_NAMES', [
            'Cap-Defect', 'Filling-Defect', 'Label-Defect', 'Wrong-Product',
            'cap', 'coca', 'filled', 'label'
        ])
        self.defect_classes = getattr(self.config, 'DEFECT_CLASSES', [0, 1, 2, 3])
        self.required_components = getattr(self.config, 'REQUIRED_COMPONENTS', {
            'cap': 4, 'filled': 6, 'label': 7
        })
        self.require_cap = getattr(self.config, 'REQUIRE_CAP', True)
        self.require_filled = getattr(self.config, 'REQUIRE_FILLED', True)
        self.require_label = getattr(self.config, 'REQUIRE_LABEL', True)
        self.debug_mode = getattr(self.config, 'DEBUG_MODE', True)
        self.save_debug_images = getattr(self.config, 'SAVE_DEBUG_IMAGES', True)
        
        # Model parameters
        self.input_size = 640
        
        # Load model
        if NCNN_AVAILABLE:
            self._load_ncnn_model()
        else:
            print("[WARNING] NCNN not available, using dummy predictions")
    
    def _load_ncnn_model(self):
        """Load NCNN model from .param and .bin files"""
        try:
            param_path = os.path.join(self.model_path, "model.ncnn.param")
            bin_path = os.path.join(self.model_path, "model.ncnn.bin")
            
            if not os.path.exists(param_path) or not os.path.exists(bin_path):
                print(f"[ERROR] Model files not found at {self.model_path}")
                print(f"  Expected: {param_path}")
                print(f"  Expected: {bin_path}")
                return
            
            self.net = ncnn.Net()
            self.net.load_param(param_path)
            self.net.load_model(bin_path)
            
            self.model_loaded = True
            print(f"[AI] NCNN model loaded successfully from {self.model_path}")
            print(f"[AI] Confidence threshold: {self.confidence_threshold}")
            print(f"[AI] NMS threshold: {self.nms_threshold}")
            
        except Exception as e:
            print(f"[ERROR] Failed to load NCNN model: {e}")
            self.model_loaded = False
    
    def predict(self, frame):
        """
        Run inference on a single frame (FAST - for continuous mode)
        
        Args:
            frame: BGR image from camera
            
        Returns:
            dict with keys:
                - result: 'OK' or 'NG'
                - reason: Explanation string
                - detections: List of detected objects
                - annotated_image: Frame with bounding boxes
                - processing_time: Time in seconds
        """
        start_time = time.time()
        
        if not self.model_loaded or not NCNN_AVAILABLE:
            return self._dummy_prediction(frame)
        
        try:
            # Preprocess
            img_h, img_w = frame.shape[:2]
            preprocessed = self._preprocess(frame)
            
            # Run inference
            detections = self._run_ncnn_inference(preprocessed, img_w, img_h)
            
            # Apply NMS using cv2.dnn.NMSBoxes
            detections = self._apply_nms(detections)
            
            # Apply sorting logic
            result_dict = self._apply_sorting_logic(detections)
            
            # Draw bounding boxes
            annotated_image = self._draw_boxes(frame.copy(), detections)
            
            # Add metadata
            processing_time = time.time() - start_time
            result_dict['annotated_image'] = annotated_image
            result_dict['processing_time'] = processing_time
            
            if self.debug_mode:
                print(f"[AI] Prediction: {result_dict['result']} | "
                      f"Reason: {result_dict['reason']} | "
                      f"Time: {processing_time*1000:.1f}ms")
            
            return result_dict
            
        except Exception as e:
            print(f"[ERROR] Prediction failed: {e}")
            import traceback
            traceback.print_exc()
            return self._dummy_prediction(frame)
    
    def _preprocess(self, frame):
        """
        Preprocess frame for NCNN inference
        
        Args:
            frame: BGR image
            
        Returns:
            ncnn.Mat object
        """
        # Resize to model input size
        resized = cv2.resize(frame, (self.input_size, self.input_size))
        
        # Convert BGR to RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # Create NCNN Mat
        mat = ncnn.Mat.from_pixels(rgb, ncnn.Mat.PixelType.PIXEL_RGB, 
                                    self.input_size, self.input_size)
        
        # Normalize (0-1)
        mean_vals = []
        norm_vals = [1/255.0, 1/255.0, 1/255.0]
        mat.substract_mean_normalize(mean_vals, norm_vals)
        
        return mat
    
    def _run_ncnn_inference(self, mat, img_w, img_h):
        """
        Run NCNN inference
        
        Args:
            mat: Preprocessed ncnn.Mat
            img_w: Original image width
            img_h: Original image height
            
        Returns:
            List of detections (before NMS)
        """
        # Create extractor
        ex = self.net.create_extractor()
        ex.input("in0", mat)
        
        # Extract output
        ret, out = ex.extract("out0")
        
        if ret != 0:
            print(f"[ERROR] NCNN extraction failed with code {ret}")
            return []
        
        # Parse output
        detections = self._parse_ncnn_output(out, img_w, img_h)
        
        return detections
    
    def _parse_ncnn_output(self, output, img_w, img_h):
        """
        Parse NCNN output tensor into detections
        
        Args:
            output: ncnn.Mat output
            img_w: Original image width
            img_h: Original image height
            
        Returns:
            List of detection dicts
        """
        detections = []
        
        # Convert ncnn.Mat to numpy array
        # Output shape is typically (num_anchors, num_classes + 4)
        # where first 4 values are bbox coords, rest are class scores
        output_np = np.array(output)
        
        # Handle different output shapes
        if len(output_np.shape) == 3:
            # Shape: (1, num_anchors, num_classes + 4)
            output_np = output_np[0]
        
        num_anchors = output_np.shape[0]
        num_classes = len(self.class_names)
        
        # Scale factors
        scale_x = img_w / self.input_size
        scale_y = img_h / self.input_size
        
        for i in range(num_anchors):
            row = output_np[i]
            
            # Extract bbox (first 4 values: x_center, y_center, width, height)
            x_center = row[0] * scale_x
            y_center = row[1] * scale_y
            width = row[2] * scale_x
            height = row[3] * scale_y
            
            # Extract class scores (remaining values)
            class_scores = row[4:4+num_classes]
            
            # Get best class
            class_id = np.argmax(class_scores)
            confidence = float(class_scores[class_id])
            
            # Filter by confidence
            if confidence > self.confidence_threshold:
                # Convert to x1, y1, x2, y2
                x1 = int(x_center - width / 2)
                y1 = int(y_center - height / 2)
                x2 = int(x_center + width / 2)
                y2 = int(y_center + height / 2)
                
                # Clamp to image bounds
                x1 = max(0, min(x1, img_w))
                y1 = max(0, min(y1, img_h))
                x2 = max(0, min(x2, img_w))
                y2 = max(0, min(y2, img_h))
                
                detections.append({
                    'class_id': int(class_id),
                    'class_name': self.class_names[class_id],
                    'confidence': confidence,
                    'bbox': [x1, y1, x2, y2]
                })
        
        return detections
    
    def _apply_nms(self, detections):
        """
        Apply Non-Maximum Suppression using cv2.dnn.NMSBoxes
        
        Args:
            detections: List of detection dicts
            
        Returns:
            Filtered list of detections
        """
        if len(detections) == 0:
            return []
        
        # Prepare data for NMS
        boxes = []
        confidences = []
        class_ids = []
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            # cv2.dnn.NMSBoxes expects [x, y, width, height]
            boxes.append([x1, y1, x2 - x1, y2 - y1])
            confidences.append(float(det['confidence']))
            class_ids.append(det['class_id'])
        
        # Apply NMS
        indices = cv2.dnn.NMSBoxes(
            boxes,
            confidences,
            self.confidence_threshold,
            self.nms_threshold
        )
        
        # Filter detections
        if len(indices) > 0:
            # indices is a list of lists in OpenCV 4.x
            if isinstance(indices, tuple):
                indices = indices[0] if len(indices) > 0 else []
            
            # Flatten if needed
            if len(indices) > 0 and isinstance(indices[0], (list, np.ndarray)):
                indices = [i[0] if isinstance(i, (list, np.ndarray)) else i for i in indices]
            
            filtered_detections = [detections[i] for i in indices]
        else:
            filtered_detections = []
        
        if self.debug_mode and len(detections) != len(filtered_detections):
            print(f"[AI] NMS: {len(detections)} -> {len(filtered_detections)} detections")
        
        return filtered_detections
    
    def _apply_sorting_logic(self, detections):
        """
        Apply sorting logic based on detections
        
        Args:
            detections: List of detection dicts
            
        Returns:
            dict with result and reason
        """
        # Check for defects
        defects_found = []
        for det in detections:
            if det['class_id'] in self.defect_classes:
                defects_found.append(det['class_name'])
        
        # Check for required components
        has_cap = any(det['class_id'] == self.required_components['cap'] for det in detections)
        has_filled = any(det['class_id'] == self.required_components['filled'] for det in detections)
        has_label = any(det['class_id'] == self.required_components['label'] for det in detections)
        
        if self.debug_mode:
            print(f"[AI] Components: cap={has_cap}, filled={has_filled}, label={has_label}")
            if defects_found:
                print(f"[AI] Defects: {defects_found}")
        
        # RULE 1: Any defect -> NG
        if defects_found:
            return {
                'result': 'NG',
                'reason': f'Defect: {", ".join(defects_found)}',
                'detections': detections,
                'has_cap': has_cap,
                'has_filled': has_filled,
                'has_label': has_label,
                'defects_found': defects_found
            }
        
        # RULE 2: Missing required components -> NG
        missing = []
        if self.require_cap and not has_cap:
            missing.append('cap')
        if self.require_filled and not has_filled:
            missing.append('filled')
        if self.require_label and not has_label:
            missing.append('label')
        
        if missing:
            return {
                'result': 'NG',
                'reason': f'Missing: {", ".join(missing)}',
                'detections': detections,
                'has_cap': has_cap,
                'has_filled': has_filled,
                'has_label': has_label,
                'defects_found': []
            }
        
        # RULE 3: All good -> OK
        return {
            'result': 'OK',
            'reason': 'All components present, no defects',
            'detections': detections,
            'has_cap': has_cap,
            'has_filled': has_filled,
            'has_label': has_label,
            'defects_found': []
        }
    
    def _draw_boxes(self, image, detections):
        """
        Draw bounding boxes on image
        
        Args:
            image: BGR image
            detections: List of detection dicts
            
        Returns:
            Annotated image
        """
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            class_name = det['class_name']
            confidence = det['confidence']
            
            # Color: Red for defects, Green for components
            if det['class_id'] in self.defect_classes:
                color = (0, 0, 255)  # Red
            else:
                color = (0, 255, 0)  # Green
            
            # Draw box
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{class_name} {confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            
            # Background for text
            cv2.rectangle(image, 
                         (x1, y1 - label_size[1] - 4),
                         (x1 + label_size[0], y1),
                         color, -1)
            
            # Text
            cv2.putText(image, label, (x1, y1 - 2),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return image
    
    def _dummy_prediction(self, frame):
        """
        Dummy prediction for testing without NCNN
        
        Args:
            frame: BGR image
            
        Returns:
            Dummy result dict
        """
        import random
        
        result = 'OK' if random.random() > 0.3 else 'NG'
        reason = 'Dummy prediction (NCNN not available)'
        
        # Draw text on frame
        annotated = frame.copy()
        cv2.putText(annotated, f"DUMMY MODE: {result}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        return {
            'result': result,
            'reason': reason,
            'detections': [],
            'annotated_image': annotated,
            'processing_time': 0.05,
            'has_cap': True,
            'has_filled': True,
            'has_label': True,
            'defects_found': []
        }
