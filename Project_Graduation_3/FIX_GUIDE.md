# 🔧 Hướng Dẫn Fix Lỗi - Coca-Cola Sorting System

## ❌ Vấn Đề: Chai Bình Thường Nhưng Báo "HÀNG BỊ LỖI"

### Nguyên Nhân

Model không detect đủ 3 components: **cap**, **filled**, **label**

Thường thiếu **label** vì:
1. **Confidence threshold quá cao** → Model bỏ qua detection có confidence thấp
2. **Nhãn bị che khuất** → Camera không thấy rõ
3. **Ánh sáng không tốt** → Ảnh không rõ nét
4. **Góc camera sai** → Nhãn không nằm trong khung hình

---

## ✅ Các Giải Pháp

### 🎯 Giải Pháp 1: Giảm Confidence Threshold (KHUYẾN NGHỊ)

Đã tự động **giảm xuống 0.3** (từ 0.5)

**Cách điều chỉnh thêm**:

Mở file `config.py` và sửa:

```python
CONFIDENCE_THRESHOLD = 0.3  # Giảm xuống 0.2 nếu vẫn thiếu

# Thử các giá trị:
# 0.2 - Detect nhiều nhất (có thể bị false positive)
# 0.3 - Cân bằng (KHUYẾN NGHỊ)
# 0.5 - Chỉ detect chắc chắn
# 0.7 - Rất strict
```

### 📸 Giải Pháp 2: Cải Thiện Chất Lượng Ảnh

**A. Kiểm tra ánh sáng**:
```
✅ Đèn đủ sáng
✅ Không có bóng đổ
✅ Ánh sáng đều
❌ Ngược sáng
❌ Tối
```

**B. Kiểm tra góc camera**:
```
✅ Nhãn nằm trong khung hình
✅ Camera vuông góc với chai
✅ Khoảng cách phù hợp (30-50cm)
❌ Nhãn bị che
❌ Góc nghiêng quá
```

**C. Kiểm tra focus camera**:
```bash
# Test camera
python test_model_yolo.py
# Xem ảnh có rõ nét không
```

### 🔧 Giải Pháp 3: Điều Chỉnh Logic Sorting

Nếu label không quan trọng, có thể **bỏ qua yêu cầu** label:

Mở file `config.py`:

```python
# Yêu cầu components
REQUIRE_CAP = True      # Phải có nắp
REQUIRE_FILLED = True   # Phải đổ đầy
REQUIRE_LABEL = False   # KHÔNG bắt buộc phải có nhãn
```

Sau đó **update code** `core/ai.py` để sử dụng config này:

```python
# Trong hàm _apply_sorting_logic_internal
missing_components = []
if config.REQUIRE_CAP and not has_cap:
    missing_components.append('cap')
if config.REQUIRE_FILLED and not has_filled:
    missing_components.append('filled')
if config.REQUIRE_LABEL and not has_label:
    missing_components.append('label')
```

### 🎨 Giải Pháp 4: Train Lại Model (Lâu Dài)

Nếu model luôn thiếu label:

1. **Thu thập thêm data** của label
2. **Augment data** với các góc độ khác nhau
3. **Train lại model** với data mới
4. **Export** thành `best.pt`

---

## 🔍 Debug - Xem Chi Tiết

### Bước 1: Bật Debug Mode

File `config.py`:

```python
DEBUG_MODE = True
```

### Bước 2: Chạy Lại Hệ Thống

```bash
python main.py
```

### Bước 3: Xem Terminal Output

Khi bấm "CHẠY BẰNG TAY", terminal sẽ hiển thị:

```
[AI] Detected: cap (conf: 0.87)
[AI] Detected: filled (conf: 0.92)
[AI] Components check:
     - Cap: ✓
     - Filled: ✓
     - Label: ✗  ← THIẾU CÁI NÀY!
     - Defects: None
[AI] Result: NG (Missing: label)
```

→ Biết ngay **thiếu gì** và **tại sao NG**

---

## 🎯 Test Từng Bước

### Test 1: Xem Model Detect Được Gì

```bash
python test_model_yolo.py
```

- Đặt chai trước camera
- Nhấn phím **`-`** nhiều lần để giảm confidence về **0.2**
- Xem có thấy bounding box của **label** không

### Test 2: Chụp Nhiều Ảnh

Hệ thống giờ chụp **5 ảnh** thay vì 1 ảnh:

```python
# File config.py
NUM_CAPTURE_FRAMES = 5  # Tăng lên 7 nếu cần
FRAME_DELAY = 0.1       # 100ms giữa mỗi ảnh
```

### Test 3: Check Saved Images

Xem ảnh được lưu trong:
```
captures/ng/NG_*.jpg
```

Mở ảnh và kiểm tra:
- ✅ Có nhãn trong ảnh không?
- ✅ Nhãn có rõ nét không?
- ✅ Có bounding box nào gần nhãn không?

---

## 📊 Bảng Tham Khảo Confidence Threshold

| Threshold | Kết Quả | Khi Nào Dùng |
|-----------|---------|--------------|
| 0.2 | Detect rất nhiều | Khi model thiếu components |
| 0.3 | Cân bằng | **KHUYẾN NGHỊ** |
| 0.5 | Chỉ detect chắc chắn | Khi có quá nhiều false positive |
| 0.7 | Rất strict | Khi chỉ cần detect rõ ràng |

---

## ✅ Checklist Fix Lỗi

Làm theo thứ tự:

- [ ] 1. Giảm confidence threshold xuống **0.3** (hoặc 0.2)
- [ ] 2. Chạy lại và xem terminal debug output
- [ ] 3. Kiểm tra ánh sáng và góc camera
- [ ] 4. Test với `test_model_yolo.py`
- [ ] 5. Nếu vẫn thiếu label → Set `REQUIRE_LABEL = False`
- [ ] 6. Nếu vẫn không OK → Cần train lại model

---

## 🚨 Lỗi Thường Gặp Khác

### Lỗi 1: "No module named 'config'"

**Fix**:
```bash
# Đảm bảo file config.py có trong thư mục
ls config.py

# Nếu không có, tạo lại:
python -c "print('File config.py missing!')"
```

### Lỗi 2: Model Load Lâu

**Bình thường**: Lần đầu load model mất 5-10 giây

```
[AI] Loading YOLOv8 model from model/best.pt...
[AI] YOLOv8 model loaded successfully!
```

### Lỗi 3: Camera Không Hiển thị

**Fix**:
```python
# File config.py
CAMERA_ID = 0  # Thử đổi thành 1 hoặc 2
```

### Lỗi 4: Bounding Boxes Sai Vị Trí

**Nguyên nhân**: Ảnh bị resize sai

**Fix**: Đã tự động fix trong code mới

---

## 📞 Khi Nào Cần Hỗ Trợ

Nếu đã thử tất cả các cách trên mà vẫn lỗi:

1. **Chụp màn hình** terminal output (phần debug)
2. **Chụp ảnh** trong `captures/ng/`
3. **Ghi lại** các thông số đã thử:
   - Confidence threshold
   - Số ảnh chụp
   - Điều kiện ánh sáng

---

## 🎉 Kết Luận

**Giải pháp nhanh nhất**:
1. Giảm `CONFIDENCE_THRESHOLD = 0.2` trong `config.py`
2. Cải thiện ánh sáng
3. Điều chỉnh góc camera

**Nếu vẫn không được**:
- Set `REQUIRE_LABEL = False` để không bắt buộc phải có label

**Lâu dài**:
- Train lại model với nhiều data hơn

---

**Good luck!** 🍀

---

**File Updates**: December 2025  
**Version**: 2.1.0

