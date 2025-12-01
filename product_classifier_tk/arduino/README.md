# Arduino Product Sorter

Code Arduino để điều khiển phần cứng cho hệ thống phân loại sản phẩm.

## 📁 File

- `product_sorter.ino` - Main Arduino sketch

## 🔌 Kết Nối

### Pins:
- **D7** → Relay IN (điều khiển băng chuyền)
- **D9** → Servo Signal (gạt sản phẩm)
- **5V** → Relay VCC
- **GND** → Relay GND + Nguồn servo GND (chung)

### Serial:
- **Baud rate**: 115200
- **Port**: `/dev/ttyACM0` (trên Raspberry Pi)

## 📤 Upload Code

### Cách 1: Arduino IDE
1. Mở Arduino IDE
2. File → Open → `product_sorter.ino`
3. Tools → Board → Arduino Uno
4. Tools → Port → `/dev/ttyACM0` (hoặc COM port trên Windows)
5. Upload

### Cách 2: arduino-cli (trên Raspberry Pi)
```bash
# Cài arduino-cli
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh

# Compile
arduino-cli compile --fqbn arduino:avr:uno product_sorter.ino

# Upload
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno product_sorter.ino
```

## 📡 Các Lệnh

### Gửi từ Raspberry Pi:
```python
import serial
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)

# Bật băng chuyền
ser.write(b"RELAY_ON\n")

# Tắt băng chuyền
ser.write(b"RELAY_OFF\n")

# Gạt sản phẩm
ser.write(b"SERVO_LEFT\n")

# Trả servo về giữa
ser.write(b"SERVO_CENTER\n")

# Sequence tự động
ser.write(b"EJECT\n")

# Test kết nối
ser.write(b"PING\n")

# Lấy trạng thái
ser.write(b"STATUS\n")
```

### Response từ Arduino:
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

## 🧪 Test

### Test bằng Serial Monitor (Arduino IDE):
1. Tools → Serial Monitor
2. Set baud rate: 115200
3. Gõ lệnh và Enter:
   - `RELAY_ON`
   - `RELAY_OFF`
   - `SERVO_LEFT`
   - `SERVO_CENTER`
   - `EJECT`
   - `PING`
   - `STATUS`

### Test bằng Python:
```python
from core.hardware import HardwareController

hw = HardwareController()
hw.hardware_test()  # Test tất cả chức năng
```

## ⚙️ Cấu Hình

### Thay đổi pins:
```cpp
#define RELAY_PIN 7
#define SERVO_PIN 9
```

### Thay đổi vị trí servo:
```cpp
#define SERVO_CENTER 90   // Vị trí trung tâm
#define SERVO_LEFT 0      // Góc gạt (0-180)
#define SERVO_RIGHT 180   // Góc phải
```

### Thay đổi timing:
```cpp
void ejectBadProduct() {
  digitalWrite(RELAY_PIN, LOW);
  delay(300);  // Thời gian dừng băng chuyền
  
  sorter.write(SERVO_LEFT);
  delay(800);  // Thời gian gạt sản phẩm
  
  sorter.write(SERVO_CENTER);
  delay(500);  // Thời gian trả về
  
  digitalWrite(RELAY_PIN, HIGH);
}
```

### Thay đổi baud rate:
```cpp
Serial.begin(115200);  // Đổi thành 9600 nếu cần
```

## 🐛 Troubleshooting

### Servo không chạy:
- Kiểm tra GND chung giữa Arduino và nguồn servo
- Kiểm tra nguồn servo 5V đủ dòng (5A)
- Kiểm tra signal wire đúng pin D9

### Relay không bật:
- Kiểm tra LED trên relay module
- Kiểm tra VCC/GND đúng
- Kiểm tra IN pin đúng D7

### Serial không kết nối:
- Kiểm tra baud rate khớp (115200)
- Kiểm tra port đúng (`/dev/ttyACM0`)
- Đợi 2 giây sau khi mở serial (Arduino reset)

### Lệnh không hoạt động:
- Kiểm tra có gửi `\n` (newline) không
- Kiểm tra chữ hoa/thường (code tự động uppercase)
- Xem Serial Monitor để debug

## 📊 LED Indicators

Arduino Uno có LED built-in (pin 13):
- **Nhấp nháy nhanh** khi nhận serial data
- **Sáng liên tục** khi có lỗi

Relay module có LED:
- **Sáng** = Relay ON (băng chuyền chạy)
- **Tắt** = Relay OFF (băng chuyền dừng)

## 🔄 Workflow

1. Raspberry Pi chạy YOLOv8
2. Phát hiện sản phẩm BAD
3. Gửi lệnh `EJECT` qua serial
4. Arduino nhận lệnh
5. Thực hiện sequence:
   - Dừng băng chuyền
   - Gạt sản phẩm
   - Trả servo về
   - Chạy băng chuyền
6. Gửi response về Raspberry Pi
7. Lặp lại

## 📝 Notes

- Arduino reset mỗi khi mở serial connection
- Đợi 2 giây sau khi mở serial trước khi gửi lệnh
- Tất cả lệnh phải kết thúc bằng `\n`
- Response từ Arduino cũng kết thúc bằng `\n`
- Servo cần nguồn riêng (không dùng 5V Arduino)
- GND phải nối chung giữa tất cả thiết bị

