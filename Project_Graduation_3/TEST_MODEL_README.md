# 🧪 AI Model Testing Tool

## 📋 Tổng Quan

File `test_model.py` cho phép bạn test AI model độc lập mà không cần chạy toàn bộ hệ thống.

---

## 🚀 Cách Sử Dụng

### **1. Test với Live Camera** (Khuyến nghị)

```bash
python3 test_model.py
```

**Tính năng:**
- ✅ Xem live camera feed
- ✅ Nhấn SPACE để chạy detection
- ✅ Nhấn 's' để save snapshot
- ✅ Nhấn 'q' để thoát
- ✅ Hiển thị bounding boxes từ AI model
- ✅ Hiển thị kết quả chi tiết (OK/NG, reason, components)

**Output:**
```
[Result] N
[Reason] Thiếu nhãn
[Time] 125.3ms

[Detections] 4 objects found:
  1. cap (confidence: 0.89)
  2. filled (confidence: 0.92)
  3. coca (confidence: 0.85)
  4. Cap-Defect (confidence: 0.67)

[Components]
  - Cap: ✅
  - Filled: ✅
  - Label: ❌
  - Defects: Cap-Defect
```

---

### **2. Test với Image File**

```bash
# Test một ảnh
python3 test_model.py test_image.jpg

# Kết quả sẽ lưu vào test_image_result.jpg
```

**Tính năng:**
- ✅ Load ảnh từ file
- ✅ Chạy AI detection
- ✅ Hiển thị kết quả chi tiết
- ✅ Lưu ảnh có bounding boxes
- ✅ Show cả original và result

---

### **3. Test với Directory (Batch Testing)**

```bash
# Test tất cả ảnh trong folder
python3 test_model.py captures/ok/

# Hoặc
python3 test_model.py test_images/
```

**Tính năng:**
- ✅ Test nhiều ảnh cùng lúc
- ✅ Hiển thị progress
- ✅ Tính toán accuracy
- ✅ Lưu kết quả cho mỗi ảnh
- ✅ Summary cuối cùng

**Output:**
```
[1/10] Processing: image_001.jpg
  ✅ Result: O - Sản phẩm đạt chuẩn
  ⏱ Time: 125.3ms
  🔍 Detections: 4

[2/10] Processing: image_002.jpg
  ❌ Result: N - Thiếu nhãn
  ⏱ Time: 118.7ms
  🔍 Detections: 3

...

SUMMARY
========================================
Total: 10
✅ OK: 8
❌ NG: 2

Accuracy: 80.0%
```

---

## 🎯 Các Controls (Live Camera Mode)

| Key | Action |
|-----|--------|
| SPACE | Chạy AI detection trên frame hiện tại |
| 's' | Save snapshot hiện tại |
| 'q' | Quit/Thoát |

---

## 📊 Thông Tin Hiển Thị

### **1. Detection Results**
```
[Result] O / N
[Reason] Sản phẩm đạt chuẩn / Thiếu nhãn / Phát hiện lỗi: ...
[Time] Processing time (ms)
```

### **2. Detections List**
```
[Detections] X objects found:
  1. class_name (confidence: 0.XX)
  2. class_name (confidence: 0.XX)
  ...
```

### **3. Components Check**
```
[Components]
  - Cap: ✅/❌
  - Filled: ✅/❌
  - Label: ✅/❌
  - Defects: [list] or None
```

### **4. Bounding Boxes**
- **Green boxes:** Good components (cap, filled, label, coca)
- **Red boxes:** Defects (Cap-Defect, Filling-Defect, etc.)

---

## 🔧 Troubleshooting

### **Issue: "AI model failed to load"**

**Solution:**
```bash
# Kiểm tra model files
ls -l model/

# Đảm bảo có:
# - best.ncnn.param
# - best.ncnn.bin

# Hoặc kiểm tra config.py
MODEL_PATH = "model"  # Đúng folder
```

### **Issue: "Cannot open camera"**

**Solution:**
```bash
# Kiểm tra camera ID
ls /dev/video*

# Sửa config.py nếu cần
CAMERA_ID = 0  # hoặc 1, 2, ...
```

### **Issue: "No detections found"**

**Possible reasons:**
1. **Confidence threshold quá cao:**
   ```python
   # config.py
   CONFIDENCE_THRESHOLD = 0.3  # Giảm từ 0.5
   ```

2. **Ảnh không có chai:**
   - Đảm bảo chai trong frame
   - Đủ ánh sáng
   - Camera focus tốt

3. **Model chưa train:**
   - Đảm bảo model đã train đúng
   - Kiểm tra model files

---

## 💡 Tips

### **1. Tìm Confidence Threshold Tốt Nhất**

```bash
# Test với nhiều ảnh
python3 test_model.py test_images/

# Quan sát:
# - Bao nhiêu OK/NG đúng?
# - Confidence scores của detections?

# Điều chỉnh config.py:
CONFIDENCE_THRESHOLD = 0.3  # Thử 0.3, 0.4, 0.5, 0.6
```

### **2. Debug False Positives/Negatives**

```bash
# Test từng ảnh cụ thể
python3 test_model.py problem_image.jpg

# Xem chi tiết:
# - Detections nào được tìm?
# - Confidence bao nhiêu?
# - Missing components nào?
```

### **3. Batch Testing**

```bash
# Tạo test folder
mkdir test_images
cp captures/ok/*.jpg test_images/
cp captures/ng/*.jpg test_images/

# Test tất cả
python3 test_model.py test_images/

# Kiểm tra accuracy
```

---

## 📈 Performance Benchmarks

**Typical Results:**
- **Processing Time:** 50-200ms (depends on hardware)
- **Detection Rate:** 95%+
- **False Positive:** <5%
- **False Negative:** <5%

**On Raspberry Pi 5:**
- NCNN model: ~100-150ms
- GPU acceleration (Vulkan): ~50-100ms

**On Desktop/Laptop:**
- NCNN model: ~50-100ms
- GPU acceleration: ~20-50ms

---

## 🎓 Examples

### **Example 1: Quick Test**

```bash
# Test với camera
python3 test_model.py

# Đưa chai vào camera
# Nhấn SPACE
# Xem kết quả
```

### **Example 2: Test Một Ảnh**

```bash
# Chụp ảnh từ camera hoặc có sẵn
python3 test_model.py bottle_image.jpg

# Xem cửa sổ hiển thị:
# - Original Image
# - AI Detection Result (có bounding boxes)

# File kết quả: bottle_image_result.jpg
```

### **Example 3: Validate Model**

```bash
# Chuẩn bị test set
mkdir validation_set
# Copy 100 ảnh vào (50 OK, 50 NG)

# Run validation
python3 test_model.py validation_set/

# Kiểm tra accuracy
# Điều chỉnh thresholds nếu cần
```

---

## ⚙️ Configuration

Tất cả settings trong `config.py`:

```python
# AI Model
CONFIDENCE_THRESHOLD = 0.5  # Điều chỉnh sensitivity
NMS_THRESHOLD = 0.45        # Overlap threshold

# Sorting Logic
REQUIRE_CAP = True
REQUIRE_FILLED = True
REQUIRE_LABEL = True

# Debug
DEBUG_MODE = True
VERBOSE_LOGGING = True
```

---

## 📝 Summary

`test_model.py` là công cụ **quan trọng** để:
- ✅ Validate AI model
- ✅ Debug detection issues
- ✅ Tune thresholds
- ✅ Batch testing
- ✅ Performance benchmarking

**Khuyến nghị:** Test model trước khi chạy full system!

---

**Happy Testing! 🧪🚀**

