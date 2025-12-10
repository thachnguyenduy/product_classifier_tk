# 📝 Ghi Chú Cập Nhật - Project Graduation

## ✨ Các Thay Đổi Mới

### 1. ✅ Sửa Lỗi UI - Các Nút Không Còn Biến Mất

**Vấn đề cũ**: Khi bấm "START SYSTEM", các nút View History và Exit bị ẩn.

**Đã sửa**:
- Tất cả các nút giờ luôn hiển thị
- Chỉ nút START/STOP bị disable/enable
- Grid layout được cấu hình đúng để tránh overlap

**File đã sửa**: `ui/main_window.py`

---

### 2. 📸 Chụp Nhiều Ảnh Khi Detect

**Tính năng mới**: Thay vì chụp 1 ảnh, giờ hệ thống chụp **5 ảnh** khi IR sensor detect chai.

**Quy trình mới**:
```
IR Sensor Detect → Chụp 5 ảnh (100ms giữa mỗi ảnh)
                 → AI phân tích tất cả 5 ảnh
                 → Chọn ảnh có nhiều detections nhất
                 → Kết hợp kết quả từ tất cả ảnh
                 → Hiển thị ảnh tốt nhất có bounding boxes
```

**File đã sửa**: `ui/main_window.py` - hàm `on_bottle_detected()`

---

### 3. 🎯 Vẽ Bounding Boxes Lên Ảnh

**Tính năng mới**: Ảnh hiển thị trong UI giờ có bounding boxes:
- **Màu Đỏ**: Defects (Cap-Defect, Filling-Defect, Label-Defect, Wrong-Product)
- **Màu Xanh**: Components (cap, coca, filled, label)
- Mỗi box có label với tên class và confidence score

**File đã sửa**: 
- `core/ai.py` - thêm hàm `draw_detections()`
- `ui/main_window.py` - hiển thị `annotated_image`

---

### 4. 🤖 Đổi Từ NCNN Sang YOLOv8 (.pt)

**Thay đổi lớn**: Hệ thống giờ dùng **YOLOv8** thay vì NCNN.

**Model mới**: `model/best.pt`

**Ưu điểm**:
- ✅ Dễ sử dụng hơn (chỉ cần 1 file .pt)
- ✅ Hỗ trợ tốt hơn từ ultralytics
- ✅ Dễ train và export
- ✅ Performance tốt

**File đã sửa**: 
- `core/ai.py` - viết lại toàn bộ để dùng YOLOv8
- `main.py` - đổi model_path thành `'model/best.pt'`
- `requirements.txt` - thêm ultralytics, torch

---

## 📦 Cài Đặt Dependencies Mới

Bạn cần cài đặt thêm các packages sau:

```bash
pip install ultralytics torch torchvision
```

Hoặc cài tất cả từ requirements.txt:

```bash
pip install -r requirements.txt
```

---

## 🚀 Cách Chạy Sau Khi Cập Nhật

### Bước 1: Cài Dependencies

```bash
cd Project_Graduation
pip install -r requirements.txt
```

### Bước 2: Đảm Bảo Model File Tồn Tại

Kiểm tra file `model/best.pt` có tồn tại:

```bash
ls model/best.pt  # Linux/Mac
dir model\best.pt  # Windows
```

### Bước 3: Chạy Hệ Thống

```bash
python main.py
```

---

## 🎯 Test Các Tính Năng Mới

### Test 1: UI Buttons
1. Chạy `python main.py`
2. Bấm "START SYSTEM"
3. **Kiểm tra**: Các nút "View History" và "Exit" vẫn hiển thị ✅

### Test 2: Multi-Frame Capture
1. Start system
2. Đặt chai trước IR sensor
3. **Xem terminal**: Sẽ thấy "Capturing 5 frames..."
4. **Kiểm tra**: Ảnh hiển thị có nhiều thông tin hơn

### Test 3: Bounding Boxes
1. Start system
2. Detect một chai
3. **Kiểm tra snapshot**: Phải thấy các boxes màu đỏ/xanh
4. **Kiểm tra labels**: Mỗi box có tên class và confidence

