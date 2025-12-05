# 🍾 Coca-Cola Bottle Defect Detection System - Continuous Flow

## 📋 Tổng Quan

Hệ thống kiểm tra lỗi chai Coca-Cola tự động trên băng chuyền với cơ chế **continuous flow** (băng chuyền chạy liên tục, không dừng lại để chụp ảnh).

### Đặc Điểm Nổi Bật

- ✅ **Continuous Flow**: Băng chuyền không bao giờ dừng lại
- 📸 **Burst Capture**: Chụp 5 khung hình liên tục khi phát hiện chai
- 🗳️ **Voting Mechanism**: ≥3/5 frames cùng lỗi → Xác định lỗi
- ⏰ **Time-Stamped Ejection**: Tính toán chính xác thời điểm gạt chai lỗi
- 📊 **Real-time Dashboard**: Hiển thị live feed, thống kê, và hình ảnh lỗi
- 🧵 **Multi-threading**: Xử lý song song, không blocking

---

## 🔧 Cấu Hình Phần Cứng

### Master: Raspberry Pi 5
- **Model**: Raspberry Pi 5 (8GB RAM)
- **OS**: Raspberry Pi OS (Debian-based)
- **Tasks**: 
  - AI inference (YOLOv8)
  - Image processing
  - Dashboard display
  - Serial communication với Arduino

### Slave: Arduino Uno
- **Firmware**: `arduino/product_sorter.ino`
- **Kết nối**: USB Serial → Raspberry Pi
- **Tasks**:
  - Đọc cảm biến IR
  - Điều khiển relay (băng chuyền)
  - Điều khiển servo (gạt chai lỗi)

### Cảm Biến & Cơ Cấu

| Thiết bị | Pin | Mô tả | Đặc điểm |
|----------|-----|-------|----------|
| **IR Sensor** | D2 | Phát hiện chai | Active LOW (0 = có vật) |
| **Relay 5V** | D7 | Điều khiển băng chuyền 12V | LOW Trigger (LOW = ON) |
| **Servo Motor** | D9 | Gạt chai lỗi | 0° = gạt, 90° = nghỉ |
| **USB Camera** | USB | Chụp ảnh chai | 640x480 @ 30fps |

### Sơ Đồ Kết Nối

```
┌─────────────────────────────────────────┐
│         Raspberry Pi 5                  │
│  ┌──────────────────────────────────┐   │
│  │  - AI Model (YOLOv8)             │   │
│  │  - Dashboard (OpenCV)            │   │
│  │  - Serial Communication          │   │
│  └──────────────────────────────────┘   │
│                 │                        │
│           USB Serial                     │
│                 ↓                        │
└─────────────────────────────────────────┘
                  │
┌─────────────────────────────────────────┐
│          Arduino Uno                    │
│  ┌──────────────────────────────────┐   │
│  │  D2 ← IR Sensor (Active LOW)    │   │
│  │  D7 → Relay (LOW Trigger)       │   │
│  │  D9 → Servo Motor                │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
         │           │            │
         ↓           ↓            ↓
    IR Sensor    Relay 5V    Servo Motor
                    ↓
              Băng Chuyền
               12V DC Motor
```

---

## 🚀 Cài Đặt

### 1. Arduino Setup

**1.1. Upload Firmware**

```bash
# Mở Arduino IDE
# File → Open → arduino/product_sorter.ino
# Tools → Board → Arduino Uno
# Tools → Port → /dev/ttyACM0 (hoặc COM port trên Windows)
# Upload
```

**1.2. Kiểm Tra Kết Nối**

Mở Serial Monitor (115200 baud) và kiểm tra message:
```
Arduino Bottle Defect System Ready
Commands: START_CONVEYOR, STOP_CONVEYOR, REJECT, PING, STATUS
```

### 2. Raspberry Pi Setup

**2.1. Cài Đặt Dependencies**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
cd product_classifier_tk
pip3 install -r requirements.txt

# Nếu chưa có requirements.txt, cài thủ công:
pip3 install opencv-python numpy ultralytics pyserial pillow
```

**2.2. Kiểm Tra Camera**

```bash
# List available cameras
ls /dev/video*

