# 🔧 Hướng Dẫn Tinh Chỉnh Hệ Thống

## 📋 **Tổng Quan Cải Tiến**

Hệ thống đã được cải tiến với:
- ✅ Phát hiện chai chính xác hơn (giảm false positive)
- ✅ Vẽ bounding box lên chai được phát hiện
- ✅ Điều khiển băng chuyền qua Relay (LOW trigger)
- ✅ Hiển thị thông tin chai (diện tích, aspect ratio)

---

## 🎯 **Hiện Tượng và Giải Pháp**

### **Vấn đề: Nhận diện khi không có chai**

**Nguyên nhân:**
- Blob detection quá nhạy
- Background noise
- Ánh sáng thay đổi

**Giải pháp đã áp dụng:**
1. **Tăng diện tích tối thiểu:** 5000 → 8000 pixels
2. **Kiểm tra aspect ratio:** Chai phải có tỷ lệ 1.2 - 5.0 (cao hơn rộng)
3. **Gaussian blur:** Giảm noise
4. **Adaptive threshold:** Thích ứng với ánh sáng

---

## ⚙️ **Các Tham Số Có Thể Điều Chỉnh**

### **1. Diện Tích Tối Thiểu**

Trong `ui/main_window.py`, dòng ~225:

```python
# Filter by minimum area
if area < 8000:  # Tăng nếu còn phát hiện nhầm
    continue
```

**Khuyến nghị:**
- Môi trường ít noise: `6000 - 8000`
- Môi trường nhiều noise: `10000 - 15000`
- Chai nhỏ: `5000`
- Chai lớn: `12000`

### **2. Aspect Ratio (Tỷ lệ cao/rộng)**

Trong `ui/main_window.py`, dòng ~235:

```python
# Valid bottle: aspect ratio between 1.2 and 5.0
if aspect_ratio < 1.2 or aspect_ratio > 5.0:
    continue
```

**Khuyến nghị:**
- Chai đứng chuẩn: `1.5 - 4.0`
- Chai nghiêng được: `1.2 - 5.0`
- Chai rất cao: `2.0 - 6.0`

### **3. Threshold Value**

Hiện tại dùng Adaptive Threshold, nhưng nếu cần threshold cố định:

```python
# Thay thế adaptive threshold bằng:
_, thresh = cv2.threshold(blurred, 120, 255, cv2.THRESH_BINARY_INV)
# Tăng 120 nếu background sáng
# Giảm 120 nếu background tối
```

### **4. Virtual Line Position**

Trong `config.py`:

```python
VIRTUAL_LINE_X = 320  # Vị trí pixel (0-640)
```

**Khuyến nghị:**
- Sớm hơn: `200` (nhiều thời gian xử lý)
- Giữa: `320` (cân bằng)
- Muộn hơn: `400` (ít thời gian nhưng chính xác)

### **5. Detection Cooldown**

Trong `config.py`:

```python
DETECTION_COOLDOWN = 1.0  # Giây
```

**Khuyến nghị:**
- Băng chuyền chậm: `0.5 - 0.8`
- Băng chuyền vừa: `1.0 - 1.5`
- Băng chuyền nhanh: `1.5 - 2.0`

---

## 🎨 **Bounding Box và Hiển Thị**

### **Màu sắc hiện tại:**
- **GREEN (Xanh lá):** Chai được phát hiện hợp lệ
- **RED (Đỏ):** Chai đang crossing virtual line (trigger detection)

### **Thông tin hiển thị:**
- `Area:` Diện tích (pixels²)
- `AR:` Aspect Ratio (cao/rộng)
- `CROSSING!` Khi đi qua vạch

### **Tùy chỉnh màu:**

Trong `ui/main_window.py`, dòng ~250:

```python
# Bottle detected
cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Green

# Crossing line
cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)  # Red
```

**Màu BGR:**
- `(0, 255, 0)` = Green
- `(0, 0, 255)` = Red
- `(255, 0, 0)` = Blue
- `(0, 255, 255)` = Yellow
- `(255, 255, 0)` = Cyan

---

## 🔌 **Cấu Hình Relay**

### **Arduino Pin:**
```cpp
const int RELAY_PIN = 7;  // Thay đổi nếu dùng pin khác
```

### **Chế độ Trigger:**
```cpp
const int RELAY_ON = LOW;   // LOW trigger (hiện tại)
const int RELAY_OFF = HIGH;

// Nếu relay của bạn là HIGH trigger:
// const int RELAY_ON = HIGH;
// const int RELAY_OFF = LOW;
```

### **Test Relay:**

Upload Arduino code, sau đó test qua Serial Monitor:

