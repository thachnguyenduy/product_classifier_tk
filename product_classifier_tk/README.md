# 🍾 Hệ Thống Kiểm Tra Lỗi Chai Coca-Cola

> **Continuous Flow Detection System with Tkinter GUI**

## 🚀 Quick Start

### 1. Cài Đặt

```bash
pip3 install -r requirements.txt
```

### 2. Upload Arduino Firmware

```bash
# Mở Arduino IDE
# File → Open → arduino/product_sorter.ino
# Upload to Arduino Uno
```

### 3. Kiểm Tra Hệ Thống

```bash
python3 test_system_components.py
```

### 4. Chạy Hệ Thống

```bash
# Cách 1: Dùng script (khuyến nghị)
bash run_tkinter.sh

# Cách 2: Trực tiếp
python3 main_continuous_flow_tkinter.py
```

---

## 📁 Cấu Trúc Dự Án

```
product_classifier_tk/
│
├── main_continuous_flow_tkinter.py   ⭐ FILE CHÍNH
├── run_tkinter.sh                    Script chạy nhanh
├── requirements.txt                   Dependencies
│
├── arduino/
│   ├── product_sorter.ino            Arduino firmware
│   └── README.md
│
├── model/
│   └── my_model.pt                   YOLOv8 model
│
├── captures/
│   └── defects/                      Ảnh chai lỗi tự động lưu
│
├── database/
│   └── products.db                   Database (optional)
│
├── 📚 DOCUMENTATION
├── README.md                          ← BẠN ĐANG Ở ĐÂY
├── README_VI.md                       Hướng dẫn tiếng Việt đầy đủ
├── INDEX.md                           Chỉ mục tất cả tài liệu
├── QUICK_START.md                     Setup nhanh 5 phút
├── CONTINUOUS_FLOW_README.md          Hướng dẫn chi tiết
├── CALIBRATION_GUIDE.md               Hướng dẫn hiệu chỉnh
├── TKINTER_VERSION.md                 Thông tin GUI
│
└── 🧪 TESTING
    ├── test_system_components.py      Test từng thành phần
    └── demo_voting_mechanism.py       Demo voting concept
```

---

## 🎯 Tính Năng

- ✅ **Continuous Flow** - Băng chuyền chạy liên tục, không dừng
- ✅ **Burst Capture** - Chụp 5 khung hình mỗi chai (50ms interval)
- ✅ **Voting Mechanism** - ≥3/5 frames phải đồng ý mới xác nhận lỗi
- ✅ **Time-Stamped Ejection** - Tính toán chính xác thời điểm gạt chai
- ✅ **IR Sensor Integration** - Tự động phát hiện chai
- ✅ **Tkinter GUI** - Giao diện ổn định, không lỗi Qt
- ✅ **Real-time Statistics** - Thống kê trực tiếp
- ✅ **Defect Image Saving** - Tự động lưu ảnh chai lỗi

---

## ⚙️ Cấu Hình Nhanh

Mở `main_continuous_flow_tkinter.py`, tìm class `Config`:

```python
class Config:
    # Serial
    SERIAL_PORT = "/dev/ttyACM0"  # hoặc "COM3" trên Windows
    
    # Camera
    CAMERA_INDEX = 0
    
    # Timing - ⚠️ PHẢI HIỆU CHỈNH!
    PHYSICAL_DELAY = 2.0  # giây
    
    # Voting
    VOTING_THRESHOLD = 3  # tối thiểu 3/5 frames
```

### Cách Tính PHYSICAL_DELAY

```
Khoảng cách (camera → servo): ___ cm
Tốc độ băng chuyền: ___ cm/s
→ PHYSICAL_DELAY = khoảng_cách / tốc_độ
```

**Chi tiết:** Xem [CALIBRATION_GUIDE.md](CALIBRATION_GUIDE.md)

---

## 🔌 Kết Nối Phần Cứng

### Arduino Uno

| Thiết Bị | Pin | Mô Tả |
|----------|-----|-------|
| **IR Sensor** | D2 | Active LOW (0 = có chai) |
| **Relay 5V** | D7 | LOW Trigger (LOW = BẬT) |
| **Servo Motor** | D9 | Gạt chai lỗi (0-180°) |

### Nguồn Điện