# Test camera (nên thấy camera feed)
python3 -c "import cv2; cap = cv2.VideoCapture(0); ret, frame = cap.read(); print('Camera OK' if ret else 'Camera FAILED'); cap.release()"
```

**2.3. Kiểm Tra Serial Port**

```bash
# List serial devices
ls /dev/ttyACM* /dev/ttyUSB*

# Nên thấy /dev/ttyACM0 (Arduino)
# Nếu không có quyền:
sudo usermod -a -G dialout $USER
# Logout và login lại
```

**2.4. Chuẩn Bị Model**

Đảm bảo model YOLOv8 đã được trained và đặt đúng path:
```
product_classifier_tk/
  └── model/
      └── my_model.pt  ← YOLOv8 model file
```

---

## ⚙️ Calibration (Tinh Chỉnh)

**QUAN TRỌNG**: Trước khi chạy production, cần calibrate các thông số sau!

### 1. Serial Port

Mở `main_continuous_flow.py`, tìm `Config` class:

```python
class Config:
    # ==================== Serial Communication ====================
    SERIAL_PORT = "/dev/ttyACM0"  # ← THAY ĐỔI NẾU CẦN
    # SERIAL_PORT = "COM3"  # Uncomment for Windows
```

### 2. Camera Settings

```python
    # ====================== Camera Settings =======================
    CAMERA_INDEX = 0  # ← Thay đổi nếu dùng camera khác
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
```

### 3. Timing Parameters (QUAN TRỌNG NHẤT!)

```python
    # ================= Burst Capture Configuration ================
    BURST_COUNT = 5  # Số frame chụp mỗi chai
    BURST_INTERVAL = 0.05  # 50ms giữa các frame
    DELAY_SENSOR_TO_CAPTURE = 0.2  # 200ms từ sensor detect → chụp frame đầu
    
    # =============== Physical Timing (CALIBRATE!) =================
    PHYSICAL_DELAY = 2.0  # ← PHẢI CALIBRATE!
```

### 4. Cách Calibrate PHYSICAL_DELAY

`PHYSICAL_DELAY` là thời gian từ lúc chụp ảnh đến lúc chai đến vị trí gạt.

**Phương pháp đo:**

1. Đánh dấu 1 chai (vd: dán giấy màu)
2. Đo khoảng cách từ camera đến servo ejector (cm)
3. Đo tốc độ băng chuyền (cm/s)
4. Tính: `PHYSICAL_DELAY = distance / speed`

**Ví dụ:**
- Khoảng cách camera → ejector: 60 cm
- Tốc độ băng chuyền: 30 cm/s
- → `PHYSICAL_DELAY = 60 / 30 = 2.0` giây

**Test & Fine-tune:**
```python
PHYSICAL_DELAY = 2.0  # Bắt đầu với giá trị tính toán
```

Chạy thử nghiệm:
- Nếu gạt **sớm** (chai chưa đến) → TĂNG giá trị
- Nếu gạt **muộn** (chai đã qua) → GIẢM giá trị

Điều chỉnh từng 0.1s cho đến khi chính xác.

### 5. Voting Threshold

```python
    # =================== Voting Mechanism =========================
    VOTING_THRESHOLD = 3  # Tối thiểu 3/5 frames phải cùng lỗi
```

Điều chỉnh dựa trên độ chính xác mong muốn:
- `VOTING_THRESHOLD = 2`: Dễ dàng hơn (có thể false positive nhiều)
- `VOTING_THRESHOLD = 3`: Cân bằng (khuyên dùng)
- `VOTING_THRESHOLD = 4`: Nghiêm ngặt (có thể bỏ sót)

---

## 🎯 Chạy Hệ Thống

### Quy Trình Khởi Động

```bash
cd product_classifier_tk

# Chạy hệ thống
python3 main_continuous_flow.py
```

### Giao Diện Dashboard (1280x720)

```
┌─────────────────────────────────────────────────────┐
│  Live Feed (640x480)    │  Latest Defect (640x480)  │
│  [Real-time camera]     │  [Annotated defect image] │
│                         │                           │
├─────────────────────────────────────────────────────┤
│  Statistics (1280x240)                              │
│  Total Bottles: 125                                 │
│  Good: 118        Defects: 7                        │
│  Thiếu nắp: 2   Mức nước thấp: 3   ...             │
└─────────────────────────────────────────────────────┘
```

### Keyboard Controls

- **`q`**: Quit (thoát chương trình)
- **`r`**: Reset statistics (reset bộ đếm)

### Console Output

```
================================================================================
🍾 BOTTLE #5 DETECTED at 2025-12-05 14:32:15
================================================================================
📸 Burst capturing 5 frames...
   Frame 1/5 captured
   Frame 2/5 captured
   Frame 3/5 captured
   Frame 4/5 captured
   Frame 5/5 captured
