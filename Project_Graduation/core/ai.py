"""
AI Engine for Coca-Cola Sorting System
Uses YOLOv8 model (.pt) for real-time bottle inspection
Implements strict sorting logic based on defect detection and component verification
"""

import cv2
import numpy as np
import os
import random
import time

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("[WARNING] ultralytics library not available. Using dummy predictions for testing.")
    print("         Install with: pip install ultralytics")

# Import config
try:
    import config
except ImportError:
    # Default values if config not found
    class config:
        CONFIDENCE_THRESHOLD = 0.3
        DEBUG_MODE = True


class AIEngine:
    """
    AI Engine for bottle classification using YOLOv8 model
    
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
    
    def __init__(self, model_path="model/best.pt"):
        """
        Initialize AI Engine with YOLOv8 model
        
        Args:
            model_path: Path to YOLOv8 .pt model file
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
        
        # Load from config
        self.confidence_threshold = getattr(config, 'CONFIDENCE_THRESHOLD', 0.3)
        self.input_size = 640  # Model trained on 640x640 images
        self.debug_mode = getattr(config, 'DEBUG_MODE', True)
        self.require_cap = getattr(config, 'REQUIRE_CAP', True)
        self.require_filled = getattr(config, 'REQUIRE_FILLED', True)
        self.require_label = getattr(config, 'REQUIRE_LABEL', True)
        self.save_debug = getattr(config, 'SAVE_DEBUG_IMAGES', False)
        
        self.model = None
        self.model_loaded = False
        self.model_path = model_path
        
        if YOLO_AVAILABLE:
            self._load_model(model_path)
        else:
            print("[AI] Running in DEMO mode (YOLOv8 not installed)")
    
    def _load_model(self, model_path):
        """Load YOLOv8 model from .pt file"""
        try:
            if not os.path.exists(model_path):
                print(f"[ERROR] Model file not found at {model_path}")
                return
            
            print(f"[AI] Loading YOLOv8 model from {model_path}...")
            self.model = YOLO(model_path)
            
            self.model_loaded = True
            print(f"[AI] YOLOv8 model loaded successfully!")
            
        except Exception as e:
            print(f"[ERROR] Failed to load YOLOv8 model: {e}")
            self.model_loaded = False
    
    def predict_single(self, frame):
        """
        Predict bottle quality from a single image frame
        
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
                'defects_found': list,
                'annotated_image': frame with bounding boxes drawn
            }
        """
        if not YOLO_AVAILABLE or not self.model_loaded:
            return self._dummy_predict(frame)
        
        try:
            # Run YOLOv8 inference
            results = self.model(frame, conf=self.confidence_threshold, verbose=False)[0]
            
            # Parse detections
            detections = []
            detected_classes = set()
            defects_found = []
            
            # Get boxes, classes, and confidences
            if results.boxes is not None and len(results.boxes) > 0:
                for box in results.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    bbox = box.xyxy[0].cpu().numpy()  # [x1, y1, x2, y2]
                    
                    if class_id < len(self.class_names):
                        class_name = self.class_names[class_id]
                        detected_classes.add(class_id)
                        
                        detections.append({
                            'class': class_name,
                            'class_id': class_id,
                            'confidence': f"{confidence:.2f}",
                            'bbox': bbox.tolist()
                        })
                        
                        # DEBUG: Print detection
                        if self.debug_mode:
                            print(f"[AI] Detected: {class_name} (conf: {confidence:.2f})")
                        
                        # Check for defects
                        if class_id in self.defect_classes:
                            defects_found.append(class_name)
            
            # Component checks
            has_cap = 4 in detected_classes
            has_filled = 6 in detected_classes
            has_label = 7 in detected_classes
            
            # Draw bounding boxes on frame
            annotated_frame = self.draw_detections(frame.copy(), detections)
            
            # Apply sorting logic
            result = self._apply_sorting_logic_internal(
                defects_found, has_cap, has_filled, has_label, detections
            )
            result['annotated_image'] = annotated_frame

            # Save debug image if needed
            if self.save_debug:
                os.makedirs("captures/debug", exist_ok=True)
                ts = int(time.time() * 1000)
                cv2.imwrite(f"captures/debug/debug_{ts}.jpg", annotated_frame)
            
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
                'defects_found': [],
                'annotated_image': frame
            }
    
    def predict_multiple(self, frames):
        """
        Predict from multiple frames and return best result
        
        Args:
            frames: List of OpenCV images
        
        Returns:
            dict: Combined result with best annotated image
        """
        if not frames:
            return self.predict_single(np.zeros((640, 640, 3), dtype=np.uint8))
        
        results = []
        for frame in frames:
            result = self.predict_single(frame)
            results.append(result)
        
        # Find frame with most detections
        best_idx = 0
        max_detections = len(results[0]['detections'])
        
        for i, result in enumerate(results):
            if len(result['detections']) > max_detections:
                max_detections = len(result['detections'])
                best_idx = i
        
        # Use best frame's result
        best_result = results[best_idx]
        
        # Combine detections from all frames for decision
        all_detected_classes = set()
        all_defects = []
        
        for result in results:
            for det in result['detections']:
                all_detected_classes.add(det['class_id'])
                if det['class_id'] in self.defect_classes:
                    all_defects.append(det['class'])
        
        # Recompute final decision based on all frames
        has_cap = 4 in all_detected_classes
        has_filled = 6 in all_detected_classes
        has_label = 7 in all_detected_classes
        all_defects = list(set(all_defects))  # Remove duplicates
        
        final_result = self._apply_sorting_logic_internal(
            all_defects, has_cap, has_filled, has_label, best_result['detections']
        )
        final_result['annotated_image'] = best_result['annotated_image']
        
        return final_result
    
    def predict(self, frame):
        """
        Main predict function (for backward compatibility)
        Captures multiple frames if frame is from camera
        
        Args:
            frame: OpenCV image or Camera object
        
        Returns:
            dict: Prediction result
        """
        # For now, just predict single frame
        return self.predict_single(frame)
    
    def _apply_sorting_logic_internal(self, defects_found, has_cap, has_filled, has_label, detections):
        """
        Apply strict sorting logic based on detections
        """
        # DEBUG: Print component status
        if self.debug_mode:
            print(f"[AI] Components check:")
            print(f"     - Cap: {'✓' if has_cap else '✗'}")
            print(f"     - Filled: {'✓' if has_filled else '✗'}")
            print(f"     - Label: {'✓' if has_label else '✗'}")
            print(f"     - Defects: {defects_found if defects_found else 'None'}")
        
        # RULE 1: Any defect -> NG
        if defects_found:
            if self.debug_mode:
                print(f"[AI] Result: NG (Defects found)")
            return {
                'result': 'NG',
                'reason': f'Lỗi: {", ".join(defects_found)}',
                'detections': detections,
                'has_cap': has_cap,
                'has_filled': has_filled,
                'has_label': has_label,
                'defects_found': defects_found
            }
        
        # RULE 2: Missing required components -> NG
        missing_components = []
        if self.require_cap and not has_cap:
            missing_components.append('cap')
        if self.require_filled and not has_filled:
            missing_components.append('filled')
        if self.require_label and not has_label:
            missing_components.append('label')
        
        if missing_components:
            if self.debug_mode:
                print(f"[AI] Result: NG (Missing: {', '.join(missing_components)})")
            return {
                'result': 'NG',
                'reason': f'Thiếu: {", ".join(missing_components)}',
                'detections': detections,
                'has_cap': has_cap,
                'has_filled': has_filled,
                'has_label': has_label,
                'defects_found': []
            }
        
        # RULE 3: No defects + all components -> OK
        if self.debug_mode:
            print(f"[AI] Result: OK (All components present)")
        return {
            'result': 'OK',
            'reason': 'Đạt tiêu chuẩn, không có lỗi',
            'detections': detections,
            'has_cap': True,
            'has_filled': True,
            'has_label': True,
            'defects_found': []
        }
    
    def _dummy_predict(self, frame):
        """
        Dummy prediction for testing when YOLOv8 is not available
        """
        # Random decision (70% OK, 30% NG)
        is_ok = random.random() > 0.3
        
        # Draw some dummy boxes
        annotated_frame = frame.copy()
        h, w = frame.shape[:2]
        
        if is_ok:
            # Draw dummy component boxes
            cv2.rectangle(annotated_frame, (w//4, h//4), (w//2, h//2), (0, 255, 0), 2)
            cv2.putText(annotated_frame, "cap: 0.95", (w//4, h//4-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            return {
                'result': 'OK',
                'reason': '[DEMO] All components present, no defects',
                'detections': [
                    {'class': 'cap', 'class_id': 4, 'confidence': '0.95'},
                    {'class': 'label', 'class_id': 7, 'confidence': '0.92'},
                    {'class': 'filled', 'class_id': 6, 'confidence': '0.88'}
                ],
                'has_cap': True,
                'has_filled': True,
                'has_label': True,
                'defects_found': [],
                'annotated_image': annotated_frame
            }
        else:
            # Draw dummy defect box
            cv2.rectangle(annotated_frame, (w//3, h//3), (2*w//3, 2*h//3), (0, 0, 255), 2)
            defect = random.choice(['Cap-Defect', 'Label-Defect', 'Filling-Defect'])
            cv2.putText(annotated_frame, f"{defect}: 0.87", (w//3, h//3-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            return {
                'result': 'NG',
                'reason': f'[DEMO] Defect detected: {defect}',
                'detections': [
                    {'class': defect, 'class_id': 0, 'confidence': '0.87'}
                ],
                'has_cap': False,
                'has_filled': True,
                'has_label': True,
                'defects_found': [defect],
                'annotated_image': annotated_frame
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
            class_id = det['class_id']
            class_name = det['class']
            confidence = det['confidence']
            
            if 'bbox' in det:
                bbox = det['bbox']
                x1, y1, x2, y2 = map(int, bbox)
                
                # Choose color: Red for defects, Green for components
                color = (0, 0, 255) if class_id in self.defect_classes else (0, 255, 0)
                
                # Draw box
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                
                # Draw label
                label = f"{class_name}: {confidence}"
                (text_width, text_height), baseline = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
                )
                
                # Background for text
                cv2.rectangle(frame, (x1, y1 - text_height - 10), 
                            (x1 + text_width, y1), color, -1)
                
                # Text
                cv2.putText(frame, label, (x1, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return frame
