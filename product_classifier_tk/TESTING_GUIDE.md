# 🧪 Testing Guide - Hướng Dẫn Test Hệ Thống

## 📋 Tổng Quan

Có 3 test scripts để kiểm tra hệ thống:

| Script | Mục Đích | Khi Nào Dùng |
|--------|----------|--------------|
| `test_system_components.py` | Test tất cả components | Lần đầu setup |
| `test_arduino_connection.py` | Test Arduino connection | Khi có vấn đề Arduino |
| `demo_voting_mechanism.py` | Demo voting concept | Hiểu cách voting hoạt động |

---

## 🔧 Test 1: System Components

### Mục Đích
Test tất cả components của hệ thống:
- ✅ Python dependencies
- ✅ Camera availability
- ✅ Arduino serial connection
- ✅ YOLOv8 model loading

### Cách Chạy
```bash
python3 test_system_components.py
```

### Output Mong Đợi
```
================================================================================
🧪 SYSTEM COMPONENT TEST SUITE
================================================================================

TEST 1: Checking Python Dependencies
✅ opencv-python        - OK
✅ numpy                - OK
✅ pyserial             - OK
✅ ultralytics          - OK
✅ Pillow               - OK

TEST 2: Camera Detection
✅ Camera 0 found: 640x480

TEST 3: Arduino Serial Connection
✅ Connected to Arduino at /dev/ttyACM0

TEST 4: YOLOv8 Model Loading
✅ Model loaded successfully!

================================================================================
📋 TEST SUMMARY
================================================================================
IMPORTS          : ✅ PASS
CAMERA           : ✅ PASS
SERIAL           : ✅ PASS
MODEL            : ✅ PASS

✅ ALL TESTS PASSED!
System is ready to run.
```

### Khi Nào Chạy
- ✅ Lần đầu setup hệ thống
- ✅ Sau khi cài dependencies mới
- ✅ Khi có component không hoạt động

---

## 🔌 Test 2: Arduino Connection

### Mục Đích
Test chi tiết kết nối và giao tiếp với Arduino.

### Cách Chạy

#### Mode 1: Connection Test Only (An Toàn)
```bash
python3 test_arduino_connection.py
```

**Chỉ test:**
- Serial port connection
- PING/PONG communication
- STATUS command
- **KHÔNG** chạy hardware thật

#### Mode 2: Full Hardware Test
```bash
python3 test_arduino_connection.py --hardware
```

**Test đầy đủ:**
- Serial port connection
- Communication
- **Băng chuyền chạy 2 giây** ⚠️
- **Servo eject motion** ⚠️

⚠️ **CẢNH BÁO:** Mode `--hardware` sẽ chạy motor thật!
- Đảm bảo khu vực an toàn
- Băng chuyền phải được lắp đúng
- Servo phải được gắn chắc chắn

### Output Mong Đợi

**Connection Test:**
```
================================================================================
🔧 ARDUINO CONNECTION TEST
================================================================================
Port: /dev/ttyACM0
Baud: 115200

Step 1: Opening serial port...
✅ Port opened successfully

Step 2: Waiting for Arduino reset (2.5s)...
✅ Wait complete

Step 3: Reading startup messages...
  📨 Arduino Bottle Defect System Ready
✅ Startup messages received

Step 4: Testing PING command...
  📨 Response: PONG
✅ PING successful!

Step 5: Testing STATUS command...
  📨 === System Status ===
  📨 Relay (Conveyor): OFF
✅ STATUS received

Step 6: Hardware test skipped
  ℹ️  To test hardware, run with --hardware flag

================================================================================
📊 TEST RESULTS
================================================================================
✅ Arduino connection: OK
✅ Communication: WORKING
✅ Ready to use!
```

**Hardware Test (`--hardware`):**
```
Step 6: Testing physical hardware...
  ⚠️  WARNING: This will move physical hardware!
  - Conveyor will RUN for 2 seconds
  - Servo will perform eject motion

  Make sure:
    • Area is clear and safe
    • Conveyor belt is properly connected
    • Servo is properly mounted

  ⚠️  Proceed with hardware test? (y/N): y

  Starting hardware test in 3 seconds...
    3...
    2...
    1...

  🔵 Starting conveyor...
    📨 OK: Conveyor started
  ▶️  Conveyor RUNNING...
    ⏱️  2 seconds remaining...
    ⏱️  1 seconds remaining...
  🔴 Stopping conveyor...
    📨 OK: Conveyor stopped
  ✅ Conveyor stopped

  Testing servo movement...
  🔧 Moving servo to eject position...
    📨 REJECT: Ejecting bottle...
    📨 OK: Bottle ejected
  ✅ Servo test complete

✅ All hardware commands executed successfully!
```

### Khi Nào Chạy
- ✅ Khi thấy "SIMULATION MODE"
- ✅ Băng chuyền không chạy
- ✅ Cần verify hardware hoạt động
- ✅ Sau khi sửa connection issues

---

## 🗳️ Test 3: Voting Mechanism Demo

