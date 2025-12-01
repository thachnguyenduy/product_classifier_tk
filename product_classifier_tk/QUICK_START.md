# Quick Start Guide

## 🚀 Chạy nhanh

```bash
cd product_classifier_tk
python main.py
```

## 📋 Các bước sử dụng

1. **Start Camera** → Bật camera
2. **Start Detection** → Bật AI nhận diện
3. Đưa chai vào trước camera
4. Xem kết quả:
   - 🟢 **GOOD** = Sản phẩm OK
   - 🔴 **BAD** = Có lỗi
5. **History** → Xem lịch sử

## 🎯 Kết quả phân loại

### ✅ GOOD (Sản phẩm tốt)
- Chỉ detect: `cap`, `coca`, `filled`, `label`
- Không có defect nào
- Box màu xanh

### ❌ BAD (Sản phẩm lỗi)
- Detect bất kỳ: `Cap-Defect`, `Filling-Defect`, `Label-Defect`, `Wrong-Product`
- Box màu đỏ dày
- Servo sẽ đẩy chai ra

## 🔧 Test nhanh

```bash
# Test camera + model
python test_camera_model.py
```

## 📊 Xem log

Mở console/terminal khi chạy app để thấy:
```
Running detection...
Found 3 boxes
  ✅ OK: cap (0.92)
  ✅ OK: coca (0.88)
  ❌ DEFECT: Filling-Defect (0.85)
→ Returning BAD
```

## ⚙️ Cài đặt

```bash
pip install -r requirements.txt
```

## 📖 Đọc thêm

- `README.md` - Hướng dẫn đầy đủ
- `CLASSIFICATION_LOGIC.md` - Chi tiết logic phân loại
- `requirements.txt` - Dependencies

## 🆘 Lỗi thường gặp

### Camera không mở được
```bash
python test_camera_model.py  # Test camera
```

### Model không detect
- Kiểm tra ánh sáng
- Kiểm tra khoảng cách camera
- Xem console log

### PyTorch lỗi (Windows)
```bash
pip uninstall torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

