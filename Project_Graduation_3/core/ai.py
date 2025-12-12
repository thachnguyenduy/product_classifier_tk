# ============================================
# AI ENGINE - YOLO Detection with Line Crossing
# ============================================
"""
AI Engine for Coca-Cola Bottle Sorting System

CRITICAL CLASSIFICATION RULES:
1. NG if ANY defect class detected (Cap-Defect, Filling-Defect, Label-Defect, Wrong-Product)
2. OK if ALL good classes (cap + label + filled) detected AND NO defects
3. "coca" class is ONLY for identity confirmation, NOT for classification
4. NO confidence score usage for classification
5. Classification based ONLY on detected labels

IMPORTANT: 
- Line crossing finalizes classification
- Each bottle has unique object_id
- Continuously collect labels while bottle is RIGHT of line
- When bottle CROSSES line (right to left), classification is LOCKED
"""

import cv2
import numpy as np
import time
from ultralytics import YOLO
import config


class TrackedObject:
    """
    Represents a tracked bottle with accumulated detections
    """
    def __init__(self, object_id, x_center, y_center):
        self.object_id = object_id
        self.x_center = x_center
        self.y_center = y_center
        self.detected_classes = set()  # Accumulate class names
        self.bbox = None
        self.last_seen = time.time()
        self.crossed = False
        self.classification_result = None  # 'OK' or 'NG'
        self.classification_reason = ""
    
    def update_position(self, x_center, y_center, bbox=None):
        """Update object position"""
        self.x_center = x_center
        self.y_center = y_center
        if bbox is not None:
            self.bbox = bbox
        self.last_seen = time.time()
    
    def add_detected_class(self, class_name):
        """Add detected class to collection"""
        self.detected_classes.add(class_name)
    
    def finalize_classification(self):
        """
        Finalize classification when crossing line
        
        Rules (STRICT):
        - If ANY defect detected → NG
        - If ALL good classes (cap + label + filled) present AND NO defects → OK
        - Otherwise → NG
        """
        # Check for defects
        defect_classes = {'Cap-Defect', 'Filling-Defect', 'Label-Defect', 'Wrong-Product'}
        detected_defects = self.detected_classes & defect_classes
        
        if detected_defects:
            # ANY defect → NG
            self.classification_result = 'NG'
            self.classification_reason = f"Defect: {', '.join(detected_defects)}"
            return
        
        # Check for all required good classes
        required_good = {'cap', 'label', 'filled'}
        has_all_good = required_good.issubset(self.detected_classes)
        
        if has_all_good:
            # All good classes present, no defects → OK
            self.classification_result = 'OK'
            self.classification_reason = "All components OK"
        else:
            # Missing some good classes → NG
            missing = required_good - self.detected_classes
            self.classification_result = 'NG'
            self.classification_reason = f"Missing: {', '.join(missing)}"