### Mục Đích
Demo minh họa cách voting mechanism hoạt động.

### Cách Chạy
```bash
python3 demo_voting_mechanism.py
```

### Output
```
================================================================================
🗳️  VOTING MECHANISM DEMONSTRATION
================================================================================

Scenario: Good Bottle (no defect)
Ground Truth: GOOD
Detection Accuracy: 85%
Voting Threshold: 3/5 frames must agree

Frame 1: ✅ GOOD (confidence: 0.87)
Frame 2: ✅ GOOD (confidence: 0.82)
Frame 3: ❌ DEFECT: no_cap (confidence: 0.65)
Frame 4: ✅ GOOD (confidence: 0.79)
Frame 5: ✅ GOOD (confidence: 0.91)

Vote Summary:
  - No defect votes: 4

FINAL DECISION (after voting):
  Result: ✅ GOOD BOTTLE
  Defect votes: 1/5 (below threshold)

✅ CORRECT DECISION!
```

### Khi Nào Chạy
- ✅ Muốn hiểu voting mechanism
- ✅ Training người dùng mới
- ✅ Demo hệ thống

---

## 📊 So Sánh Test Scripts

| Feature | test_system_components | test_arduino_connection | demo_voting |
|---------|----------------------|------------------------|-------------|
| **Test Dependencies** | ✅ | ❌ | ❌ |
| **Test Camera** | ✅ | ❌ | ❌ |
| **Test Arduino Connection** | ✅ | ✅ | ❌ |
| **Test Serial Communication** | Basic | Detailed | ❌ |
| **Test Hardware Movement** | ❌ | ✅ (with --hardware) | ❌ |
| **Test AI Model** | Load only | ❌ | ❌ |
| **Demo Concept** | ❌ | ❌ | ✅ |

---

## 🎯 Workflow Khuyến Nghị

### Lần Đầu Setup:

```bash
# 1. Test tất cả components
python3 test_system_components.py

# 2. Nếu Arduino pass → Test chi tiết
python3 test_arduino_connection.py

# 3. Nếu connection OK → Test hardware
python3 test_arduino_connection.py --hardware

# 4. Hiểu voting concept
python3 demo_voting_mechanism.py

# 5. Chạy hệ thống
python3 main_continuous_flow_tkinter.py
```

### Khi Gặp Lỗi:

**Lỗi: SIMULATION MODE**
```bash
# Test Arduino chi tiết
python3 test_arduino_connection.py

# Xem logs và fix
# Sau khi fix, test lại với hardware
python3 test_arduino_connection.py --hardware
```

**Lỗi: Camera không mở**
```bash
# Test components để xem camera nào available
python3 test_system_components.py

# Update CAMERA_INDEX trong Config
```

**Lỗi: Model không load**
```bash
# Test components để verify model path
python3 test_system_components.py

# Check model file exists
ls -lh model/my_model.pt
```

---

## 💡 Tips

### Tip 1: Test Nhanh Arduino

Nếu chỉ muốn verify Arduino kết nối nhanh:
```bash
python3 test_arduino_connection.py | grep "RESULTS" -A 5
```

### Tip 2: Test Hardware An Toàn

Luôn chạy test connection trước khi test hardware:
```bash
# Step 1: Connection first
python3 test_arduino_connection.py

# Step 2: If pass, then hardware
python3 test_arduino_connection.py --hardware
```

### Tip 3: Automate Testing

Tạo script test tự động:
```bash
#!/bin/bash
# test_all.sh

echo "Running all tests..."

echo -e "\n=== Test 1: Components ==="
python3 test_system_components.py

if [ $? -eq 0 ]; then
    echo -e "\n=== Test 2: Arduino Connection ==="
    python3 test_arduino_connection.py
fi

echo -e "\nAll tests complete!"
```

---

## 🔍 Troubleshooting Tests

### Test Script Fails to Run

**Error:** `ModuleNotFoundError: No module named 'serial'`
```bash
pip3 install pyserial
```

**Error:** `ModuleNotFoundError: No module named 'cv2'`
```bash
pip3 install opencv-python
```

**Error:** `ModuleNotFoundError: No module named 'ultralytics'`
```bash
pip3 install ultralytics
```

### Arduino Test Always Fails

1. Check port exists:
   ```bash
   ls /dev/ttyACM*
   ```

2. Check permissions:
   ```bash
   sudo usermod -a -G dialout $USER
   # Logout & login
   ```

3. Check firmware uploaded:
   - Open Arduino IDE
   - Upload `arduino/product_sorter.ino`

4. Read detailed guide:
   ```bash
   cat ARDUINO_DEBUG.md
   ```

---

## 📚 Related Documentation

- **[ARDUINO_DEBUG.md](ARDUINO_DEBUG.md)** - Arduino troubleshooting chi tiết
- **[QUICK_START.md](QUICK_START.md)** - Setup nhanh
- **[README_VI.md](README_VI.md)** - Hướng dẫn đầy đủ tiếng Việt

---

**Happy Testing! 🧪🤖**

