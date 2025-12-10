# 🎯 Hướng Dẫn NMS (Non-Maximum Suppression)

## ❓ NMS Là Gì?

**NMS (Non-Maximum Suppression)** là kỹ thuật loại bỏ các **bounding boxes chồng lấn** trong object detection.

### Vấn Đề Trước Khi Có NMS:
```
┌─────────────┐
│ Label-Defect│ ← Box 1 (conf: 0.41)
│   ┌─────────┼───┐
│   │ Filling-│   │ ← Box 2 (conf: 0.83) CHỒNG LẤN!
└───┼─────────┘   │
    │   Defect    │
    └─────────────┘
```

### Sau Khi Áp Dụng NMS:
```
┌─────────────────┐
│ Filling-Defect  │ ← GIỮ box có confidence CAO NHẤT
│   (conf: 0.83)  │   LOẠI BỎ box khác chồng lấn
└─────────────────┘
```

---

## ⚙️ Cách Hoạt Động

NMS hoạt động theo 3 bước:

### 1. Sắp Xếp Theo Confidence
```
Boxes: [Box1: 0.41, Box2: 0.83, Box3: 0.65]
Sorted: [Box2: 0.83, Box3: 0.65, Box1: 0.41]
```

### 2. Tính IoU (Intersection over Union)
```
IoU = Diện tích chồng lấn / Diện tích tổng

     ┌──────┐
     │      │ ← Box A
     │  ┌───┼──┐
     └──┼───┘  │ ← Box B
        └──────┘

IoU = (vùng chồng) / (A + B - vùng chồng)
```

### 3. Loại Bỏ Boxes
```
Nếu IoU > NMS_THRESHOLD:
    → LOẠI BỎ box có confidence THẤP hơn
```

---

## 🔧 Điều Chỉnh NMS_THRESHOLD

### Trong File `config.py`:

```python
NMS_THRESHOLD = 0.45  # Mặc định
```

### Ý Nghĩa Các Giá Trị:

| Threshold | Hành Vi | Khi Nào Dùng |
|-----------|---------|--------------|
| **0.3** | Loại bỏ nhiều boxes (strict) | Khi có quá nhiều boxes chồng lấn |
| **0.45** | Cân bằng (KHUYẾN NGHỊ) | Mặc định cho YOLO |
| **0.6** | Giữ lại nhiều boxes (lỏng) | Khi cần detect nhiều objects gần nhau |

---

## 🎯 Ví Dụ Thực Tế

### Trường Hợp 1: Quá Nhiều Boxes Chồng Lấn

**Triệu chứng**: 
- 3-4 boxes cùng detect 1 object
- Nhìn rối mắt

**Giải pháp**:
```python
# File config.py
NMS_THRESHOLD = 0.3  # GIẢM XUỐNG để loại bỏ nhiều hơn
```

### Trường Hợp 2: Thiếu Detections

**Triệu chứng**:
- Model bỏ qua một số objects
- Có 2 objects gần nhau nhưng chỉ detect được 1

**Giải pháp**:
```python
# File config.py
NMS_THRESHOLD = 0.6  # TĂNG LÊN để giữ lại nhiều hơn
```

### Trường Hợp 3: Cân Bằng (Mặc Định)

**Khi nào dùng**:
- Hầu hết các trường hợp
- YOLO mặc định dùng 0.45

```python
# File config.py
NMS_THRESHOLD = 0.45  # KHUYẾN NGHỊ
```

---

## 🧪 Test NMS

### Cách Test:

1. **Chạy hệ thống**:
```bash
python main.py
```

2. **Quan sát kết quả**:
   - Có bao nhiêu boxes?
   - Có chồng lấn không?

3. **Điều chỉnh**:
   - Mở `config.py`
   - Thay đổi `NMS_THRESHOLD`
   - Restart hệ thống

4. **So sánh**:
   - Trước: Nhiều boxes chồng lấn
   - Sau: Chỉ giữ box tốt nhất

---

## 📊 So Sánh NMS Thresholds

### Test Với Chai Coca-Cola:

#### NMS = 0.3 (Strict)
```
Detections: 3
✓ cap (0.95)
✓ filled (0.88)
✓ label (0.82)
```
→ **Ít boxes, rõ ràng**

#### NMS = 0.45 (Default)
```
Detections: 4
✓ cap (0.95)
✓ filled (0.88)
✓ label (0.82)
✓ coca (0.75)
```
→ **Cân bằng**

