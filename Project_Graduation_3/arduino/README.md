# Arduino Dual Sensor Mode

## 📁 Files trong thư mục này

### `sorting_control.ino` (CHÍNH)
Code chính để chạy hệ thống với 2 IR sensor và servo MG996R.

**Upload file này lên Arduino để chạy hệ thống thật.**

### `TEST_DUAL_SENSOR.ino` (TEST)
Code test nhanh để kiểm tra sensors và servo trước khi chạy hệ thống.

**Dùng để:**
- Test servo angle (IDLE/KICK)
- Test cả 2 sensors
- Điều chỉnh thời gian giữ

### `DUAL_SENSOR_GUIDE.md`
Hướng dẫn chi tiết:
- Cách kết nối phần cứng
- Cách calibration
- Troubleshooting
- Tips tối ưu

---

## 🚀 QUICK START

### 1. Test Setup (5 phút)
```
1. Upload TEST_DUAL_SENSOR.ino
2. Mở Serial Monitor (9600 baud)
3. Gửi 'T' để test servo
4. Gửi 'S' để xem sensors
5. Điều chỉnh góc servo nếu cần
```

### 2. Run Full System
```
1. Upload sorting_control.ino
2. Chạy Python: python main.py
3. Bấm START SYSTEM trên UI
4. Test với chai thật
```

---

## ⚙️ CẤU HÌNH QUAN TRỌNG

Trong `sorting_control.ino`, dòng 35-38:

```cpp
const int SERVO_IDLE = 0;         // Rack rút vào
const int SERVO_KICK = 90;        // Rack đẩy ra (ĐIỀU CHỈNH NẾU CẦN)
const int SERVO_KICK_DURATION = 2000;  // Giữ 2 giây
```

**Nếu rack đẩy không đủ**: Tăng `SERVO_KICK` (100, 110, 120...)  
**Nếu chai chưa kịp ngã**: Tăng `SERVO_KICK_DURATION` (2500, 3000...)

---

## 🔌 KẾT NỐI

```
Arduino Uno:
  Pin 2  → Sensor 1 (IR) [Đầu băng chuyền]
  Pin 3  → Sensor 2 (IR) [Gần servo]
  Pin 4  → Relay (Băng chuyền)
  Pin 9  → Servo MG996R Signal
  
Servo MG996R:
  VCC    → 6V nguồn ngoài (KHÔNG nối Arduino 5V)
  GND    → GND chung
  Signal → Arduino Pin 9
```

---

## ❓ TROUBLESHOOTING

| Vấn đề | Giải pháp |
|--------|-----------|
| Servo không đủ lực | Dùng nguồn 6V, không dùng Arduino 5V |
| Rack đẩy không đủ | Tăng `SERVO_KICK` |
| Chai chưa ngã | Tăng `SERVO_KICK_DURATION` |
| Đẩy sai chai | Kiểm tra vị trí Sensor 2 (8-10cm trước servo) |
| Queue full | Giảm tốc băng chuyền hoặc tăng `BUFFER_SIZE` |

---

## 📞 Support

Đọc chi tiết: `DUAL_SENSOR_GUIDE.md`

