# HƯỚNG DẪN SỬ DỤNG HỆ THỐNG DUAL SENSOR

## 🔧 CẤU HÌNH PHẦN CỨNG

### Kết nối Arduino:
- **Sensor 1 (IR)**: Pin 2 → Phát hiện chai ở đầu băng chuyền (trước camera)
- **Sensor 2 (IR)**: Pin 3 → Phát hiện chai gần servo (nơi đẩy)
- **Relay Module**: Pin 4 → Điều khiển băng chuyền
- **Servo MG996R**: Pin 9 → Linear actuator đẩy chai

### Servo MG996R Specs:
- Torque: 11 kg·cm (4.8V), 13 kg·cm (6V)
- Speed: 0.17s/60° (4.8V), 0.14s/60° (6V)
- Góc quay: 0-180°
- Điện áp: 4.8-7.2V

---

## 🚀 WORKFLOW MỚI (Không cần TRAVEL_TIME)

### Luồng hoạt động:
1. **Sensor 1** phát hiện chai → Gửi 'D' cho Raspberry Pi
2. **Raspberry Pi** chạy AI → Trả về 'O' (OK) hoặc 'N' (NG)
3. Chai được đánh dấu trong queue: `OK` hoặc `NG pending`
4. **Sensor 2** phát hiện chai gần servo:
   - Nếu `NG pending` → **ĐẨY NGAY**
   - Nếu `OK` → **CHO QUA**

### Ưu điểm:
✅ Không cần đo TRAVEL_TIME  
✅ Không phụ thuộc tốc độ băng chuyền  
✅ Chính xác 100% (phản ứng theo vị trí thực tế)  
✅ Hoạt động với nhiều chai cùng lúc (queue buffer)

---

## ⚙️ CALIBRATION (Hiệu chỉnh)

### Bước 1: Kiểm tra servo angle
```cpp
// Trong file sorting_control.ino, dòng 35-37:
const int SERVO_IDLE = 0;         // Rack rút vào (không chặn)
const int SERVO_KICK = 90;        // Rack đẩy ra (chặn chai)
```

**Cách test:**
1. Upload code lên Arduino
2. Mở Serial Monitor (9600 baud)
3. Quan sát rack khi khởi động:
   - Rack phải rút vào hoàn toàn (IDLE = 0)
4. Khi có chai NG, rack phải đẩy ra đủ để chặn chai

**Điều chỉnh SERVO_KICK:**
- Nếu rack đẩy **KHÔNG ĐỦ**: tăng lên (ví dụ: 100, 110, 120)
- Nếu rack đẩy **QUÁ MỨC**: giảm xuống (ví dụ: 80, 70, 60)
- **Lưu ý**: MG996R quay 0-180°, chọn góc vừa đủ chặn chai

### Bước 2: Điều chỉnh thời gian giữ
```cpp
// Dòng 38:
const int SERVO_KICK_DURATION = 2000;  // 2 giây
```

**Cách test:**
1. Cho chai NG chạy qua
2. Quan sát:
   - Chai có ngã ra khỏi băng chuyền không?
   - Rack có kịp rút về trước chai tiếp theo không?

**Điều chỉnh:**
- Chai **CHƯA KỊP NGÃ**: tăng lên (2500, 3000 ms)
- Rack **CHẶN CHAI TIẾP THEO**: giảm xuống (1500, 1000 ms)
- **Gợi ý**: Với chai 330ml, 2000ms thường đủ

### Bước 3: Đặt vị trí Sensor 2
**Quan trọng**: Sensor 2 phải đặt đúng vị trí!

```
[Sensor 1]  →  [Camera]  →  [Sensor 2] [Servo]
   |                             |         |
   └─ Phát hiện đầu             └─ Phát hiện gần servo
```

**Khoảng cách Sensor 2 đến Servo:**
- **Quá gần** (< 5cm): Servo không kịp phản ứng
- **Quá xa** (> 15cm): Chai đã qua khỏi vùng đẩy
- **Tối ưu**: 8-10 cm trước servo

---

## 🧪 TESTING (Kiểm tra)

### Test 1: Sensor detection
```
1. Mở Serial Monitor
2. Đặt tay che Sensor 1 → Phải thấy: "[Sensor 1] Bottle detected"
3. Đặt tay che Sensor 2 → Phải thấy: "[Sensor 2] OK bottle detected → PASSED"
```

### Test 2: Servo movement
```
1. Gửi 'N' qua Serial Monitor (giả lập Pi trả NG)
2. Che Sensor 2
3. Servo phải đẩy ra và giữ 2 giây, sau đó rút về
```