🧠 Running AI detection with voting mechanism...
❌ DEFECT DETECTED: low_level
   Votes: 4/5
   Confidence: 87.32%
📅 Scheduled ejection for bottle #5 in 2.00s
💾 Defect image saved: captures/defects/defect_5_low_level_20251205_143215.jpg
================================================================================
```

---

## 🔄 Workflow Logic

### Quy Trình Hoạt Động

```
1. [System Start]
   ↓
2. Start Conveyor → Băng chuyền chạy liên tục
   ↓
3. [Wait for bottle...]
   ↓
4. IR Sensor detects bottle → Arduino sends "DETECTED"
   ↓
5. Pi receives DETECTED → Wait DELAY_SENSOR_TO_CAPTURE
   ↓
6. Burst Capture: Chụp 5 frames (interval: 50ms)
   ↓ (Record timestamp T₀)
   ↓
7. AI Processing (parallel, non-blocking):
   - Run YOLOv8 on all 5 frames
   - Voting: Count defect occurrences
   - If ≥3 frames detect same defect → DEFECT
   - Else → GOOD
   ↓
8. If DEFECT detected:
   - Schedule ejection at T₀ + PHYSICAL_DELAY
   - Update dashboard with defect image
   - Save image to disk
   ↓
9. [Timed Ejection Thread]
   - Wait until (T₀ + PHYSICAL_DELAY)
   - Send "REJECT" to Arduino
   - Arduino: Servo ejects bottle
   ↓
10. Update statistics
    ↓
11. [Loop back to step 3]
```

### Key Features

#### 1. Continuous Flow
- Băng chuyền **KHÔNG BAO GIỜ DỪNG** trong quá trình chụp/xử lý
- Chỉ servo gạt hoạt động, băng chuyền vẫn chạy

#### 2. Burst Capture
- Chụp 5 frames liên tục (50ms interval)
- Lấy được nhiều góc độ của chai
- Tăng độ tin cậy của voting

#### 3. Voting Mechanism
- Mỗi frame cho 1 "vote"
- Defect phải xuất hiện trong ≥3/5 frames
- Giảm false positive do góc chụp không tốt

#### 4. Time-Stamped Ejection
- Ghi nhận thời điểm capture: `T₀`
- Tính thời điểm ejection: `T_eject = T₀ + PHYSICAL_DELAY`
- Thread riêng đếm ngược và trigger đúng thời điểm
- **Không block** luồng xử lý camera

---

## 📁 Cấu Trúc File

```
product_classifier_tk/
│
├── arduino/
│   ├── product_sorter.ino          # Arduino firmware (REFACTORED)
│   └── README.md
│
├── captures/
│   └── defects/                    # Hình ảnh chai lỗi được lưu tại đây
│       ├── defect_1_no_cap_20251205_143210.jpg
│       ├── defect_2_low_level_20251205_143215.jpg
│       └── ...
│
├── model/
│   └── my_model.pt                 # YOLOv8 trained model
│
├── main_continuous_flow.py         # Main system (REFACTORED)
├── CONTINUOUS_FLOW_README.md       # This file
│
├── core/                           # Old modules (legacy)
│   ├── ai.py
│   ├── camera.py
│   ├── hardware.py
│   └── database.py
│
└── ui/                             # Old UI (legacy, not used)
    └── main_window.py
```

---

## 🛠️ Troubleshooting

### Problem 1: Camera không mở được

**Triệu chứng:**
```
❌ Failed to open camera 0
```

**Giải pháp:**
```bash
# Check camera availability
ls /dev/video*

# Test with different index
# Edit main_continuous_flow.py:
CAMERA_INDEX = 1  # Try 1, 2, etc.