```
Gửi: S    → Băng chuyền BẬT (relay LOW)
Gửi: P    → Băng chuyền TẮT (relay HIGH)
```

---

## 🧪 **Quy Trình Calibration**

### **Bước 1: Test Phát Hiện Chai**

```bash
# Chạy hệ thống
python3 main.py

# Bấm "START SYSTEM"
# Quan sát camera feed:
# - Có bounding box GREEN khi có chai?
# - Có FALSE POSITIVE không?
```

### **Bước 2: Điều Chỉnh Nếu Cần**

**Nếu vẫn phát hiện nhầm:**
```python
# Tăng area tối thiểu
if area < 12000:  # Tăng lên 12000
    continue
```

**Nếu không phát hiện được chai:**
```python
# Giảm area tối thiểu
if area < 5000:  # Giảm xuống 5000
    continue

# Hoặc giảm aspect ratio min
if aspect_ratio < 1.0:  # Giảm từ 1.2 xuống 1.0
    continue
```

### **Bước 3: Test Virtual Line**

```bash
# Di chuyển chai qua vạch cyan
# Kiểm tra:
# - Box chuyển từ GREEN sang RED?
# - Có text "CROSSING!"?
# - Queue tăng +1?
```

### **Bước 4: Test Relay**

```bash
# Bấm "START SYSTEM"
# Kiểm tra:
# - Arduino Serial Monitor: "Conveyor: RUNNING"
# - Relay click (nghe tiếng)
# - Băng chuyền chạy

# Bấm "STOP SYSTEM"
# Kiểm tra:
# - Arduino Serial Monitor: "Conveyor: STOPPED"
# - Băng chuyền dừng
```

---

## 📊 **Debug Info**

### **Thông tin trên frame:**

Khi có chai được phát hiện, bạn sẽ thấy:

```
Area: 9500, AR: 2.35    ← Thông tin chai
         ↓
┌──────────┐
│  GREEN   │            ← Bounding box xanh
│  BOX     │
└──────────┘

Khi crossing:
    CROSSING!           ← Text đỏ
┌──────────┐
│   RED    │            ← Box chuyển đỏ
│   BOX    │
└──────────┘
```

### **Terminal Output:**

```
[UI] Bottle detected at (320, 240)
[AI] NCNN output shape: (8400, 12)
[AI] Raw detections: 47, After NMS: 5
[AI] Components: cap=True, filled=True, label=False
[AI] Result: N | Reason: Thiếu nhãn | Time: 125.3ms
[UI] Added to queue: N | Queue size: 1
```

---

## 🎯 **Troubleshooting**

### **1. Vẫn phát hiện khi không có chai**

```python
# Tăng area đến 15000
if area < 15000:
    continue

# Hoặc kiểm tra thêm độ tròn (circularity)
perimeter = cv2.arcLength(contour, True)
circularity = 4 * 3.14159 * area / (perimeter * perimeter)
if circularity < 0.3:  # Chai không quá tròn
    continue
```

### **2. Không phát hiện được chai**

```python
# Giảm area xuống 4000
if area < 4000:
    continue

# Giảm aspect ratio
if aspect_ratio < 0.8 or aspect_ratio > 6.0:
    continue

# Thử threshold thấp hơn
_, thresh = cv2.threshold(blurred, 80, 255, cv2.THRESH_BINARY_INV)
```

### **3. Relay không hoạt động**

```bash
# Kiểm tra pin
ls -l /sys/class/gpio/  # Pi có pin 7 không?

# Test relay trực tiếp trên Arduino
digitalWrite(7, LOW);   // Phải nghe click
digitalWrite(7, HIGH);  // Phải nghe click

# Kiểm tra jumper relay
# Đảm bảo jumper ở chế độ LOW (hoặc HIGH tùy relay)
```

### **4. Bounding box không hiện**

```python
# Kiểm tra có vào được if statement không
print(f"[DEBUG] Valid bottles found: {len(valid_bottles)}")

# Nếu = 0, kiểm tra lại threshold và area
```

---

## 📝 **Summary Checklist**

- [ ] Arduino code đã upload với relay support
- [ ] Python code có vẽ bounding box
- [ ] Relay pin đúng (mặc định: pin 7)
- [ ] Jumper relay đúng mode (LOW trigger)
- [ ] Area threshold phù hợp (8000 - 12000)
- [ ] Aspect ratio phù hợp (1.2 - 5.0)
- [ ] Virtual line ở vị trí hợp lý (320)
- [ ] Cooldown phù hợp với tốc độ băng chuyền (1.0s)
- [ ] Test phát hiện chai: ✅
- [ ] Test virtual line: ✅
- [ ] Test relay: ✅
- [ ] Test queue: ✅

---

**Chúc bạn thành công! 🚀**