### Test 3: Full workflow
```
1. Khởi động hệ thống (Python + Arduino)
2. Bấm START SYSTEM trên UI
3. Đặt chai OK → Quan sát:
   - Sensor 1 phát hiện → AI chạy → Trả OK
   - Sensor 2 phát hiện → Chai qua không bị đẩy
4. Đặt chai NG → Quan sát:
   - Sensor 1 phát hiện → AI chạy → Trả NG
   - Sensor 2 phát hiện → Servo đẩy chai ra
```

---

## 📊 SERIAL OUTPUT MẪU

```
========================================
Coca-Cola Sorting System - DUAL SENSOR MODE
========================================
Servo: MG996R Linear Actuator
Sensor 1 (Pin 2): Start position - triggers AI
Sensor 2 (Pin 3): Near servo - triggers kick
Servo Kick Angle: 90
Kick Duration: 2000 ms
Buffer Size: 20
Conveyor Running (Continuous)...
Ready for operation.

[Sensor 1] Bottle detected → AI triggered | Queue: 1
D,12345
[Pi Decision] OK → Bottle will pass
[Sensor 2] OK bottle detected → PASSED

[Sensor 1] Bottle detected → AI triggered | Queue: 1
D,15678
[Pi Decision] NG → Bottle marked for rejection | Queue: 1
[Sensor 2] NG bottle detected → KICKED!
[Servo] Kick executed | Queue remaining: 0

========== STATISTICS ==========
Total Detections (Sensor 1): 10
Total Passed (OK):           7
Total Rejected (NG):         3
Pass Rate:                   70.0%
Reject Rate:                 30.0%
Current Queue Size:          0
================================
```

---

## 🔍 TROUBLESHOOTING

### Vấn đề: Sensor 2 trigger nhưng không đẩy
**Nguyên nhân**: Pi chưa kịp trả lời hoặc decision bị mất  
**Giải pháp**: 
- Kiểm tra kết nối Serial (USB cable)
- Kiểm tra baud rate (9600)
- Xem log Pi có gửi 'O' hoặc 'N' không

### Vấn đề: Đẩy sai chai (chai OK bị đẩy)
**Nguyên nhân**: Queue bị lộn xộn (chai vượt nhau)  
**Giải pháp**:
- Đảm bảo chai chạy theo thứ tự (không vượt)
- Tăng khoảng cách giữa các chai
- Kiểm tra DEBOUNCE_DELAY (300ms)

### Vấn đề: Servo không đủ lực đẩy chai
**Nguyên nhân**: Điện áp yếu hoặc góc chưa đủ  
**Giải pháp**:
- Dùng nguồn 6V cho servo (thay vì 5V)
- Tăng SERVO_KICK (90 → 110)
- Kiểm tra rack có bị kẹt không

### Vấn đề: Queue full
**Nguyên nhân**: Quá nhiều chai cùng lúc  
**Giải pháp**:
- Giảm tốc độ băng chuyền
- Tăng BUFFER_SIZE (20 → 30)
- Kiểm tra Sensor 2 có bị lỗi không

---

## 📝 LƯU Ý QUAN TRỌNG

1. **Khoảng cách Sensor 1 - Sensor 2**: Đảm bảo đủ thời gian để Pi xử lý AI (thường cần 500-1000ms)

2. **Nguồn điện Servo**: MG996R tiêu thụ ~500mA khi hoạt động, KHÔNG nối trực tiếp vào Arduino 5V. Dùng nguồn ngoài 6V.

3. **Debounce**: DEBOUNCE_DELAY = 300ms để tránh đếm trùng. Nếu chai chạy quá nhanh, có thể giảm xuống 200ms.

4. **Buffer Size**: BUFFER_SIZE = 20 cho phép 20 chai cùng lúc trong hệ thống. Với tốc độ thấp, 10 cũng đủ.

5. **Backup Logic**: Nếu queue empty mà Sensor 2 vẫn trigger, có thể là:
   - Chai chạy quá nhanh (vượt qua Sensor 1 không kịp phát hiện)
   - Sensor 1 bị lỗi
   - Cần kiểm tra lại vị trí sensor

---

## 🎯 OPTIMIZATION TIPS

### Tối ưu tốc độ:
- Giảm DEBOUNCE_DELAY xuống 200ms
- Giảm SERVO_KICK_DURATION xuống 1500ms
- Dùng nguồn 6V cho servo (nhanh hơn)

### Tối ưu độ chính xác:
- Đặt Sensor 2 càng gần servo càng tốt (nhưng > 5cm)
- Kiểm tra cân chỉnh sensor (phải vuông góc với chai)
- Test nhiều lần với các loại chai khác nhau

### Tối ưu độ tin cậy:
- Tăng BUFFER_SIZE lên 30
- Thêm timeout cho queue (xóa entry quá lâu)
- Log statistics sau mỗi 10 chai để monitor

---

*Cập nhật: 2025-12-17 | Servo MG996R Linear Actuator Mode*

