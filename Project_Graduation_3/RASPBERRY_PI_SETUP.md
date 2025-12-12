# Raspberry Pi 5 Setup & Optimization Guide
## Coca-Cola Bottle Sorting System v2.0

---

## 🚀 Quick Start (5 phút)

### Bước 1: Cài đặt dependencies hệ thống

```bash
sudo apt-get update
sudo apt-get install -y python3-opencv python3-serial python3-pil python3-tk python3-numpy
```

### Bước 2: Cài đặt NCNN

```bash
# Thử cài qua pip trước
pip3 install ncnn

# Kiểm tra
python3 -c "import ncnn; print('NCNN OK!')"
```

**Nếu pip install ncnn bị lỗi, build từ source:**

```bash
# Install build dependencies
sudo apt-get install -y git cmake build-essential

# Clone NCNN
cd ~
git clone https://github.com/Tencent/ncnn.git
cd ncnn

# Build (15-20 phút)
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release \
      -DNCNN_VULKAN=OFF \
      -DNCNN_PYTHON=ON \
      -DNCNN_BUILD_EXAMPLES=OFF \
      ..

make -j4
sudo make install

# Test
python3 -c "import ncnn; print('NCNN installed successfully!')"
```

### Bước 3: Chạy project

```bash
cd Project_Graduation_3
python3 main.py
```

---

## 🔧 Tối ưu hiệu suất

### 1. Tắt Debug Mode (QUAN TRỌNG!)

**Edit `config.py`:**

```python
# Tắt debug để tăng tốc độ
DEBUG_MODE = False
VERBOSE_LOGGING = False
```

**Hiệu quả:** +10-15% FPS

---

### 2. Điều chỉnh Resolution

**Nếu vẫn giật, giảm resolution:**

```python
# config.py
CAMERA_WIDTH = 640   # Giữ nguyên (tốt nhất)
CAMERA_HEIGHT = 480

# Hoặc giảm nếu cần:
# CAMERA_WIDTH = 480
# CAMERA_HEIGHT = 360
```

**Hiệu quả:** Resolution thấp hơn = nhanh hơn

---

### 3. Giảm Confidence Threshold

```python
# config.py
CONFIDENCE_THRESHOLD = 0.35  # Tăng để xử lý ít hơn
```

**Hiệu quả:** Ít detection hơn = nhanh hơn

---

### 4. Skip Frames (nếu vẫn lag)

```python
# config.py
SKIP_FRAMES = 1  # Xử lý mỗi frame thứ 2
```

**Hiệu quả:** +50% FPS nhưng có thể miss detections

---

### 5. Tối ưu Camera

```bash
# Kiểm tra camera devices
v4l2-ctl --list-devices

# List supported formats
v4l2-ctl -d /dev/video0 --list-formats-ext

# Chọn MJPEG format cho tốc độ tốt nhất (đã auto config trong code)
```

---

### 6. Overclock Raspberry Pi 5 (TÙY CHỌN)

**⚠️ CẨN THẬN: Cần cooling tốt!**

```bash
sudo nano /boot/config.txt

# Thêm vào cuối file:
over_voltage=6
arm_freq=2800

# Save và reboot
sudo reboot
```

**Hiệu quả:** +15-20% performance

---

## 📊 Benchmark & Performance

### Hiệu suất mong đợi trên Raspberry Pi 5:

| Configuration | FPS | Inference Time |
|--------------|-----|----------------|
| YOLO PyTorch | 5-8 | 150-200ms |
| **NCNN (optimized)** | **20-30** | **30-50ms** |
| NCNN + Skip frames | 40-50 | 20-30ms |

### Kiểm tra FPS thực tế:

Code sẽ in ra console khi `DEBUG_MODE = True`:

```
[AI] Inference: 35.2ms | Detections: 3
[AI] Inference: 32.8ms | Detections: 5
```

---

## 🐛 Troubleshooting

### Lỗi: "NCNN library not found"

**Giải pháp:**

```bash
# Kiểm tra Python path
python3 -c "import sys; print(sys.path)"

# Cài lại NCNN
pip3 install --user ncnn
```

---

### Lỗi: Camera lag hoặc giật

**Kiểm tra:**

1. **Camera format:**
```bash
v4l2-ctl -d /dev/video0 --list-formats-ext
```

Nếu hỗ trợ MJPEG → tốt (đã auto config)

2. **Buffer size:**
```python
# Đã config trong camera.py:
self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
```

3. **Reduce resolution:**
```python
# config.py
CAMERA_WIDTH = 480
CAMERA_HEIGHT = 360
```

---

### Lỗi: Model không load

**Kiểm tra files:**

```bash
ls -lh model/best_ncnn_model/
# Cần có:
# - model.ncnn.param
# - model.ncnn.bin
```

**Nếu thiếu, convert từ YOLO:**

```bash
# Install ultralytics
pip3 install ultralytics

# Convert
yolo export model=model/best.pt format=ncnn
```

---

### System vẫn giật sau khi tối ưu

**Checklist:**

