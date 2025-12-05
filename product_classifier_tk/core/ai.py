"""YOLOv8 inference helper."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import numpy as np
from ultralytics import YOLO


class AIModel:
    """Wrapper around the Ultralytics YOLO model."""

    def __init__(self, model_path: Path) -> None:
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Missing model file: {self.model_path}")

        self.model = YOLO(str(self.model_path))

    def predict(self, frame: np.ndarray) -> Dict:
        """Run inference on a BGR frame."""
        print(f"Running YOLO inference on frame shape: {frame.shape}")
        results = self.model(frame, verbose=False)
        
        if not results:
            print("No results from YOLO model")
            return None

        result = results[0]
        detections = []
        
        # Required parts for GOOD product
        required_parts = {"cap", "filled", "label"}
        
        # Defect classes
        defect_classes = {"cap-defect", "filling-defect", "label-defect", "wrong-product"}

        if result.boxes is not None and len(result.boxes) > 0:
            boxes = result.boxes
            print(f"Found {len(boxes)} boxes")
            
            detected_parts = set()
            has_defect = False
            best_confidence = 0
            
            for idx in range(len(boxes)):
                bbox = boxes.xyxy[idx].cpu().numpy().astype(int).tolist()
                cls_id = int(boxes.cls[idx].item())
                conf = float(boxes.conf[idx].item())
                label = self.model.names.get(cls_id, f"class_{cls_id}")
                
                detection = {
                    "bbox": bbox,
                    "class_id": cls_id,
                    "confidence": conf,
                    "label": label,
                }
                detections.append(detection)
                best_confidence = max(best_confidence, conf)
                
                label_lower = label.lower()
                
                # Check for defects
                if any(defect in label_lower for defect in defect_classes):
                    has_defect = True
                    print(f"  ❌ DEFECT: {label} ({conf:.2f})")
                else:
                    # Track normal parts
                    if label_lower in required_parts:
                        detected_parts.add(label_lower)
                    print(f"  ✅ OK: {label} ({conf:.2f})")
            
            # Determine result
            if has_defect:
                print(f"→ BAD: Found defect(s)")
                return {"result": "BAD", "confidence": best_confidence, "detections": detections, "reason": "Phát hiện lỗi"}
            
            # Check if all required parts are present
            missing_parts = required_parts - detected_parts
            if missing_parts:
                print(f"→ BAD: Missing {missing_parts}")
                return {"result": "BAD", "confidence": best_confidence, "detections": detections, "reason": f"Thiếu: {', '.join(missing_parts)}"}
            
            print(f"→ GOOD: All parts OK")
            return {"result": "GOOD", "confidence": best_confidence, "detections": detections, "reason": "Đầy đủ"}

        print("→ No detections")
        return None

