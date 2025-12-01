# Phân loại sản phẩm - Raspberry Pi 5 + Arduino

Hệ thống phân loại sản phẩm tự động sử dụng YOLOv8, Tkinter, Raspberry Pi 5, và Arduino Uno.

## 🔧 Phần Cứng

- **Raspberry Pi 5** (8GB) - Chạy YOLOv8, điều khiển hệ thống
- **Arduino Uno** - Điều khiển relay và servo
- **Camera Pi v2** (CSI) - Chụp ảnh sản phẩm
- **Relay 5V** - Bật/tắt băng chuyền
- **Servo SG90** - Gạt sản phẩm lỗi
- **Motor DC + Mạch điều tốc** - Băng chuyền

📖 **Chi tiết kết nối**: Xem `HARDWARE_SETUP.md`

## Cài đặt

### 1. Cài đặt Python packages

```bash
pip install opencv-python pillow ultralytics numpy pyserial
```

### 2. Trên Raspberry Pi

```bash
sudo apt install python3-opencv

# Thêm user vào group dialout (cho serial)
sudo usermod -a -G dialout $USER
# Logout và login lại
```

### 3. Upload Arduino code

```bash
cd arduino
# Dùng Arduino IDE hoặc arduino-cli
arduino-cli compile --fqbn arduino:avr:uno product_sorter.ino
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno product_sorter.ino
```

📖 **Chi tiết Arduino**: Xem `arduino/README.md`

### 3. Kiểm tra cấu trúc thư mục

```
product_classifier_tk/
├── main.py                 # Entry point
├── model/
│   └── my_model.pt        # YOLOv8 trained model
├── database/
│   └── products.db        # SQLite database
├── captures/              # Captured images (auto-created)
├── core/                  # Core modules
│   ├── camera.py         # Camera streaming
│   ├── ai.py             # YOLO inference
│   ├── database.py       # SQLite operations
│   └── hardware.py       # GPIO/Arduino control
└── ui/                    # Tkinter UI
    ├── main_window.py    # Main window
    └── history_window.py # History viewer
```

## Chạy ứng dụng

```bash
cd product_classifier_tk
python main.py
```

## Hướng dẫn sử dụng

### Các bước cơ bản:

1. **Start Camera** - Bật camera (mặc định camera 0)
2. **Start Detection** - Bật chế độ nhận diện AI
3. Camera sẽ liên tục detect và hiển thị:
   - Bounding box màu đỏ = BAD (phát hiện lỗi)
   - Bounding box màu xanh = GOOD (không có lỗi)
4. **Capture Product** - Lưu ảnh và kết quả vào database
5. **History** - Xem lịch sử các lần detect

### Menu Bar:

- **File → Exit** - Thoát ứng dụng
- **Tools → Hardware test** - Test relay + servo + Arduino
- **View → History** - Xem lịch sử phân loại

### Status Bar (dưới cùng):

- **FPS** - Tốc độ camera
- **Result** - Kết quả phân loại (GOOD/BAD)
- **Confidence** - Độ tin cậy (0-1)

## Xử lý lỗi

### ❌ "Unable to access camera"

**Nguyên nhân:**
- Camera không được kết nối
- Camera đang được dùng bởi app khác
- Quyền truy cập camera bị từ chối

**Giải pháp:**
```bash
# Kiểm tra camera có sẵn không (Linux/Pi)
ls /dev/video*

# Test camera bằng OpenCV
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"

# Nếu dùng nhiều camera, thử camera index khác
# Sửa trong core/camera.py: camera_index = 1
```

### ❌ Model không nhận diện được

**Kiểm tra:**

1. **Model có load thành công không?**
   - Xem console khi khởi động
   - Đảm bảo file `model/my_model.pt` tồn tại

2. **Detection có được bật không?**
   - Nhấn "Start Camera" trước
   - Sau đó nhấn "Start Detection"
   - Xem console có thông báo "Detection enabled" không

3. **Xem debug logs:**
   - Mở console/terminal khi chạy app
   - Khi nhấn "Start Detection", sẽ thấy:
     ```
     Detection enabled
     Running detection...
     Running YOLO inference on frame shape: (720, 1280, 3)
     Found X boxes
       Detection 0: label_name (0.85) at [x1, y1, x2, y2]
     ```

