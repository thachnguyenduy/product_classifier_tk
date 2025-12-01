# Hướng Dẫn Kết Nối Phần Cứng

## 📋 Danh Sách Linh Kiện

### Phần chính:
- ✅ Raspberry Pi 5 (8GB)
- ✅ Arduino Uno
- ✅ Camera Raspberry Pi v2 (CSI)
- ✅ Motor DC + Mạch điều tốc PWM
- ✅ Relay 5V (1 kênh)
- ✅ Servo SG90 9g
- ✅ Nguồn 12V (cho motor)
- ✅ Nguồn tổ ong 5V - 5A (cho servo)
- ✅ Dây USB (Raspberry Pi ↔ Arduino)

## 🔌 Sơ Đồ Kết Nối

### 1. Raspberry Pi 5 ↔ Arduino Uno
```
Raspberry Pi 5 (USB)  ←→  Arduino Uno (USB)
                          
Giao tiếp: USB Serial
Port: /dev/ttyACM0
Baud rate: 115200
```

### 2. Camera ↔ Raspberry Pi
```
Camera v2 (CSI) → Cổng CSI trên Raspberry Pi 5
```

### 3. Servo SG90 ↔ Arduino + Nguồn Tổ Ong
```
Servo SG90:
  Signal (Vàng/Cam)  →  Arduino D9
  VCC (Đỏ)          →  Nguồn tổ ong +5V
  GND (Nâu/Đen)     →  Nguồn tổ ong GND

⚠️ QUAN TRỌNG: 
  GND nguồn tổ ong  →  GND Arduino (nối chung)
  
Nếu không nối chung GND → Servo không hoạt động!
```

### 4. Relay ↔ Arduino
```
Relay Module:
  VCC  →  Arduino 5V
  GND  →  Arduino GND
  IN   →  Arduino D7
```

### 5. Relay ↔ Nguồn 12V ↔ Mạch Điều Tốc
```
Adapter 12V (+) → Relay COM
Relay NO        → Mạch điều tốc IN+ (đỏ)
Adapter 12V (–) → Mạch điều tốc IN– (đen)

Mạch điều tốc:
  OUT+ / OUT–  →  Motor DC
```

## 🔧 Chi Tiết Kết Nối

### Arduino Uno Pinout:
```
D7  → Relay IN (điều khiển băng chuyền)
D9  → Servo Signal (gạt sản phẩm)
5V  → Relay VCC
GND → Relay GND + Nguồn tổ ong GND (chung)
USB → Raspberry Pi
```

### Relay Module:
```
COM (Common)     → Nguồn 12V (+)
NO (Normally Open) → Mạch điều tốc IN+
NC (Normally Closed) → Không dùng
IN (Signal)      → Arduino D7
VCC              → Arduino 5V
GND              → Arduino GND
```

### Mạch Điều Tốc PWM:
```
IN+  → Relay NO
IN–  → Nguồn 12V (–)
OUT+ → Motor DC (+)
OUT– → Motor DC (–)
PWM  → Điều chỉnh tốc độ motor (núm vặn)
```

## ⚡ Nguồn Điện

### Nguồn 12V (Adapter):
- Cấp cho: Motor DC (qua mạch điều tốc)
- Dòng: Tối thiểu 2A (tùy motor)

### Nguồn Tổ Ong 5V - 5A:
- Cấp cho: Servo SG90
- Lý do: Servo tiêu thụ dòng lớn, không dùng 5V từ Arduino

### Raspberry Pi 5:
- Nguồn riêng: USB-C PD 5V/5A
- Không dùng chung với motor/servo

### Arduino Uno:
- Nguồn từ USB (Raspberry Pi)
- Chỉ cấp điện cho relay (dòng nhỏ)

## 🔍 Kiểm Tra Kết Nối

### 1. Kiểm tra Arduino có kết nối không:
```bash
# Trên Raspberry Pi
ls /dev/ttyACM*
# Phải thấy: /dev/ttyACM0
```

### 2. Kiểm tra quyền truy cập:
```bash
sudo usermod -a -G dialout $USER
# Logout và login lại
```

### 3. Test serial connection:
```bash
python3 -c "import serial; s = serial.Serial('/dev/ttyACM0', 115200, timeout=1); print(s.readline())"
```

### 4. Upload Arduino code:
```bash
# Dùng Arduino IDE hoặc arduino-cli
arduino-cli compile --fqbn arduino:avr:uno arduino/product_sorter.ino
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno arduino/product_sorter.ino
```

### 5. Test từ Python:
```bash
cd product_classifier_tk
python3 -c "from core.hardware import HardwareController; h = HardwareController(); h.ping()"
```

## 🎯 Quy Trình Hoạt Động

### Khi phát hiện sản phẩm GOOD:
1. Băng chuyền tiếp tục chạy
2. Không có action nào

