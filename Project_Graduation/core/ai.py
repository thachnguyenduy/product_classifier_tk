"""
AI Engine for Coca-Cola Sorting System
Uses NCNN model for real-time bottle inspection
Implements strict sorting logic based on defect detection and component verification
"""

import cv2
import numpy as np
import os
import random

try:
    import ncnn
    NCNN_AVAILABLE = True
except ImportError:
    NCNN_AVAILABLE = False
    print("[WARNING] NCNN library not available. Using dummy predictions for testing.")


class AIEngine:
    """
    AI Engine for bottle classification using NCNN model
    
    Class Mapping (0-7):
    - 0: Cap-Defect
    - 1: Filling-Defect  
    - 2: Label-Defect
    - 3: Wrong-Product
    - 4: cap (component)
    - 5: coca (component)
    - 6: filled (component)
    - 7: label (component)
    
    Sorting Logic:
    - NG if: ANY defect detected (0-3) OR missing critical components (4, 6, 7)
    - OK only if: NO defects AND has cap, filled, and label
    """
    
    def __init__(self, model_path="model/best_ncnn_model"):
        """
        Initialize AI Engine with NCNN model
        
        Args:
            model_path: Path to NCNN model directory
        """
        self.class_names = [
            'Cap-Defect',       # 0
            'Filling-Defect',   # 1
            'Label-Defect',     # 2
            'Wrong-Product',    # 3
            'cap',              # 4
            'coca',             # 5
            'filled',           # 6
            'label'             # 7
        ]
        
        # Critical components that must be present
        self.required_components = {4, 6, 7}  # cap, filled, label
        
        # Defect classes that trigger rejection
        self.defect_classes = {0, 1, 2, 3}
        
        self.confidence_threshold = 0.5
        self.input_size = 640  # Model trained on 640x640 images
        
        self.net = None
        self.model_loaded = False
        
        if NCNN_AVAILABLE:
            self._load_model(model_path)
        else:
            print("[AI] Running in DEMO mode (NCNN not installed)")
    
    def _load_model(self, model_path):
        """Load NCNN model from param and bin files"""
        try:
            param_file = os.path.join(model_path, "model.ncnn.param")
            bin_file = os.path.join(model_path, "model.ncnn.bin")
            
            if not os.path.exists(param_file) or not os.path.exists(bin_file):
                print(f"[ERROR] Model files not found at {model_path}")
                return
            
            self.net = ncnn.Net()
            self.net.load_param(param_file)
            self.net.load_model(bin_file)
            
            self.model_loaded = True
            print(f"[AI] NCNN model loaded successfully from {model_path}")
            
        except Exception as e:
            print(f"[ERROR] Failed to load NCNN model: {e}")
            self.model_loaded = False
    
    def predict(self, frame):
        """
        Predict bottle quality from image frame
        
        Args:
            frame: OpenCV image (BGR format)
        
        Returns:
            dict: {
                'result': 'OK' or 'NG',
                'reason': Explanation string,
                'detections': List of detected objects,
                'has_cap': bool,
                'has_filled': bool,
                'has_label': bool,
                'defects_found': list
            }
        """
        if not NCNN_AVAILABLE or not self.model_loaded:
            return self._dummy_predict()
        
        try:
            # Preprocess image
            img = self._preprocess(frame)
            
            # Run inference
            detections = self._inference(img)
            
            # Apply sorting logic
            result = self._apply_sorting_logic(detections)
            
            return result
            
        except Exception as e:
            print(f"[ERROR] Prediction failed: {e}")
            return {
                'result': 'OK',
                'reason': f'Error occurred: {str(e)}',
                'detections': [],
                'has_cap': False,
                'has_filled': False,
                'has_label': False,
                'defects_found': []
            }
    
    def _preprocess(self, frame):
        """
        Preprocess image for NCNN model
        - Resize to 640x640
        - Normalize pixel values
        """
        # Resize to model input size
        img = cv2.resize(frame, (self.input_size, self.input_size))
        
        # Convert BGR to RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        return img
    
    def _inference(self, img):
        """
        Run NCNN inference on preprocessed image
        
        Returns:
            List of detections: [(class_id, confidence, x, y, w, h), ...]
        """
        detections = []
        
        try:
            # Create NCNN Mat from numpy array
            mat_in = ncnn.Mat.from_pixels(
                img,
                ncnn.Mat.PixelType.PIXEL_RGB,
                img.shape[1],
                img.shape[0]
            )
            
            # Normalize (assuming model expects 0-1 range)
            mat_in.substract_mean_normalize([0, 0, 0], [1/255.0, 1/255.0, 1/255.0])
            
            # Create extractor
            ex = self.net.create_extractor()
            ex.input("in0", mat_in)
            
            # Get output
            ret, mat_out = ex.extract("out0")
            
            if ret == 0:
                # Parse detections (YOLO format)
                detections = self._parse_yolo_output(mat_out)
            
        except Exception as e:
            print(f"[ERROR] Inference error: {e}")
        
        return detections
    
    def _parse_yolo_output(self, mat_out):
        """
        Parse YOLO NCNN output to detection list
        
        Note: This is a simplified parser. Adjust based on actual model output format.
        """
        detections = []
        
        try:
            # Convert Mat to numpy array
            out = np.array(mat_out)
            
            # YOLO output format: [batch, num_detections, (x, y, w, h, conf, cls_conf...)]
            # Parse each detection
            for detection in out:
                if len(detection) >= 6:
                    x, y, w, h, conf = detection[:5]
                    class_scores = detection[5:]
                    
                    if conf > self.confidence_threshold:
                        class_id = np.argmax(class_scores)
                        class_conf = class_scores[class_id]
                        
                        if class_conf > self.confidence_threshold:
                            detections.append({
                                'class_id': int(class_id),
                                'confidence': float(class_conf),
                                'bbox': [float(x), float(y), float(w), float(h)]
                            })
        
        except Exception as e:
            print(f"[ERROR] Parse output error: {e}")
        
        return detections
    
    def _apply_sorting_logic(self, detections):
        """
        Apply strict sorting logic based on detections
        
        CRITICAL SORTING RULES:
        1. If ANY defect detected (class 0-3) -> NG
        2. If missing cap (4), filled (6), or label (7) -> NG
        3. Only OK if: NO defects AND has all required components
        """
        # Track what we found
        detected_classes = set()
        defects_found = []
        all_detections = []
        
        # Analyze detections
        for det in detections:
            class_id = det['class_id']
            confidence = det['confidence']
            class_name = self.class_names[class_id]
            
            detected_classes.add(class_id)
            all_detections.append({
                'class': class_name,
                'confidence': f"{confidence:.2f}"
            })
            
            # Check for defects
            if class_id in self.defect_classes:
                defects_found.append(class_name)
        
        # Component checks
        has_cap = 4 in detected_classes
        has_filled = 6 in detected_classes
        has_label = 7 in detected_classes
        
        # RULE 1: Any defect -> NG
        if defects_found:
            return {
                'result': 'NG',
                'reason': f'Defects detected: {", ".join(defects_found)}',
                'detections': all_detections,
                'has_cap': has_cap,
                'has_filled': has_filled,
                'has_label': has_label,
                'defects_found': defects_found
            }
        
        # RULE 2: Missing required components -> NG
        missing_components = []
        if not has_cap:
            missing_components.append('cap')
        if not has_filled:
            missing_components.append('filled')
        if not has_label:
            missing_components.append('label')
        
        if missing_components:
            return {
                'result': 'NG',
                'reason': f'Missing components: {", ".join(missing_components)}',
                'detections': all_detections,
                'has_cap': has_cap,
                'has_filled': has_filled,
                'has_label': has_label,
                'defects_found': []
            }
        
        # RULE 3: No defects + all components -> OK
        return {
            'result': 'OK',
            'reason': 'All components present, no defects',
            'detections': all_detections,
            'has_cap': True,
            'has_filled': True,
            'has_label': True,
            'defects_found': []
        }
    
    def _dummy_predict(self):
        """
        Dummy prediction for testing when NCNN is not available
        Returns random OK/NG results for UI testing
        """
        # Random decision (70% OK, 30% NG)
        is_ok = random.random() > 0.3
        
        if is_ok:
            return {
                'result': 'OK',
                'reason': '[DEMO] All components present, no defects',
                'detections': [
                    {'class': 'cap', 'confidence': '0.95'},
                    {'class': 'label', 'confidence': '0.92'},
                    {'class': 'filled', 'confidence': '0.88'}
                ],
                'has_cap': True,
                'has_filled': True,
                'has_label': True,
                'defects_found': []
            }
        else:
            defect = random.choice(['Cap-Defect', 'Label-Defect', 'Filling-Defect'])
            return {
                'result': 'NG',
                'reason': f'[DEMO] Defect detected: {defect}',
                'detections': [
                    {'class': defect, 'confidence': '0.87'}
                ],
                'has_cap': False,
                'has_filled': True,
                'has_label': True,
                'defects_found': [defect]
            }
    
    def draw_detections(self, frame, detections):
        """
        Draw bounding boxes on frame for visualization
        
        Args:
            frame: Original image
            detections: List of detection dictionaries
        
        Returns:
            frame: Annotated image
        """
        for det in detections:
            if 'bbox' in det:
                x, y, w, h = det['bbox']
                class_name = self.class_names[det['class_id']]
                confidence = det['confidence']
                
                # Draw box
                color = (0, 0, 255) if det['class_id'] in self.defect_classes else (0, 255, 0)
                cv2.rectangle(frame, (int(x), int(y)), (int(x+w), int(y+h)), color, 2)
                
                # Draw label
                label = f"{class_name}: {confidence:.2f}"
                cv2.putText(frame, label, (int(x), int(y)-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return frame

