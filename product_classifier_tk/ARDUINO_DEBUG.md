# 🔧 Arduino Connection Debugging Guide

## ⚠️ Vấn Đề: Băng Chuyền Không Chạy

Nếu bạn thấy log như "SIMULATION MODE" hoặc "Băng chuyền KHÔNG chạy thật", có nghĩa là **Arduino chưa kết nối**.

---

## 🔍 Kiểm Tra Từng Bước

### Bước 1: Kiểm Tra Arduino Đã Cắm USB

```bash
# Linux/Raspberry Pi:
ls /dev/ttyACM* /dev/ttyUSB*

# Nên thấy output:
# /dev/ttyACM0  hoặc /dev/ttyUSB0

# Windows:
# Mở Device Manager
# Ports (COM & LPT) → Tìm Arduino Uno (COMx)
```

**Nếu không thấy device:**
- ❌ Arduino chưa cắm USB
- ❌ Dây USB hỏng
- ❌ Driver chưa cài (Windows)

**Giải pháp:**
```bash
# Thử rút và cắm lại USB
# Thử dây USB khác
# Windows: Cài Arduino IDE (có driver tự động)
```

---

### Bước 2: Kiểm Tra Port Trong Config

Mở `main_continuous_flow_tkinter.py`, tìm `Config` class:

```python
class Config:
    # ==================== Serial Communication ====================
    SERIAL_PORT = "/dev/ttyACM0"  # ← KIỂM TRA DÒNG NÀY
```

**Thay đổi theo port thật:**

```python
# Linux/Pi:
SERIAL_PORT = "/dev/ttyACM0"   # Hoặc /dev/ttyUSB0

# Windows:
SERIAL_PORT = "COM3"           # Hoặc COM4, COM5, etc.
```

**Cách tìm port đúng:**

```bash
# Linux/Pi - Trước khi cắm:
ls /dev/ttyACM* /dev/ttyUSB*

# Cắm Arduino vào

# Linux/Pi - Sau khi cắm:
ls /dev/ttyACM* /dev/ttyUSB*
# Port mới xuất hiện là port của Arduino
```

---

### Bước 3: Kiểm Tra Quyền Truy Cập (Linux/Pi)

```bash
# Kiểm tra quyền
ls -l /dev/ttyACM0

# Output:
# crw-rw---- 1 root dialout ... /dev/ttyACM0
#                    ^^^^^^^ User phải trong group này

# Thêm user vào group dialout
sudo usermod -a -G dialout $USER

# QUAN TRỌNG: Logout và login lại!
# Hoặc restart Pi
```

**Verify:**
```bash
# Kiểm tra user đã trong group chưa
groups

# Nên thấy: ... dialout ...
```

---

### Bước 4: Kiểm Tra Firmware Đã Upload

```bash
# Mở Arduino IDE
# File → Open → arduino/product_sorter.ino

# Tools → Board → Arduino Uno
# Tools → Port → /dev/ttyACM0 (hoặc COM port)

# Upload (nhấn mũi tên →)
```

**Verify upload thành công:**

```bash
# Mở Serial Monitor (Ctrl+Shift+M)
# Set baud rate: 115200

# Nên thấy:
# ========================================
# Arduino Bottle Defect System Ready
# Commands: START_CONVEYOR, STOP_CONVEYOR, REJECT, PING, STATUS
# ========================================
```

---

### Bước 5: Test Arduino Tự Động

**Chạy test script:**

```bash
# Test connection only (không chạy hardware)
python3 test_arduino_connection.py

# Test connection + hardware (băng chuyền chạy 2s)
python3 test_arduino_connection.py --hardware
```

**⚠️ Lưu ý:** Flag `--hardware` sẽ:
- Chạy băng chuyền 2 giây
- Test servo gạt
- Cần đảm bảo an toàn trước khi chạy!

---

### Bước 6: Test Arduino Manual (Advanced)

**Python test script thủ công:**

```python
# test_arduino_manual.py
import serial
import time

port = "/dev/ttyACM0"  # Thay đổi nếu cần
baud = 115200

try:
    print(f"Connecting to {port}...")
    ser = serial.Serial(port, baud, timeout=1)
    time.sleep(2.5)  # Wait for Arduino reset
    
    # Read startup message
    print("\nStartup messages:")
    for _ in range(10):
        if ser.in_waiting > 0:
            line = ser.readline().decode().strip()
            print(f"  {line}")
    
    # Send PING
    print("\nSending PING...")
    ser.write(b"PING\n")
    time.sleep(0.5)
    
    # Read response
    if ser.in_waiting > 0:
        response = ser.readline().decode().strip()
        print(f"Response: {response}")
        if response == "PONG":
            print("✅ Arduino communication OK!")
        else:
            print("⚠️  Unexpected response")
    else:
        print("❌ No response from Arduino")
    
    # Send STATUS
    print("\nSending STATUS...")
    ser.write(b"STATUS\n")
    time.sleep(0.5)
    
    while ser.in_waiting > 0:
        line = ser.readline().decode().strip()
        print(f"  {line}")
    
    ser.close()
    print("\n✅ Test complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
```