#### NMS = 0.6 (Loose)
```
Detections: 6
✓ cap (0.95)
✓ filled (0.88)
✓ label (0.82)
✓ label (0.70)  ← Duplicate!
✓ coca (0.75)
✓ filled (0.65) ← Duplicate!
```
→ **Nhiều boxes, có duplicate**

---

## 🔍 Debug NMS

### Xem Log Terminal:

Khi chạy hệ thống, terminal sẽ hiển thị:

```
[AI][NCNN] Detected: cap (conf: 0.95)
[AI][NCNN] Detected: filled (conf: 0.88)
[AI][NCNN] Detected: label (conf: 0.82)
```

**Nếu thấy duplicate**:
```
[AI][NCNN] Detected: label (conf: 0.82)
[AI][NCNN] Detected: label (conf: 0.41)  ← DUPLICATE!
```
→ Giảm `NMS_THRESHOLD` xuống **0.3**

**Nếu thiếu detections**:
```
[AI][NCNN] Detected: cap (conf: 0.95)
[AI][NCNN] Detected: filled (conf: 0.88)
# Thiếu label!
```
→ Tăng `CONFIDENCE_THRESHOLD` hoặc check camera

---

## 💡 Tips & Tricks

### Tip 1: Bắt Đầu Với Mặc Định
```python
NMS_THRESHOLD = 0.45  # Dùng mặc định trước
```

### Tip 2: Điều Chỉnh Từ Từ
```python
# Nếu quá nhiều boxes:
NMS_THRESHOLD = 0.4  # Giảm 0.05
NMS_THRESHOLD = 0.35 # Giảm thêm nếu cần
NMS_THRESHOLD = 0.3  # Min khuyến nghị

# Nếu thiếu boxes:
NMS_THRESHOLD = 0.5  # Tăng 0.05
NMS_THRESHOLD = 0.55 # Tăng thêm nếu cần
```

### Tip 3: Kết Hợp Với Confidence
```python
# Nếu vẫn chồng lấn:
CONFIDENCE_THRESHOLD = 0.4  # Tăng để lọc boxes yếu
NMS_THRESHOLD = 0.3         # Giảm để loại bỏ overlap
```

### Tip 4: Test Với Ảnh Thật
- Chụp ảnh chai thật
- Chạy hệ thống
- Xem kết quả
- Điều chỉnh

---

## 🎓 Thuật Toán NMS (Chi Tiết)

```python
def apply_nms(boxes, confidences, threshold):
    """
    boxes: List of [x1, y1, x2, y2]
    confidences: List of confidence scores
    threshold: NMS threshold (0.0 - 1.0)
    """
    # 1. Sắp xếp theo confidence (cao → thấp)
    sorted_indices = sorted(range(len(confidences)), 
                           key=lambda i: confidences[i], 
                           reverse=True)
    
    keep = []
    
    # 2. Duyệt qua từng box
    while sorted_indices:
        # Lấy box có confidence cao nhất
        current = sorted_indices[0]
        keep.append(current)
        
        # 3. Tính IoU với các box còn lại
        remaining = []
        for i in sorted_indices[1:]:
            iou = calculate_iou(boxes[current], boxes[i])
            
            # 4. Chỉ giữ box nếu IoU < threshold
            if iou < threshold:
                remaining.append(i)
        
        sorted_indices = remaining
    
    return keep
```

---

## 📝 Checklist

- [ ] Đọc hiểu NMS là gì
- [ ] Biết cách điều chỉnh `NMS_THRESHOLD` trong `config.py`
- [ ] Test với giá trị mặc định (0.45)
- [ ] Nếu có boxes chồng lấn → Giảm xuống 0.3
- [ ] Nếu thiếu detections → Tăng lên 0.6
- [ ] Quan sát log terminal để debug
- [ ] Check ảnh trong `captures/debug/`

---

## ✅ Kết Luận

**NMS** là công cụ quan trọng để:
- ✅ Loại bỏ bounding boxes chồng lấn
- ✅ Giữ lại box tốt nhất (confidence cao)
- ✅ Làm kết quả rõ ràng, dễ nhìn

**Giá trị khuyến nghị**:
- `NMS_THRESHOLD = 0.45` (mặc định YOLO)
- Điều chỉnh từ **0.3 - 0.6** tùy tình huống

**Nhớ**: NMS chỉ loại bỏ boxes **CÙNG CLASS** chồng lấn. Nếu 2 boxes khác class, cả 2 đều được giữ.

---

**Good luck!** 🍀

**Version**: 1.0  
**Date**: December 2025

