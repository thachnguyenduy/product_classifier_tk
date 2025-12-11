# 🔍 Virtual Line Detection Logic - Right to Left

## 📋 **Tổng Quan**

Hệ thống nhận diện chai nước khi băng chuyền di chuyển từ **PHẢI sang TRÁI**.

---

## 🎯 **Logic Mới (Đã Cải Thiện)**

### **1. Tracking Bottles** ⭐

**Trước:**
- ❌ Không track vị trí trước đó
- ❌ Trigger khi chai ở gần line (có thể trigger nhiều lần)
- ❌ Không biết hướng di chuyển

**Sau:**
- ✅ Track từng chai với ID riêng
- ✅ Lưu vị trí trước đó (prev_cx)
- ✅ Chỉ trigger khi đi từ RIGHT → LEFT qua line
- ✅ Mỗi chai chỉ trigger 1 lần

---

### **2. Crossing Detection Logic**

```python
# Chai bắt đầu ở bên PHẢI (cx > line_x + tolerance)
prev_cx = 500  # Ví dụ: ở bên phải

# Chai di chuyển sang TRÁI
cx = 300  # Đang đi về phía line

# Khi đi qua line (cx <= line_x + tolerance)
if prev_cx > line_x + tolerance and cx <= line_x + tolerance:
    # ✅ TRIGGER DETECTION!
    # Chai đã đi từ RIGHT sang LEFT qua line
```

**Điều kiện:**
- `prev_cx > line_x + tolerance` → Chai ở bên PHẢI
- `cx <= line_x + tolerance` → Chai đã đi qua line sang TRÁI
- `not tracked['crossed']` → Chưa trigger lần nào

---

### **3. Visual Feedback**

**Màu sắc:**
- **GREEN box:** Chai đang được track (chưa qua line)
- **GRAY box:** Chai đã qua line (đã trigger)
- **RED box:** Chai đang crossing line (triggering)

**Mũi tên:**
- **←:** Chai đang đi sang TRÁI
- **→:** Chai đang đi sang PHẢI

---

## ⚙️ **Cấu Hình**

### **config.py**

```python
VIRTUAL_LINE_X = 320        # Vị trí line (giữa frame 640px)
CROSSING_TOLERANCE = 40     # Tăng từ 20 → 40 (dễ detect hơn)
DETECTION_COOLDOWN = 0.8    # Giảm từ 1.0 → 0.8 (nhanh hơn)
```

### **Detection Thresholds**

```python
# Blob detection
area_min = 5000              # Giảm từ 8000 → 5000
aspect_ratio = 1.0 - 6.0     # Mở rộng từ 1.2-5.0 → 1.0-6.0
```

---

## 🔄 **Workflow**

```
Frame 1: Chai ở RIGHT (cx=500)
  → Track: bottle_id=0, prev_cx=500, crossed=False
  → Draw GREEN box

Frame 2: Chai di chuyển LEFT (cx=400)
  → Update: prev_cx=500, cx=400
  → Draw GREEN box + arrow ←

Frame 3: Chai gần line (cx=350)
  → Update: prev_cx=400, cx=350
  → Draw GREEN box + arrow ←

Frame 4: Chai CROSSING LINE (cx=310)
  → Check: prev_cx=350 > 320+40? NO (350 < 360)
  → Wait...

Frame 5: Chai CROSSING LINE (cx=300)
  → Check: prev_cx=350 > 360? NO
  → Wait...

Frame 6: Chai đã qua line (cx=280)
  → Check: prev_cx=300 > 360? NO
  → Wait...

Frame 7: Chai tiếp tục LEFT (cx=250)
  → Check: prev_cx=280 > 360? NO
  → Wait...

❌ VẤN ĐỀ: Logic cần fix!

✅ FIX: Check khi prev_cx > line_x + tolerance VÀ cx <= line_x + tolerance
```

---

## 🔧 **Fix Logic**

**Code đã fix:**

```python
# Check crossing from RIGHT to LEFT
if prev_cx > line_x + tolerance and cx <= line_x + tolerance:
    # ✅ TRIGGER!
    tracked['crossed'] = True
    self._on_bottle_detected(frame, cx, cy)
```

**Ví dụ:**
- `line_x = 320`
- `tolerance = 40`
- `prev_cx = 380` (RIGHT: 380 > 360 ✅)
- `cx = 350` (LEFT: 350 <= 360 ✅)
- **→ TRIGGER!**

---

## 📊 **Debug Output**

Khi `DEBUG_MODE = True`:

```
[Blob] ✅ Bottle #0 CROSSED LINE!
  From: 380 (RIGHT) → To: 350 (LEFT)
  Line: 320, Tolerance: 40

[UI] Bottle detected at (350, 240)
[AI] Running detection...
```

---

## 🎯 **Test Checklist**

- [ ] Chai ở bên PHẢI (cx > 360)
- [ ] Chai di chuyển sang TRÁI
- [ ] Thấy GREEN box + arrow ←
- [ ] Chai đi qua line (cx <= 360)
- [ ] Thấy RED box + "CROSSING!"
- [ ] Terminal in: "✅ Bottle #X CROSSED LINE!"
- [ ] AI detection chạy
- [ ] Queue tăng +1
- [ ] Box chuyển GRAY (đã trigger)

---

## 🐛 **Troubleshooting**

### **Issue: Không trigger**

**Check:**
1. **Chai có ở bên PHẢI không?**
   ```python
   # Debug: In prev_cx
   print(f"prev_cx={prev_cx}, line_x={line_x}, threshold={line_x + tolerance}")
   # prev_cx phải > line_x + tolerance
   ```

2. **Chai có đi qua line không?**
   ```python
   # Debug: In cx
   print(f"cx={cx}, threshold={line_x + tolerance}")
   # cx phải <= line_x + tolerance
   ```

3. **Cooldown có hết chưa?**
   ```python
   # Check time
   print(f"Time since last: {current_time - self.last_detection_time}")
   ```

### **Issue: Trigger nhiều lần**

**Fix:** Logic đã có `tracked['crossed'] = True` để prevent double trigger

### **Issue: Không thấy chai**

**Fix:**
- Giảm `area_min`: 5000 → 3000
- Tăng `tolerance`: 40 → 60
- Check lighting

---

## 📝 **Summary**

✅ **Logic mới:**
- Track bottles với ID
- Chỉ trigger khi đi từ RIGHT → LEFT
- Mỗi chai chỉ trigger 1 lần
- Visual feedback rõ ràng

✅ **Cải thiện:**
- Reduced thresholds (dễ detect hơn)
- Increased tolerance (40px)
- Faster cooldown (0.8s)
- Better tracking

✅ **Debug:**
- Chi tiết logs
- Visual arrows
- Color coding

---

**Ready to test! 🚀**

