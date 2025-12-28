# HƯỚNG DẪN ĐIỀU KHIỂN BĂNG CHUYỀN

## 🎯 TÍNH NĂNG MỚI

**START SYSTEM** → Băng chuyền CHẠY + Nhận diện HOẠT ĐỘNG  
**STOP SYSTEM** → Băng chuyền DỪNG + Nhận diện TẠM NGƯNG

---

## 🔧 CÁC THAY ĐỔI

### 1. **Arduino (`sorting_control.ino`)**

#### Thêm biến trạng thái:
```cpp
bool conveyorRunning = false;  // Trạng thái băng chuyền
```

#### Setup ban đầu:
```cpp
void setup() {
  // ...
  // Băng chuyền BẮT ĐẦU Ở TRẠNG THÁI DỪNG
  digitalWrite(RELAY_PIN, HIGH);  // HIGH = Stop
  conveyorRunning = false;
  
  Serial.println("Conveyor: STOPPED (waiting for START command)");
  Serial.println("Ready. Send 'S' to start, 'P' to pause.");
}
```

#### Lệnh điều khiển mới:
- **'S'** (Start) → Bật relay (LOW), băng chuyền chạy
- **'P'** (Pause/Stop) → Tắt relay (HIGH), băng chuyền dừng
- **'O'** (OK) → Quyết định chai OK (như cũ)
- **'N'** (NG) → Quyết định chai NG (như cũ)

#### Logic sensors:
```cpp
void checkSensor1() {
  // CHỈ hoạt động nếu conveyor đang chạy
  if (!conveyorRunning) {
    return;
  }
  // ... xử lý sensor
}

void checkSensor2() {
  // CHỈ hoạt động nếu conveyor đang chạy
  if (!conveyorRunning) {
    return;
  }
  // ... xử lý sensor
}
```

---

### 2. **Python Hardware (`core/hardware.py`)**

#### Thêm methods mới:
```python
def start_conveyor(self):
    """Start conveyor belt (relay ON)"""
    print("[Hardware] Starting conveyor belt...")
    return self.send_command('S')

def stop_conveyor(self):
    """Stop conveyor belt (relay OFF)"""
    print("[Hardware] Stopping conveyor belt...")
    return self.send_command('P')
```

---

### 3. **UI (`ui/main_window.py`)**

#### START SYSTEM:
```python
def start_system(self):
    # 1. Bật băng chuyền
    self.hardware.start_conveyor()
    
    # 2. Bật nhận diện
    self.hardware.start_listening(self.on_bottle_detected)
    
    # 3. Cập nhật UI
    self.status_label.configure(text="● RUNNING", fg='#27ae60')
```

#### STOP SYSTEM:
```python
def stop_system(self):
    # 1. Dừng nhận diện
    self.hardware.stop_listening()
    
    # 2. Dừng băng chuyền
    self.hardware.stop_conveyor()
    
    # 3. Cập nhật UI
    self.status_label.configure(text="● STOPPED", fg='#e74c3c')
```

---

## 🎬 WORKFLOW

### **Khi khởi động hệ thống:**
```
Arduino: Relay = HIGH (Dừng)
UI: Status = STOPPED
Sensors: Không hoạt động
```

### **Khi bấm START SYSTEM:**
```
1. Pi gửi 'S' → Arduino
2. Arduino: 
   - digitalWrite(RELAY_PIN, LOW) → Băng chuyền CHẠY
   - conveyorRunning = true
   - Sensors bắt đầu hoạt động
3. UI: Status = RUNNING (xanh)
```

### **Khi bấm STOP SYSTEM:**
```
1. Pi gửi 'P' → Arduino
2. Arduino:
   - digitalWrite(RELAY_PIN, HIGH) → Băng chuyền DỪNG
   - conveyorRunning = false
   - Sensors ngưng hoạt động
3. UI: Status = STOPPED (đỏ)
```

---

## 📊 SERIAL LOG MẪU

### **Khởi động:**
```
========================================
Coca-Cola Sorting System - DUAL SENSOR MODE
========================================
Conveyor: STOPPED (waiting for START command)
Ready. Send 'S' to start, 'P' to pause.
```