- [ ] Tắt DEBUG_MODE
- [ ] Tắt VERBOSE_LOGGING
- [ ] Dùng NCNN (không phải YOLO)
- [ ] Resolution 640x480 hoặc thấp hơn
- [ ] Camera format MJPEG
- [ ] Buffer size = 1
- [ ] Close các app khác
- [ ] Đủ nguồn 5V 5A

**Nếu vẫn không được:**

```python
# config.py - Extreme optimization
SKIP_FRAMES = 2  # Process every 3rd frame
CONFIDENCE_THRESHOLD = 0.40
CAMERA_WIDTH = 480
CAMERA_HEIGHT = 360
DEBUG_MODE = False
VERBOSE_LOGGING = False
```

---

## ⚡ Performance Comparison

### TRƯỚC tối ưu (YOLO PyTorch):
```
- FPS: 5-8
- CPU: 85-95%
- Inference: 150-200ms
- Lag: Nhiều
- Frame drops: Thường xuyên
```

### SAU tối ưu (NCNN):
```
- FPS: 20-30 ✅
- CPU: 60-70% ✅
- Inference: 30-50ms ✅
- Lag: Không ✅
- Frame drops: Hiếm ✅
```

---

## 🎯 Recommended Settings cho Pi 5

### Cấu hình TỐI ƯU (balance quality/speed):

```python
# config.py
MODEL_PATH_NCNN = "model/best_ncnn_model"  # ✅ NCNN
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CONFIDENCE_THRESHOLD = 0.30
SKIP_FRAMES = 0  # Process all frames
DEBUG_MODE = False
VERBOSE_LOGGING = False
NCNN_NUM_THREADS = 4
```

### Cấu hình PERFORMANCE (maximum speed):

```python
# config.py
MODEL_PATH_NCNN = "model/best_ncnn_model"  # ✅ NCNN
CAMERA_WIDTH = 480
CAMERA_HEIGHT = 360
CONFIDENCE_THRESHOLD = 0.35
SKIP_FRAMES = 1  # Skip every other frame
DEBUG_MODE = False
VERBOSE_LOGGING = False
NCNN_NUM_THREADS = 4
```

---

## 💡 Tips & Tricks

### 1. Giảm nhiệt độ Pi

```bash
# Kiểm tra nhiệt độ
vcgencmd measure_temp

# Monitor real-time
watch -n 1 vcgencmd measure_temp
```

**Nhiệt độ tốt:** < 70°C  
**Cần cooling:** > 75°C

### 2. Monitor CPU usage

```bash
# Install htop
sudo apt-get install htop

# Run
htop
```

### 3. Kill unused processes

```bash
# List running processes
ps aux | grep python

# Kill if needed
pkill -f "process_name"
```

### 4. Disable GUI (headless mode) - EXTREME

```bash
# Chạy từ SSH, không dùng desktop
sudo systemctl set-default multi-user.target
sudo reboot
```

**Hiệu quả:** +20-30% performance  
**Lưu ý:** Mất GUI, chỉ dùng SSH

---

## 🔍 Monitoring Tools

### FPS Counter trong code:

```python
# Thêm vào main_window.py (nếu cần)
import time

self.fps_counter = 0
self.fps_start_time = time.time()

# Trong _update_video_loop():
self.fps_counter += 1
if time.time() - self.fps_start_time >= 1.0:
    print(f"[FPS] {self.fps_counter}")
    self.fps_counter = 0
    self.fps_start_time = time.time()
```

---

## 📦 Backup của settings gốc

Nếu muốn revert về YOLO PyTorch:

```python
# config.py
# Comment out NCNN settings
# MODEL_PATH_NCNN = "model/best_ncnn_model"

# Uncomment YOLO settings
MODEL_PATH_YOLO = "model/best.pt"

# Edit core/ai.py line ~8
from ultralytics import YOLO  # Thay vì import ncnn
```

---

## ✅ Checklist trước khi chạy

- [ ] NCNN đã cài đặt
- [ ] Model files tồn tại (model.ncnn.param, model.ncnn.bin)
- [ ] Camera kết nối
- [ ] Arduino kết nối (hoặc dummy mode)
- [ ] DEBUG_MODE = False
- [ ] Resolution phù hợp
- [ ] Nguồn đủ 5V 5A

---

## 🎓 Performance Tips cho Defense

Khi demo graduation:

1. **Test trước 30 phút:**
   - Chạy thử vài lần
   - Check FPS
   - Warm up system

2. **Tắt apps không cần:**
   ```bash
   # Close browser
   # Close file manager
   # Only keep terminal + demo
   ```

3. **Prepare dummy mode backup:**
   ```python
   # config.py
   USE_DUMMY_HARDWARE = True  # Nếu Arduino fail
   ```

4. **Record video backup** (nếu system crash)

---

## 📞 Support

**Nếu vẫn lag sau tất cả tối ưu:**

1. Check nhiệt độ Pi (có thể thermal throttling)
2. Check nguồn (phải 5V 5A official)
3. Test với resolution thấp hơn (320x240)
4. Consider skip frames = 2

**Expected final performance:**
- 20-30 FPS (smooth, no lag)
- Real-time detection
- Sẵn sàng cho defense

---

**Good luck! 🚀**

