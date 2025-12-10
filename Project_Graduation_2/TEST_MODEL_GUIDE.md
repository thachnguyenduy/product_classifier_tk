# 🧪 Hướng Dẫn Test Model

Chương trình test model real-time với camera và vẽ bounding boxes.

---

## 📋 Mục Đích

File `test_model_live.py` giúp bạn:
- ✅ Test model NCNN với camera thực
- ✅ Xem kết quả nhận diện real-time
- ✅ Vẽ bounding boxes với màu sắc khác nhau
- ✅ Hiển thị confidence score
- ✅ Đếm FPS và thời gian inference
- ✅ Chụp ảnh kết quả

---

## 🚀 Cách Sử Dụng

### 1. Cài Đặt Dependencies

```bash
pip install opencv-python numpy
# NCNN cần cài riêng (xem phần Installation bên dưới)
```

### 2. Chạy Chương Trình

```bash
cd Project_Graduation
python test_model_live.py
```

### 3. Điều Khiển

Khi chương trình đang chạy:

| Phím | Chức Năng |
|------|-----------|
| **Q** | Thoát chương trình |
| **S** | Chụp ảnh (lưu vào screenshot_XXX.jpg) |
| **SPACE** | Tạm dừng/Tiếp tục |

---

## 🎨 Màu Sắc Bounding Boxes

### Defects (Màu Đỏ)
- 🔴 **Cap-Defect** - Lỗi nắp
- 🔴 **Filling-Defect** - Lỗi đổ đầy
- 🔴 **Label-Defect** - Lỗi nhãn
- 🔴 **Wrong-Product** - Sản phẩm sai

### Components (Màu Xanh/Vàng)
- 🟢 **cap** - Nắp (xanh lá)
- 🔵 **coca** - Chai coca (cyan)
- 🟡 **filled** - Đã đổ đầy (vàng)
- 🟣 **label** - Nhãn (magenta)

---

## 📊 Thông Tin Hiển Thị

### Góc Trên Bên Trái
- **FPS**: Số khung hình/giây
- **Detections**: Số object phát hiện được
- **Controls**: Hướng dẫn phím

### Góc Trên Bên Phải
- **Legend**: Danh sách tất cả các class và màu sắc

### Góc Dưới Bên Trái
- **Inference Time**: Thời gian xử lý mỗi frame (ms)

### Trên Mỗi Object
- **Class Name**: Tên loại object
- **Confidence**: Độ tin cậy (0.00 - 1.00)
- **Bounding Box**: Khung màu quanh object

---

## ⚙️ Cấu Hình

Mở file `test_model_live.py` và chỉnh sửa:

### Thay Đổi Ngưỡng Confidence

```python
CONFIDENCE_THRESHOLD = 0.5  # Giảm để thấy nhiều detections hơn
```

### Thay Đổi Camera

```python
cap = cv2.VideoCapture(0)  # 0 = camera mặc định
# Thay bằng 1, 2,... cho camera khác
```

### Thay Đổi Độ Phân Giải Camera

```python
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)   # Width
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)   # Height
```

### Thay Đổi NMS Threshold

```python
NMS_THRESHOLD = 0.45  # Giảm để loại bỏ nhiều boxes trùng lặp hơn
```

---

## 🐛 Xử Lý Lỗi

### Lỗi: "NCNN not available"

**Nguyên nhân**: Chưa cài đặt NCNN

**Giải pháp**:

#### Trên Raspberry Pi:
```bash
# Cài từ source
git clone https://github.com/Tencent/ncnn.git
cd ncnn
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release -DNCNN_VULKAN=OFF ..
make -j4
sudo make install
```

#### Trên Windows:
- Download pre-built binary từ GitHub releases
- Hoặc build từ source với Visual Studio

### Lỗi: "Cannot open camera"

**Giải pháp**:
1. Kiểm tra camera đã cắm chưa
2. Thử camera ID khác: `cv2.VideoCapture(1)`
3. Test camera:
   ```python
   python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"
   ```

### Lỗi: "Model files not found"

**Giải pháp**:
1. Kiểm tra đường dẫn model:
   ```bash
   ls model/best_ncnn_model/
   ```
2. Đảm bảo có 2 files:
   - `model.ncnn.param`
   - `model.ncnn.bin`

### Lỗi: FPS thấp (<10 FPS)

**Giải pháp**:
1. Giảm độ phân giải camera
2. Tăng `num_threads` trong code:
   ```python
   net.opt.num_threads = 4  # Tăng lên 8
   ```
3. Bật Vulkan (nếu GPU hỗ trợ):
   ```python
   net.opt.use_vulkan_compute = True
   ```

---

## 📸 Chụp Ảnh Kết Quả

Nhấn phím **S** để chụp ảnh. File sẽ được lưu với tên:
- `screenshot_001.jpg`
- `screenshot_002.jpg`
- `screenshot_003.jpg`
- ...

Ảnh sẽ bao gồm:
- Frame camera gốc
- Tất cả bounding boxes
- Thông tin FPS, detections
- Legend các class

---

## 🎯 Test Cases Nên Thử

### 1. Test Với Chai OK
- Đặt chai Coca-Cola bình thường trước camera
- Kiểm tra xem model có detect:
  - ✅ `cap` (nắp)
  - ✅ `filled` (đã đổ đầy)
  - ✅ `label` (nhãn)
  - ✅ `coca` (chai)

### 2. Test Với Chai NG
- Dùng chai có lỗi hoặc giả lập:
  - Không có nắp → Nên detect thiếu `cap`
  - Nhãn bị rách → Nên detect `Label-Defect`
  - Chai sai loại → Nên detect `Wrong-Product`

### 3. Test Với Background
- Thử với background khác nhau
- Kiểm tra false positives