### **Bấm START SYSTEM:**
```
[Hardware] Starting conveyor belt...
[Conveyor] STARTED - Belt running
[Hardware] Started listening for detections
[UI] System started - Conveyor running, waiting for detections...
```

### **Hoạt động:**
```
[Sensor 1] Bottle detected → AI triggered | Queue: 1
D,12345
[Pi Decision] OK → Bottle at index 0 will pass
[Sensor 2] Bottle at index 0 detected → OK → PASSING
```

### **Bấm STOP SYSTEM:**
```
[Hardware] Stopping listener...
[Hardware] Listener stopped
[Hardware] Stopping conveyor belt...
[Conveyor] STOPPED - Belt paused
[UI] System stopped - Conveyor stopped, detection paused
```

---

## 🔍 KIỂM TRA HOẠT ĐỘNG

### **Test 1: Khởi động**
```
✅ Băng chuyền phải DỪNG (không chạy)
✅ UI hiện "● STOPPED" màu đỏ
✅ Serial Monitor: "Conveyor: STOPPED"
```

### **Test 2: START SYSTEM**
```
✅ Băng chuyền BẮT ĐẦU CHẠY
✅ UI hiện "● RUNNING" màu xanh
✅ Serial Monitor: "[Conveyor] STARTED"
✅ Đặt chai qua → sensor phát hiện → AI chạy
```

### **Test 3: STOP SYSTEM**
```
✅ Băng chuyền DỪNG LẠI
✅ UI hiện "● STOPPED" màu đỏ
✅ Serial Monitor: "[Conveyor] STOPPED"
✅ Đặt chai qua → sensor KHÔNG phát hiện (đúng!)
```

### **Test 4: START lại**
```
✅ Băng chuyền chạy lại
✅ Sensors hoạt động lại bình thường
```

---

## ⚠️ LƯU Ý

### **1. Relay logic:**
- **LOW (0V)** = Relay ON = Băng chuyền CHẠY
- **HIGH (5V)** = Relay OFF = Băng chuyền DỪNG

### **2. Sensors chỉ hoạt động khi băng chuyền chạy:**
- Nếu STOP → sensors không phát hiện chai
- Tránh xử lý chai khi băng dừng

### **3. Queue vẫn giữ nguyên khi STOP:**
- Các chai đang trong queue không bị xóa
- Khi START lại → tiếp tục xử lý từ queue

### **4. Nếu relay không hoạt động:**
- Kiểm tra kết nối relay (Pin 4)
- Kiểm tra relay module (có thể cần đảo logic HIGH/LOW)
- Test bằng cách: Sensor 1 → relay phải BẬT/TẮT

---

## 🛠️ TROUBLESHOOTING

### **Vấn đề: Băng chuyền không chạy khi START**
**Kiểm tra:**
1. Serial Monitor có hiện "[Conveyor] STARTED"?
2. Relay module có click?
3. Kiểm tra dây kết nối Pin 4 → Relay IN
4. Thử đảo logic: `digitalWrite(RELAY_PIN, HIGH)` trong `startConveyor()`

### **Vấn đề: Băng chuyền không dừng khi STOP**
**Kiểm tra:**
1. Serial Monitor có hiện "[Conveyor] STOPPED"?
2. Relay module có click?
3. Có thể relay của bạn cần logic ngược lại

### **Vấn đề: Sensors vẫn phát hiện khi STOP**
**Kiểm tra:**
1. Code đã có `if (!conveyorRunning) return;` trong checkSensor1/2?
2. Upload lại code Arduino
3. Restart hệ thống

---

## 📝 TỔNG KẾT

### **Trước đây:**
- Băng chuyền luôn chạy (CONTINUOUS MODE)
- Không điều khiển được

### **Bây giờ:**
- ✅ **START** → Băng chuyền CHẠY + Nhận diện ON
- ✅ **STOP** → Băng chuyền DỪNG + Nhận diện OFF
- ✅ Kiểm soát đầy đủ từ UI
- ✅ An toàn hơn (không chạy khi không cần)

---

*Cập nhật: 2025-12-17 | Conveyor Start/Stop Control*

