# Hướng Dẫn Setup Camera Raspberry Pi v2

## ⚠️ Vấn Đề Thường Gặp

Nếu `rpicam-hello` chạy được nhưng code Python không, nguyên nhân là:
- Raspberry Pi OS mới dùng `libcamera` thay vì V4L2
- OpenCV không tương thích trực tiếp với `libcamera`
- **Giải pháp**: Dùng thư viện `picamera2`

## ✅ Giải Pháp: Sử dụng picamera2

### Bước 1: Cài đặt picamera2

```bash
# Cập nhật system
sudo apt update
sudo apt upgrade -y

# Cài picamera2 (nếu chưa có)
sudo apt install -y python3-picamera2

# Kiểm tra
python3 -c "from picamera2 import Picamera2; print('✅ picamera2 OK')"
```

### Bước 2: Enable camera

```bash
# Mở raspi-config
sudo raspi-config

# Chọn:
# 3. Interface Options
# → I1 Camera
# → Yes
# → Finish
# → Reboot
```

### Bước 3: Test camera

```bash
# Test với rpicam-hello
rpicam-hello --timeout 5000

# Test với Python
cd product_classifier_tk
python3 test_picamera2.py
```

### Bước 4: Chạy app

```bash
python3 main.py
```

## 🔍 Troubleshooting

### ❌ "picamera2 not installed"

```bash
sudo apt install -y python3-picamera2
```

### ❌ "Camera not detected"

```bash
# Kiểm tra camera
vcgencmd get_camera

# Phải thấy: supported=1 detected=1
```

Nếu `detected=0`:
1. Tắt Pi: `sudo shutdown -h now`
2. Kiểm tra cáp camera cắm chặt
3. Bật lại và test

### ❌ "Failed to open camera"

```bash
# Kiểm tra process nào đang dùng camera
sudo lsof /dev/video*

# Kill process nếu cần
sudo killall rpicam-hello libcamera-hello
```

### ❌ "Permission denied"

```bash
# Thêm user vào group video
sudo usermod -a -G video $USER

# Logout và login lại
```

## 📊 So Sánh Methods

| Method | Raspberry Pi OS | Tốc độ | Độ ổn định |
|--------|----------------|--------|------------|
| **picamera2** | ✅ Bullseye+ | ⭐⭐⭐ | ⭐⭐⭐ |
| OpenCV V4L2 | ⚠️ Cũ | ⭐⭐ | ⭐ |
| GStreamer | ⚠️ Phức tạp | ⭐⭐ | ⭐⭐ |

**→ Khuyến nghị: Dùng picamera2**

## 🎯 Code Đã Được Cập Nhật

File `core/camera.py` giờ tự động:
1. Detect Raspberry Pi
2. Thử dùng `picamera2` trước (nếu có)
3. Fallback sang OpenCV V4L2
4. Fallback sang OpenCV default

## 📝 Kiểm Tra Hoạt Động

### Console output khi chạy:

```
🎥 Opening camera (Raspberry Pi=True, picamera2=True)...
  Using picamera2 for Pi Camera Module v2...
  ✅ picamera2 success! Frame shape: (720, 1280, 3)
```

Hoặc nếu không có picamera2:

```
🎥 Opening camera (Raspberry Pi=True, picamera2=False)...
  Using OpenCV VideoCapture...
  Trying V4L2 backend...
  ✅ V4L2 success! Frame shape: (720, 1280, 3)
```

## 🚀 Quick Test

```bash
# Test 1: rpicam-hello
rpicam-hello --timeout 5000

# Test 2: picamera2
python3 test_picamera2.py

# Test 3: Full app
python3 test_camera_model.py

# Test 4: GUI
python3 main.py
```

## 📖 Tài Liệu Tham Khảo

- [Picamera2 Manual](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf)
- [Raspberry Pi Camera](https://www.raspberrypi.com/documentation/accessories/camera.html)
- [libcamera](https://libcamera.org/)

## ✅ Checklist

- [ ] `sudo apt install -y python3-picamera2`
- [ ] `sudo raspi-config` → Enable camera
- [ ] Reboot
- [ ] `rpicam-hello --timeout 5000` hoạt động
- [ ] `python3 test_picamera2.py` pass
- [ ] `python3 main.py` → Start Camera hoạt động

## 🎉 Done!

Sau khi hoàn thành checklist, camera sẽ hoạt động hoàn hảo với code!