class AIEngine:
    """
    AI Engine using YOLO for object detection and tracking
    
    Responsibilities:
    - Run YOLO inference on frames
    - Track bottles across frames
    - Accumulate detected classes per bottle
    - Detect line crossing (RIGHT → LEFT)
    - Finalize classification when bottle crosses line
    """
    
    def __init__(self):
        print("[AI] Initializing YOLO model...")
        
        # Load YOLO model
        try:
            self.model = YOLO(config.MODEL_PATH_YOLO)
            print(f"[AI] Model loaded: {config.MODEL_PATH_YOLO}")
        except Exception as e:
            print(f"[ERROR] Failed to load YOLO model: {e}")
            raise
        
        # Configuration
        self.conf_threshold = config.CONFIDENCE_THRESHOLD
        self.class_names = config.CLASS_NAMES
        self.num_classes = len(self.class_names)
        
        # Tracking
        self.tracked_objects = {}  # {object_id: TrackedObject}
        self.next_object_id = 0
        self.max_distance = 100  # Max pixels for object matching
        self.object_timeout = 3.0  # Remove objects not seen for 3 seconds
        
        # Line crossing
        self.virtual_line_x = config.VIRTUAL_LINE_X
        
        print(f"[AI] Initialized with {self.num_classes} classes")
        print(f"[AI] Virtual line at x={self.virtual_line_x}")
        print(f"[AI] Class names: {self.class_names}")
    
    def predict_and_track(self, frame):
        """
        Run YOLO detection and update tracking
        
        Returns:
            dict: {
                'detections': list of detection dicts,
                'tracked_objects': dict of TrackedObject,
                'crossed_objects': list of objects that just crossed line
            }
        """
        # Run YOLO inference
        results = self.model.predict(
            frame,
            conf=self.conf_threshold,
            verbose=False
        )
        
        # Parse detections
        detections = []
        if len(results) > 0:
            result = results[0]
            if result.boxes is not None:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0].cpu().numpy())
                    class_id = int(box.cls[0].cpu().numpy())
                    
                    if class_id < len(self.class_names):
                        class_name = self.class_names[class_id]
                        
                        detections.append({
                            'bbox': [int(x1), int(y1), int(x2), int(y2)],
                            'confidence': confidence,
                            'class_id': class_id,
                            'class_name': class_name
                        })
        
        # Update tracking and check for line crossing
        crossed_objects = self._update_tracking(detections)
        
        return {
            'detections': detections,
            'tracked_objects': self.tracked_objects,
            'crossed_objects': crossed_objects
        }
    
    def _update_tracking(self, detections):
        """
        Update object tracking with new detections
        
        Returns:
            list: Objects that just crossed the line
        """
        current_time = time.time()
        crossed_objects = []
        
        # Remove old tracked objects
        self.tracked_objects = {
            obj_id: obj for obj_id, obj in self.tracked_objects.items()
            if current_time - obj.last_seen < self.object_timeout
        }
        
        # Group detections by position (multiple classes can detect same bottle)
        detection_groups = self._group_detections_by_position(detections)
        
        # Match detection groups to tracked objects
        matched_detections = set()
        
        for obj_id, tracked_obj in list(self.tracked_objects.items()):
            if tracked_obj.crossed:
                continue  # Skip already crossed objects
            
            # Find closest detection group
            best_match = None
            min_distance = self.max_distance
            
            for i, group in enumerate(detection_groups):
                if i in matched_detections:
                    continue
                
                group_center = group['center']
                distance = np.sqrt(
                    (group_center[0] - tracked_obj.x_center)**2 +
                    (group_center[1] - tracked_obj.y_center)**2
                )
                
                if distance < min_distance:
                    min_distance = distance
                    best_match = i
            
            if best_match is not None:
                matched_detections.add(best_match)
                group = detection_groups[best_match]
                
                # Store previous x position for crossing detection
                prev_x = tracked_obj.x_center
                
                # Update tracked object
                tracked_obj.update_position(
                    group['center'][0],
                    group['center'][1],
                    group['bbox']
                )
                
                # Add all detected classes from this group
                for det in group['detections']:
                    tracked_obj.add_detected_class(det['class_name'])
                
                # Check for line crossing (RIGHT → LEFT)
                if not tracked_obj.crossed:
                    if prev_x > self.virtual_line_x and tracked_obj.x_center <= self.virtual_line_x:
                        # Object crossed from RIGHT to LEFT!
                        tracked_obj.crossed = True
                        tracked_obj.finalize_classification()
                        crossed_objects.append(tracked_obj)
                        
                        print(f"[AI] Object #{obj_id} CROSSED LINE!")
                        print(f"  Position: {prev_x} → {tracked_obj.x_center}")
                        print(f"  Detected classes: {tracked_obj.detected_classes}")
                        print(f"  Classification: {tracked_obj.classification_result}")
                        print(f"  Reason: {tracked_obj.classification_reason}")
        
        # Create new tracked objects for unmatched detections
        for i, group in enumerate(detection_groups):
            if i not in matched_detections:
                # Only track objects on the RIGHT side of line (before crossing)
                if group['center'][0] > self.virtual_line_x:
                    new_obj = TrackedObject(
                        self.next_object_id,
                        group['center'][0],
                        group['center'][1]
                    )
                    new_obj.bbox = group['bbox']
                    
                    # Add all detected classes
                    for det in group['detections']:
                        new_obj.add_detected_class(det['class_name'])
                    
                    self.tracked_objects[self.next_object_id] = new_obj
                    print(f"[AI] New object #{self.next_object_id} tracked at ({group['center'][0]}, {group['center'][1]})")
                    self.next_object_id += 1
        
        return crossed_objects
    
    def _group_detections_by_position(self, detections):
        """
        Group detections that are close together (same bottle with multiple labels)
        """
        if len(detections) == 0:
            return []
        
        groups = []
        used = set()
        
        for i, det1 in enumerate(detections):
            if i in used:
                continue
            
            # Start new group
            x1, y1, x2, y2 = det1['bbox']
            cx1 = (x1 + x2) / 2
            cy1 = (y1 + y2) / 2
            
            group_detections = [det1]
            group_boxes = [[x1, y1, x2, y2]]
            used.add(i)
            
            # Find nearby detections
            for j, det2 in enumerate(detections):
                if j in used:
                    continue
                
                x1_2, y1_2, x2_2, y2_2 = det2['bbox']
                cx2 = (x1_2 + x2_2) / 2
                cy2 = (y1_2 + y2_2) / 2
                
                # Check if centers are close
                distance = np.sqrt((cx1 - cx2)**2 + (cy1 - cy2)**2)
                if distance < 100:  # Within 100 pixels = same bottle
                    group_detections.append(det2)
                    group_boxes.append([x1_2, y1_2, x2_2, y2_2])
                    used.add(j)
            
            # Compute group bounding box (union of all boxes)
            all_x1 = [box[0] for box in group_boxes]
            all_y1 = [box[1] for box in group_boxes]
            all_x2 = [box[2] for box in group_boxes]
            all_y2 = [box[3] for box in group_boxes]
            
            group_bbox = [
                int(min(all_x1)),
                int(min(all_y1)),
                int(max(all_x2)),
                int(max(all_y2))
            ]
            
            group_center = [
                (group_bbox[0] + group_bbox[2]) / 2,
                (group_bbox[1] + group_bbox[3]) / 2
            ]
            
            groups.append({
                'detections': group_detections,
                'bbox': group_bbox,
                'center': group_center
            })
        
        return groups
    
    def draw_tracking(self, frame, tracked_objects_dict):
        """
        Draw tracking visualization on frame
        """
        for obj_id, obj in tracked_objects_dict.items():
            if obj.bbox is None:
                continue
            
            x1, y1, x2, y2 = obj.bbox
            
            # Color based on state
            if obj.crossed:
                if obj.classification_result == 'OK':
                    color = (0, 255, 0)  # Green for OK
                else:
                    color = (0, 0, 255)  # Red for NG
            else:
                color = (255, 255, 0)  # Yellow for tracking
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw object ID and center
            cv2.circle(frame, (int(obj.x_center), int(obj.y_center)), 5, color, -1)
            cv2.putText(
                frame,
                f"ID:{obj_id}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )
            
            # Draw detected classes
            classes_text = ", ".join(list(obj.detected_classes)[:3])  # Show first 3
            cv2.putText(
                frame,
                classes_text,
                (x1, y2 + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1
            )
            
            # Draw classification result if crossed
            if obj.crossed:
                cv2.putText(
                    frame,
                    f"{obj.classification_result}: {obj.classification_reason}",
                    (x1, y1 - 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2
                )
        
        return frame