4. **Confidence threshold quá cao?**
   - Model mặc định detect tất cả boxes
   - Nếu không thấy gì, có thể objects không match với classes đã train

### ❌ PyTorch/Ultralytics lỗi DLL (Windows)

```bash
# Gỡ và cài lại PyTorch
pip uninstall torch torchvision torchaudio
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Hoặc dùng virtual environment
python -m venv venv
venv\Scripts\activate
pip install opencv-python pillow ultralytics numpy pyserial
```

### ❌ Hardware không hoạt động

**Trên Windows/Laptop:**
- GPIO/Serial sẽ **KHÔNG** hoạt động
- App vẫn chạy được (chỉ in thông báo ra console)
- Bình thường vì code đã xử lý fallback

**Trên Raspberry Pi:**
- Kiểm tra GPIO pins đúng chưa (mặc định: Relay=17, Servo=18)
- Kiểm tra Arduino serial port: `/dev/ttyACM0` hoặc `/dev/ttyUSB0`
- Chạy hardware test: Menu → Tools → Hardware test

## Cấu hình

### Thay đổi GPIO pins (core/hardware.py):

```python
pins = HardwarePins(
    relay_pin=17,  # Pin điều khiển relay
    servo_pin=18,  # Pin điều khiển servo
)
```

### Thay đổi Arduino serial port (core/hardware.py):

```python
hardware = HardwareController(serial_port="/dev/ttyUSB0")
```

### Thay đổi camera index (core/camera.py):

```python
camera = CameraStreamer(camera_index=1)  # Dùng camera thứ 2
```

## Debug mode

Để xem chi tiết quá trình nhận diện, xem console output:

```bash
python main.py

# Sẽ thấy các log:
# - Camera started/stopped
# - Detection enabled/stopped
# - Running detection...
# - Found X boxes
# - Detection result: {...}
```

## Export dữ liệu

1. Mở **View → History**
2. Chọn filter: **ALL** / **GOOD** / **BAD**
3. Nhấn **Export CSV**
4. Chọn đường dẫn lưu file

File CSV sẽ có format:
```csv
ID,Timestamp,Result,Confidence
1,2025-11-25T21:30:45,BAD,0.87
2,2025-11-25T21:31:12,GOOD,1.00
```

## Lưu ý quan trọng

### Logic phân loại:

Model được train với 8 classes:

**Sản phẩm tốt (GOOD):**
- `cap` - Nắp chai đầy đủ
- `coca` - Chai Coca-Cola
- `filled` - Nước được bơm đầy đủ
- `label` - Nhãn dán đầy đủ

**Sản phẩm lỗi (BAD):**
- `Cap-Defect` - Nắp chai bị lỗi/thiếu
- `Filling-Defect` - Nước không đầy đủ
- `Label-Defect` - Nhãn dán bị lỗi/thiếu
- `Wrong-Product` - Sản phẩm sai

**Quy tắc phân loại:**
1. Nếu phát hiện **BẤT KỲ** defect nào (`Cap-Defect`, `Filling-Defect`, `Label-Defect`, `Wrong-Product`) → **BAD**
2. Nếu chỉ phát hiện các parts bình thường (`cap`, `coca`, `filled`, `label`) → **GOOD**
3. Nếu không phát hiện gì → **GOOD** (không có sản phẩm)

**Hiển thị:**
- Bounding box **ĐỎ** dày = Defect (lỗi)
- Bounding box **XANH** mỏng = Normal parts (OK)

### Performance trên Raspberry Pi:

- YOLOv8 có thể chậm trên Pi (tùy model size)
- Nếu FPS thấp, xem xét:
  - Dùng model nhỏ hơn (yolov8n thay vì yolov8m/l/x)
  - Giảm resolution camera
  - Tăng khoảng thời gian giữa các lần detect

## Liên hệ/Báo lỗi

Nếu có vấn đề, kiểm tra:
1. Console output có lỗi gì không
2. Camera có hoạt động không
3. Model file có đúng không
4. PyTorch có cài đúng không

Debug logs sẽ giúp tìm nguyên nhân nhanh hơn.