### Khi phát hiện sản phẩm BAD:
1. Raspberry Pi gửi lệnh `EJECT` tới Arduino
2. Arduino thực hiện sequence:
   - **Bước 1**: `RELAY_OFF` → Dừng băng chuyền (300ms)
   - **Bước 2**: `SERVO_LEFT` → Gạt sản phẩm (800ms)
   - **Bước 3**: `SERVO_CENTER` → Trả servo về (500ms)
   - **Bước 4**: `RELAY_ON` → Khởi động băng chuyền
3. Hệ thống tiếp tục hoạt động

## 📡 Các Lệnh Serial

### Từ Raspberry Pi → Arduino:
```
RELAY_ON      → Bật băng chuyền
RELAY_OFF     → Tắt băng chuyền
SERVO_LEFT    → Servo sang trái (gạt)
SERVO_CENTER  → Servo về giữa
SERVO_RIGHT   → Servo sang phải
EJECT         → Sequence tự động gạt sản phẩm
PING          → Test kết nối
STATUS        → Lấy trạng thái hiện tại
```

### Từ Arduino → Raspberry Pi:
```
OK: Conveyor started
OK: Servo moved to LEFT
Starting eject sequence...
  Step 1: Conveyor stopped
  Step 2: Servo ejecting product
  Step 3: Servo returned to center
  Step 4: Conveyor restarted
Eject sequence complete
```

## 🐛 Troubleshooting

### ❌ Arduino không kết nối:
```bash
# Kiểm tra device
ls -l /dev/ttyACM*
ls -l /dev/ttyUSB*

# Thử port khác
# Sửa trong core/hardware.py:
# serial_port="/dev/ttyUSB0"
```

### ❌ Servo không chạy:
- Kiểm tra GND nguồn tổ ong có nối chung GND Arduino không
- Kiểm tra nguồn 5V tổ ong có đủ dòng không (5A)
- Kiểm tra signal wire có cắm đúng D9 không

### ❌ Relay không bật:
- Kiểm tra LED trên relay có sáng không
- Kiểm tra VCC/GND có đúng không
- Kiểm tra IN có nối D7 không
- Dùng multimeter đo điện áp tại IN pin

### ❌ Motor không chạy:
- Kiểm tra nguồn 12V có đủ dòng không
- Kiểm tra relay có đóng mạch không (đo bằng multimeter)
- Kiểm tra mạch điều tốc có nguồn không
- Điều chỉnh núm PWM trên mạch điều tốc

### ❌ Permission denied:
```bash
sudo chmod 666 /dev/ttyACM0
# Hoặc
sudo usermod -a -G dialout $USER
```

## 🧪 Test Hardware

### Trong Python:
```python
from core.hardware import HardwareController

hw = HardwareController()

# Test đầy đủ
hw.hardware_test()

# Test từng chức năng
hw.start_conveyor()
time.sleep(2)
hw.stop_conveyor()

hw.servo_left()
time.sleep(1)
hw.servo_center()

hw.eject_bad_product()
```

### Trong GUI:
1. Chạy `python main.py`
2. Menu → Tools → Hardware test
3. Xem console output

## 📸 Camera Setup

### Enable camera:
```bash
sudo raspi-config
# Interface Options → Camera → Enable
```

### Test camera:
```bash
libcamera-hello
# Hoặc
python3 -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"
```

## ⚙️ Cấu Hình Tốc Độ

### Tốc độ băng chuyền:
- Điều chỉnh bằng núm vặn trên mạch điều tốc PWM
- Khuyến nghị: Tốc độ vừa phải để camera kịp chụp

### Timing servo:
- Sửa trong `arduino/product_sorter.ino`:
```cpp
delay(800);  // Thời gian gạt sản phẩm
delay(500);  // Thời gian trả về
```

### Vị trí servo:
```cpp
#define SERVO_LEFT 0      // Góc gạt (0-180)
#define SERVO_CENTER 90   // Vị trí trung tâm
#define SERVO_RIGHT 180   // Góc phải (nếu cần)
```

## 📝 Checklist Trước Khi Chạy

- [ ] Arduino đã upload code `product_sorter.ino`
- [ ] USB Arduino ↔ Raspberry Pi đã cắm
- [ ] Camera CSI đã cắm vào Raspberry Pi
- [ ] Servo signal → D9, VCC → nguồn tổ ong, GND chung
- [ ] Relay IN → D7, VCC → 5V Arduino, GND chung
- [ ] Nguồn 12V đã nối qua relay vào mạch điều tốc
- [ ] Motor đã nối vào OUT của mạch điều tốc
- [ ] Tất cả GND đã nối chung
- [ ] Test `ls /dev/ttyACM0` thấy device
- [ ] Test `python3 test_camera_model.py` pass
- [ ] Test hardware: Menu → Tools → Hardware test

## 🚀 Sẵn Sàng!

Sau khi hoàn thành checklist:
```bash
cd product_classifier_tk
python main.py
```

Chúc may mắn với đồ án! 🎓