- Arduino: USB từ Raspberry Pi
- Servo: **Nguồn 5V riêng (1A+)** - không dùng chân 5V Arduino!
- Băng chuyền: Nguồn 12V riêng

---

## 🎨 Giao Diện

```
┌───────────────────────────────────────────┐
│  📹 VIDEO TRỰC TIẾP  │  ⚠️ CHAI LỖI      │
│  [Live camera feed]  │  [Defect image]   │
├───────────────────────────────────────────┤
│  ⚙️ ĐIỀU KHIỂN       │  📊 THỐNG KÊ      │
│  [▶️ BẬT CAMERA]     │  Tổng: 125        │
│  [▶️ CHẠY BĂNG]      │  Tốt: 118         │
│  [🔄 RESET]          │  Lỗi: 7           │
│  [⏹️ THOÁT]          │  Details...       │
└───────────────────────────────────────────┘
```

---

## 📚 Tài Liệu

| Tài Liệu | Nội Dung | Khi Nào Đọc |
|----------|----------|-------------|
| **[README_VI.md](README_VI.md)** 🇻🇳 | Hướng dẫn tiếng Việt đầy đủ | Đọc đầu tiên |
| **[INDEX.md](INDEX.md)** 📚 | Chỉ mục tất cả tài liệu | Tìm thông tin |
| **[QUICK_START.md](QUICK_START.md)** ⚡ | Setup nhanh 5 phút | Lần đầu cài đặt |
| **[CALIBRATION_GUIDE.md](CALIBRATION_GUIDE.md)** 🎯 | Hiệu chỉnh chi tiết | Trước triển khai |
| **[CONTINUOUS_FLOW_README.md](CONTINUOUS_FLOW_README.md)** 📘 | Manual đầy đủ | Tham khảo kỹ thuật |
| **[TKINTER_VERSION.md](TKINTER_VERSION.md)** 🖼️ | Thông tin GUI | Hiểu giao diện |

---

## 🐛 Xử Lý Sự Cố

### Camera không mở

```bash
ls /dev/video*
# Thử CAMERA_INDEX = 0, 1, 2...
```

### Arduino không kết nối

```bash
ls /dev/ttyACM*
sudo usermod -a -G dialout $USER
# Logout và login lại
```

### Gạt không đúng thời điểm

→ Hiệu chỉnh `PHYSICAL_DELAY` trong Config
→ Xem [CALIBRATION_GUIDE.md](CALIBRATION_GUIDE.md)

### Cảm biến IR không hoạt động

- Kiểm tra kết nối D2
- Test bằng Arduino Serial Monitor
- Wave tay trước sensor → phải thấy "DETECTED"

---

## 📊 Hiệu Năng Kỳ Vọng

Sau khi hiệu chỉnh đúng:

- ✅ Độ chính xác gạt: **≥95%**
- ✅ Độ chính xác AI: **≥90%**
- ✅ False positive: **≤5%**
- ✅ Uptime: **≥8 giờ**
- ✅ Throughput: **100+ chai/phút**

---

## 🛠️ Requirements

- **Hardware:**
  - Raspberry Pi 5 (hoặc 4, 3B+)
  - Arduino Uno
  - USB Webcam
  - IR Sensor (Active LOW)
  - Relay 5V (LOW Trigger)
  - Servo Motor
  - Băng chuyền DC 12V

- **Software:**
  - Python 3.8+
  - OpenCV
  - Ultralytics (YOLOv8)
  - PySerial
  - Tkinter (built-in)

---

## 📝 License

MIT License - Free to use and modify

---

## 🙏 Credits

**Refactored System** - December 2025  
**Original Project** - FINAL PROJECT 222

---

## 🎯 Next Steps

1. ✅ Đọc [README_VI.md](README_VI.md)
2. ✅ Chạy `test_system_components.py`
3. ✅ Đọc [CALIBRATION_GUIDE.md](CALIBRATION_GUIDE.md)
4. ✅ Hiệu chỉnh `PHYSICAL_DELAY`
5. ✅ Chạy `python3 main_continuous_flow_tkinter.py`

---

**Good luck with your bottle inspection system! 🍾🤖**

For detailed information, see: **[README_VI.md](README_VI.md)** 🇻🇳