**Chạy test:**
```bash
python3 test_arduino_manual.py
```

---

### Bước 6: Kiểm Tra pyserial Đã Cài

```bash
pip3 show pyserial

# Nếu không có:
pip3 install pyserial
```

---

## 🎯 Checklist

Kiểm tra tất cả:

- [ ] Arduino đã cắm USB
- [ ] Port đúng trong Config (`SERIAL_PORT`)
- [ ] User trong group `dialout` (Linux/Pi)
- [ ] Đã logout/login lại sau khi add group
- [ ] Firmware đã upload thành công
- [ ] Baud rate = 115200 (Arduino và Python)
- [ ] pyserial đã cài (`pip3 install pyserial`)
- [ ] Test manual thành công

---

## 📊 Log Console Khi Kết Nối

### ✅ Kết Nối Thành Công:

```
[Arduino] ========================================
[Arduino] Arduino Bottle Defect System Ready
[Arduino] Commands: START_CONVEYOR, STOP_CONVEYOR, REJECT, PING, STATUS
[Arduino] ========================================
✅ Connected to Arduino at /dev/ttyACM0
🔌 Hardware control: ENABLED
```

### ❌ Kết Nối Thất Bại:

```
================================================================================
❌ KHÔNG THỂ KẾT NỐI ARDUINO!
================================================================================
Lỗi: [Errno 2] No such file or directory: '/dev/ttyACM0'
Port: /dev/ttyACM0

⚠️  HỆ THỐNG SẼ CHẠY Ở CHẾ ĐỘ SIMULATION (GIẢ LẬP)
    - Băng chuyền KHÔNG chạy thật
    - Servo KHÔNG gạt thật
    - Chỉ hiển thị log để test
```

---

## 🔧 Giải Pháp Từng Lỗi Cụ Thể

### Lỗi: "No such file or directory"

**Nguyên nhân:** Port không tồn tại

**Giải pháp:**
```bash
# Tìm port đúng
ls /dev/ttyACM* /dev/ttyUSB*

# Sửa trong Config:
SERIAL_PORT = "/dev/ttyACM0"  # Port thực tế
```

---

### Lỗi: "Permission denied"

**Nguyên nhân:** Không có quyền truy cập port

**Giải pháp:**
```bash
# Add user vào group
sudo usermod -a -G dialout $USER

# PHẢI logout/login lại!

# Hoặc chạy tạm với sudo (không khuyến nghị):
sudo python3 main_continuous_flow_tkinter.py
```

---

### Lỗi: "Device or resource busy"

**Nguyên nhân:** Port đang được dùng bởi process khác

**Giải pháp:**
```bash
# Tìm process đang dùng
sudo lsof | grep ttyACM0

# Kill process đó
kill -9 PID

# Hoặc đơn giản: Rút và cắm lại USB Arduino
```

---

### Lỗi: No startup message từ Arduino

**Nguyên nhân:** Firmware chưa upload hoặc sai

**Giải pháp:**
1. Mở Arduino IDE
2. Upload lại `arduino/product_sorter.ino`
3. Mở Serial Monitor kiểm tra
4. Baud rate phải là 115200

---

## 💡 Tips

### Tip 1: Test Nhanh Với Arduino IDE

```
1. Mở Arduino IDE
2. Tools → Serial Monitor
3. Baud: 115200
4. Gõ: PING
5. Nhấn Enter
6. Phải thấy: PONG
```

### Tip 2: Tạm Thời Chạy Simulation

Nếu muốn test code mà chưa có Arduino:

```python
# Trong Config:
SERIAL_PORT = "FAKE_PORT"  # Sẽ tự động vào simulation mode
```

### Tip 3: Debug Log

```python
# Trong Config:
DEBUG_MODE = True  # Hiển thị tất cả serial commands
```

---

## 📞 Vẫn Chưa Giải Quyết?

1. **Check Arduino board:**
   - LED power có sáng không?
   - LED TX/RX có nhấp nháy không khi upload?

2. **Try different USB port:**
   - Thử các cổng USB khác trên Pi/PC

3. **Check USB cable:**
   - Một số dây USB chỉ sạc, không truyền data
   - Thử dây USB khác

4. **Reinstall Arduino IDE:**
   - Windows: Driver có thể bị lỗi

5. **Try on another computer:**
   - Xác định vấn đề là Arduino hay máy tính

---

**Good luck! 🔧🤖**