# Or test manually:
python3 -c "import cv2; cap = cv2.VideoCapture(1); print(cap.isOpened())"
```

### Problem 2: Arduino không kết nối

**Triệu chứng:**
```
❌ Failed to connect to Arduino: [Errno 2] No such file or directory: '/dev/ttyACM0'
```

**Giải pháp:**
```bash
# Find correct port
ls /dev/ttyACM* /dev/ttyUSB*

# Add user to dialout group
sudo usermod -a -G dialout $USER
logout  # Then login again

# Edit Config.SERIAL_PORT in main_continuous_flow.py
```

### Problem 3: Gạt không đúng thời điểm

**Triệu chứng:**
- Servo gạt quá sớm (chai chưa đến)
- Servo gạt quá muộn (chai đã qua)

**Giải pháp:**
Calibrate `PHYSICAL_DELAY`:
```python
# Trong main_continuous_flow.py → Config class:
PHYSICAL_DELAY = 2.0  # Điều chỉnh giá trị này

# Gạt sớm → TĂNG (vd: 2.0 → 2.2)
# Gạt muộn → GIẢM (vd: 2.0 → 1.8)
```

### Problem 4: Model không detect được

**Triệu chứng:**
- Không có detection nào
- Accuracy thấp

**Giải pháp:**
```python
# Giảm confidence threshold
CONFIDENCE_THRESHOLD = 0.3  # Thay vì 0.5

# Hoặc check model path:
MODEL_PATH = "model/my_model.pt"  # Đảm bảo file tồn tại
```

### Problem 5: Too many false positives

**Triệu chứng:**
- Nhiều chai tốt bị nhận nhầm là lỗi

**Giải pháp:**
```python
# Tăng voting threshold
VOTING_THRESHOLD = 4  # Thay vì 3

# Hoặc tăng confidence threshold
CONFIDENCE_THRESHOLD = 0.6  # Thay vì 0.5
```

---

## 📊 Performance Tuning

### 1. Optimize AI Inference

**Sử dụng NCNN** (faster on Raspberry Pi):
```python
# Export model to NCNN format (on PC):
from ultralytics import YOLO
model = YOLO("my_model.pt")
model.export(format="ncnn")

# Update Config:
MODEL_PATH = "model/best_ncnn_model"
```

### 2. Adjust Burst Parameters

**Tăng tốc độ xử lý:**
```python
BURST_COUNT = 3  # Giảm từ 5 → 3 frames
VOTING_THRESHOLD = 2  # Adjust accordingly
```

**Tăng độ chính xác:**
```python
BURST_COUNT = 7  # Tăng lên 7 frames
VOTING_THRESHOLD = 4  # At least 4/7 must agree
```

### 3. Camera Resolution

**Giảm resolution để tăng FPS:**
```python
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240
```

---

## 🔐 Safety Notes

### 1. Emergency Stop

**Tại sao cần:**
- Nếu có sự cố, cần dừng băng chuyền ngay lập tức

**Cách dừng:**
- Nhấn `Ctrl+C` trong terminal
- System sẽ tự động:
  1. Stop conveyor
  2. Reset servo về vị trí nghỉ
  3. Close tất cả connections

**Emergency Hardware Switch:**
- Khuyến nghị: Lắp thêm nút dừng khẩn cấp (emergency stop button) cắt nguồn băng chuyền

### 2. Power Supply

**Arduino:**
- USB từ Pi đủ để chạy Arduino + đọc sensor
- **NHƯNG**: Servo cần nguồn riêng 5V (1A+)

**Relay:**
- Relay module cần nguồn 5V (từ Arduino/Pi)
- Băng chuyền 12V cần nguồn riêng

**Sơ đồ nguồn:**
```
[Power Supply 12V 2A] ──→ DC Motor (băng chuyền)
                      └─→ Buck Converter 12V→5V
                          └─→ Servo Motor

[Raspberry Pi USB]    ──→ Arduino Uno
                          └─→ Relay Module
```

---

## 📞 Contact & Support

**Developer:** Kỹ sư Thị giác máy tính & Hệ thống nhúng

**Troubleshooting Checklist:**
1. ✅ Arduino firmware uploaded?
2. ✅ Serial port correct?
3. ✅ Camera accessible?
4. ✅ Model file exists?
5. ✅ Dependencies installed?
6. ✅ PHYSICAL_DELAY calibrated?

---

## 📝 License

MIT License - Free to use and modify

---

**Good luck with your bottle inspection system! 🍾🤖**

