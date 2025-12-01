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
            return {"result": "GOOD", "confidence": 1.0, "detections": []}

        result = results[0]
        detections = []
        
        # Defect classes that indicate BAD product
        defect_classes = {
            "cap-defect", "filling-defect", "label-defect", "wrong-product"
        }

        if result.boxes is not None and len(result.boxes) > 0:
            boxes = result.boxes
            print(f"Found {len(boxes)} boxes")
            
            has_defect = False
            defect_detections = []
            
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
                
                # Check if this is a defect
                label_lower = label.lower()
                if any(defect in label_lower for defect in defect_classes):
                    has_defect = True
                    defect_detections.append(detection)
                    print(f"  ❌ DEFECT: {label} ({conf:.2f}) at {bbox}")
                else:
                    print(f"  ✅ OK: {label} ({conf:.2f}) at {bbox}")
            
            # If any defect is found, product is BAD
            if has_defect:
                best_conf = max(det["confidence"] for det in defect_detections)
                print(f"→ Returning BAD (found {len(defect_detections)} defect(s), best conf: {best_conf:.2f})")
                return {"result": "BAD", "confidence": best_conf, "detections": detections}
            else:
                # All detections are normal parts (cap, coca, filled, label)
                best_conf = max(det["confidence"] for det in detections)
                print(f"→ Returning GOOD (all {len(detections)} parts are OK, best conf: {best_conf:.2f})")
                return {"result": "GOOD", "confidence": best_conf, "detections": detections}

        print("→ No detections found, returning GOOD (no product)")
        return {"result": "GOOD", "confidence": 1.0, "detections": []}