### 4. Test Với Lighting
- Thử với ánh sáng khác nhau
- Kiểm tra ảnh hưởng đến confidence

### 5. Test Với Góc Quay
- Xoay chai ở các góc độ khác nhau
- Kiểm tra model có robust không

---

## 📊 Đánh Giá Model

### Metrics Cần Quan Sát

1. **Detection Rate**
   - Model có phát hiện được tất cả objects không?
   - Có bị miss detection không?

2. **False Positives**
   - Model có detect nhầm không?
   - Có detect objects không tồn tại không?

3. **Confidence Scores**
   - Score có hợp lý không? (>0.7 là tốt)
   - Score thấp (<0.5) có thể là detection không chắc chắn

4. **Bounding Box Quality**
   - Box có khớp với object không?
   - Box có bị overlap quá nhiều không?

5. **Performance**
   - FPS có đủ cao không? (>15 FPS là OK)
   - Inference time có chấp nhận được không? (<100ms là tốt)

---

## 🔍 So Sánh Với Main System

### Điểm Khác Biệt

| Aspect | test_model_live.py | main.py (Full System) |
|--------|-------------------|----------------------|
| **Mục đích** | Test model | Sorting system hoàn chỉnh |
| **Hardware** | Chỉ cần camera | Camera + Arduino |
| **Output** | Vẽ boxes trên màn hình | Quyết định OK/NG, điều khiển servo |
| **Database** | Không lưu | Lưu vào SQLite |
| **UI** | OpenCV window | Tkinter GUI |
| **Speed** | Tối ưu cho real-time | Tối ưu cho accuracy |

### Khi Nào Dùng Tool Nào?

**Dùng `test_model_live.py` khi:**
- 🧪 Muốn test model nhanh
- 🎨 Muốn xem detection trực quan
- 🔍 Debug model performance
- 📊 Đánh giá accuracy
- 📸 Chụp ảnh demo

**Dùng `main.py` khi:**
- 🏭 Chạy hệ thống sorting thực tế
- 💾 Cần lưu history
- 📊 Cần statistics
- 🤖 Cần điều khiển Arduino
- 📈 Sản xuất thực tế

---

## 💡 Tips & Tricks

### 1. Tăng Tốc Độ
```python
# Giảm resolution camera
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Tăng threads
net.opt.num_threads = 8
```

### 2. Tăng Accuracy
```python
# Tăng confidence threshold
CONFIDENCE_THRESHOLD = 0.7  # Chỉ giữ detections chắc chắn
```

### 3. Debug Model
```python
# In ra tất cả detections (kể cả confidence thấp)
CONFIDENCE_THRESHOLD = 0.1
```

### 4. Chụp Ảnh Auto
```python
# Thêm vào main loop
if len(detections) > 0:
    cv2.imwrite(f"auto_capture_{time.time()}.jpg", frame)
```

### 5. Lưu Video
```python
# Thêm vào đầu main()
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('output.avi', fourcc, 20.0, (1280, 720))

# Trong loop
out.write(frame)

# Cuối chương trình
out.release()
```

---

## 📈 Performance Benchmarks

### Raspberry Pi 5
- **FPS**: 15-25 FPS (640x480)
- **Inference**: 50-80ms
- **Total Latency**: 80-120ms

### PC (Intel i5)
- **FPS**: 60+ FPS (1280x720)
- **Inference**: 10-20ms
- **Total Latency**: 20-40ms

### Raspberry Pi 4
- **FPS**: 8-15 FPS (640x480)
- **Inference**: 80-120ms
- **Total Latency**: 120-200ms

---

## 🎓 Code Explanation

### Main Components

1. **Model Loading**
   ```python
   net = load_model()  # Load NCNN model
   ```

2. **Frame Capture**
   ```python
   ret, frame = cap.read()  # Get frame from camera
   ```

3. **Preprocessing**
   ```python
   img = preprocess_frame(frame)  # Resize to 640x640, normalize
   ```

4. **Inference**
   ```python
   ex.input("in0", mat_in)
   ret, mat_out = ex.extract("out0")
   ```

5. **Post-processing**
   ```python
   detections = parse_yolo_output(mat_out)  # Parse YOLO format
   detections = apply_nms(detections)        # Remove duplicates
   ```

6. **Visualization**
   ```python
   frame = draw_detections(frame, detections)  # Draw boxes
   ```

---

## 🆘 Support

### Vấn Đề Với Code
- Đọc comments trong `test_model_live.py`
- Xem function docstrings
- Check error messages trong terminal

### Vấn Đề Với Model
- Kiểm tra model files có đúng không
- Test với `main.py` để so sánh
- Xem training metrics

### Vấn Đề Với Camera
- Test camera với OpenCV đơn giản
- Thử các camera ID khác nhau
- Check camera permissions

---

## ✅ Checklist Test Model

- [ ] Model files có trong `model/best_ncnn_model/`
- [ ] NCNN đã được cài đặt
- [ ] Camera hoạt động bình thường
- [ ] Chạy script không có lỗi
- [ ] Thấy bounding boxes trên các objects
- [ ] Confidence scores hợp lý (>0.5)
- [ ] FPS ổn định (>10)
- [ ] Có thể chụp screenshot
- [ ] Pause/Resume hoạt động
- [ ] Model detect đúng các classes

---

## 📝 Kết Luận

Tool `test_model_live.py` là công cụ tuyệt vời để:
- ✅ Kiểm tra model trước khi tích hợp
- ✅ Debug và tune parameters
- ✅ Demo cho người khác xem
- ✅ Đánh giá performance
- ✅ Chụp ảnh training data mới

**Chúc bạn test model thành công!** 🎉

---

**Phiên bản**: 1.0.0  
**Ngày**: December 2025  
**Tác giả**: Final Project Team