### Test 4: YOLOv8 Model
1. Terminal sẽ hiển thị: "Loading YOLOv8 model from model/best.pt..."
2. **Kiểm tra**: Không có lỗi về NCNN
3. **Kiểm tra detections**: Kết quả nhận diện chính xác

---

## 🐛 Troubleshooting

### Lỗi: "No module named 'ultralytics'"

**Giải pháp**:
```bash
pip install ultralytics
```

### Lỗi: "Model file not found"

**Giải pháp**:
1. Kiểm tra file `model/best.pt` có tồn tại
2. Đảm bảo đang chạy từ thư mục `Project_Graduation/`
3. Nếu không có file, copy từ training output

### Lỗi: PyTorch không cài được

**Giải pháp**:
```bash
# For CPU only
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# For GPU (CUDA 11.8)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### UI Buttons Vẫn Mất

**Giải pháp**:
1. Đảm bảo đã copy code mới từ `ui/main_window.py`
2. Restart ứng dụng
3. Check grid weights trong code

### Không Thấy Bounding Boxes

**Giải pháp**:
1. Kiểm tra model có load thành công không (xem terminal)
2. Giảm confidence threshold xuống 0.3 trong `core/ai.py`
3. Test với chai thật

---

## 📊 So Sánh Trước vs Sau

| Tính Năng | Trước | Sau |
|-----------|-------|-----|
| **Model** | NCNN (.param + .bin) | YOLOv8 (.pt) |
| **Số ảnh chụp** | 1 ảnh | 5 ảnh |
| **Bounding boxes** | Không | Có (đỏ/xanh) |
| **UI buttons** | Mất khi start | Luôn hiển thị |
| **Dependencies** | ncnn-python | ultralytics, torch |
| **Độ chính xác** | Tốt | Tốt hơn (5 ảnh) |

---

## 🔧 Cấu Hình Nâng Cao

### Thay Đổi Số Ảnh Chụp

Trong `ui/main_window.py`, hàm `on_bottle_detected()`:

```python
# Mặc định: 5 ảnh
num_frames = 5

# Có thể đổi thành 3 hoặc 7
num_frames = 3  # Nhanh hơn
num_frames = 7  # Chính xác hơn
```

### Thay Đổi Confidence Threshold

Trong `core/ai.py`, constructor `__init__`:

```python
self.confidence_threshold = 0.5  # Mặc định

# Giảm để detect nhiều hơn
self.confidence_threshold = 0.3

# Tăng để chỉ detect chắc chắn
self.confidence_threshold = 0.7
```

### Thay Đổi Delay Giữa Các Ảnh

Trong `ui/main_window.py`, hàm `on_bottle_detected()`:

```python
time.sleep(0.1)  # 100ms (mặc định)

# Có thể đổi
time.sleep(0.05)  # 50ms - chụp nhanh hơn
time.sleep(0.2)   # 200ms - chụp chậm hơn
```

---

## ✅ Checklist Sau Khi Update

- [ ] Cài đặt ultralytics và torch
- [ ] File `model/best.pt` tồn tại
- [ ] Chạy `python main.py` không có lỗi
- [ ] UI hiển thị đầy đủ buttons
- [ ] Start system, các nút vẫn hiển thị
- [ ] Test với chai, thấy bounding boxes
- [ ] Terminal hiển thị "Capturing 5 frames"
- [ ] Ảnh trong UI có boxes màu đỏ/xanh
- [ ] Detection chính xác

---

## 📞 Support

Nếu gặp vấn đề:

1. Check terminal output để xem lỗi
2. Kiểm tra file `model/best.pt` có đúng format không
3. Test với dummy mode:
   ```python
   # Trong main.py
   'use_dummy_camera': True,
   'use_dummy_hardware': True
   ```
4. Đọc error messages kỹ

---

## 🎉 Kết Luận

Hệ thống đã được nâng cấp với:
- ✅ UI ổn định hơn
- ✅ Độ chính xác cao hơn (5 ảnh)
- ✅ Visualization tốt hơn (bounding boxes)
- ✅ Model dễ sử dụng hơn (YOLOv8)

**Chúc bạn sử dụng thành công!** 🚀

---

**Phiên bản**: 2.0.0  
**Ngày cập nhật**: December 2025  
**Người cập nhật**: AI Assistant

