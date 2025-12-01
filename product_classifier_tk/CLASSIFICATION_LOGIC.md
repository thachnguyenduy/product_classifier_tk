# Logic Phân Loại Sản Phẩm

## Classes trong Model

Model YOLOv8 được train với 8 classes:

### ✅ Normal Parts (Sản phẩm tốt)
| Class | Ý nghĩa | Màu hiển thị |
|-------|---------|--------------|
| `cap` | Nắp chai đầy đủ, đúng vị trí | 🟢 Xanh |
| `coca` | Chai Coca-Cola | 🟢 Xanh |
| `filled` | Nước được bơm đầy đủ | 🟢 Xanh |
| `label` | Nhãn dán đầy đủ, đúng vị trí | 🟢 Xanh |

### ❌ Defects (Sản phẩm lỗi)
| Class | Ý nghĩa | Màu hiển thị |
|-------|---------|--------------|
| `Cap-Defect` | Nắp chai bị lỗi, thiếu, hoặc sai vị trí | 🔴 Đỏ |
| `Filling-Defect` | Nước không đầy đủ (thiếu hoặc tràn) | 🔴 Đỏ |
| `Label-Defect` | Nhãn dán bị lỗi, thiếu, hoặc sai vị trí | 🔴 Đỏ |
| `Wrong-Product` | Sản phẩm sai (không phải Coca-Cola) | 🔴 Đỏ |

## Quy Tắc Phân Loại

### Kịch bản 1: Sản phẩm hoàn hảo ✅
```
Detections: [cap, coca, filled, label]
→ Result: GOOD
→ Lý do: Tất cả các parts đều OK, không có defect
```

### Kịch bản 2: Thiếu nắp ❌
```
Detections: [Cap-Defect, coca, filled, label]
→ Result: BAD
→ Lý do: Phát hiện Cap-Defect
```

### Kịch bản 3: Nước không đầy ❌
```
Detections: [cap, coca, Filling-Defect, label]
→ Result: BAD
→ Lý do: Phát hiện Filling-Defect
```

### Kịch bản 4: Nhiều lỗi cùng lúc ❌
```
Detections: [Cap-Defect, coca, Filling-Defect, Label-Defect]
→ Result: BAD
→ Confidence: Lấy confidence cao nhất trong các defects
→ Lý do: Phát hiện 3 defects
```

### Kịch bản 5: Sản phẩm sai ❌
```
Detections: [Wrong-Product]
→ Result: BAD
→ Lý do: Không phải Coca-Cola
```

### Kịch bản 6: Không có sản phẩm ✅
```
Detections: []
→ Result: GOOD
→ Confidence: 1.0
→ Lý do: Không có chai nào trên băng chuyền
```

### Kịch bản 7: Chỉ có một vài parts ✅
```
Detections: [cap, coca]
→ Result: GOOD
→ Lý do: Các parts hiện có đều OK, không có defect
→ Note: Có thể chai chưa đi qua hết các trạm
```

## Code Implementation

### File: `core/ai.py`

```python
def predict(self, frame: np.ndarray) -> Dict:
    # 1. Chạy YOLO inference
    results = self.model(frame, verbose=False)
    
    # 2. Lấy tất cả detections
    detections = []
    defect_classes = {"cap-defect", "filling-defect", "label-defect", "wrong-product"}
    
    # 3. Kiểm tra từng detection
    has_defect = False
    for detection in detections:
        label_lower = detection["label"].lower()
        if any(defect in label_lower for defect in defect_classes):
            has_defect = True
    
    # 4. Quyết định kết quả
    if has_defect:
        return {"result": "BAD", ...}
    else:
        return {"result": "GOOD", ...}
```

## Hiển Thị Trên UI

### Bounding Boxes:
- **Defects**: Box đỏ dày (3px), text trắng trên nền đỏ
- **Normal parts**: Box xanh mỏng (2px), text trắng trên nền xanh

### Status Bar:
- **Result: GOOD** → Text màu xanh
- **Result: BAD** → Text màu đỏ
- **Confidence**: Hiển thị độ tin cậy cao nhất

### Database:
Mỗi lần detect sẽ lưu:
- Timestamp
- Result (GOOD/BAD)
- Confidence
- Tất cả detections (bao gồm cả normal parts và defects)

## Hardware Actions

### Khi phát hiện BAD:
1. Lưu vào database
2. Trigger servo để đẩy chai ra khỏi băng chuyền
3. Console log: "Bad product ejected"

### Khi phát hiện GOOD:
1. Lưu vào database
2. Không có action hardware
3. Chai tiếp tục đi trên băng chuyền

## Debug Tips

### Xem chi tiết detections:
Console sẽ hiển thị:
```
Running YOLO inference on frame shape: (720, 1280, 3)
Found 4 boxes
  ✅ OK: cap (0.92) at [100, 200, 150, 250]
  ✅ OK: coca (0.88) at [80, 180, 170, 400]
  ❌ DEFECT: Filling-Defect (0.85) at [90, 300, 160, 380]
  ✅ OK: label (0.90) at [95, 320, 155, 360]
→ Returning BAD (found 1 defect(s), best conf: 0.85)
```

### Nếu model detect sai:
1. Kiểm tra lighting (ánh sáng)
2. Kiểm tra góc camera
3. Kiểm tra khoảng cách từ camera đến sản phẩm
4. Có thể cần retrain model với data mới

## Tùy Chỉnh

### Thay đổi danh sách defects:
Sửa trong `core/ai.py`:
```python
defect_classes = {
    "cap-defect", 
    "filling-defect", 
    "label-defect", 
    "wrong-product",
    # Thêm defect mới ở đây
}
```

### Thêm confidence threshold:
```python
if conf < 0.5:  # Bỏ qua detections có confidence thấp
    continue
```

### Thay đổi màu sắc:
Sửa trong `ui/main_window.py`:
```python
color = (0, 0, 255) if is_defect else (0, 255, 0)  # BGR format
# (B, G, R) = (Blue, Green, Red)
```

