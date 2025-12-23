# FIX: Chai OK bị đẩy nhầm khi 2 chai đi gần nhau

## 🐛 VẤN ĐỀ

### Tình huống:
Có 2 chai đi gần nhau:
- **Chai 1**: OK (không lỗi)
- **Chai 2**: NG (có lỗi filling-defect)

### Kết quả SAI:
- Chai 1 (OK) BỊ ĐẨY ❌
- Chai 2 (NG) ĐƯỢC QUA ❌

### Nguyên nhân:
```
T1: Sensor 1 phát hiện Chai 1 → gửi 'D' → queue[0] = false, hasDecision[0] = false
T2: Sensor 1 phát hiện Chai 2 → gửi 'D' → queue[1] = false, hasDecision[1] = false
T3: Sensor 2 phát hiện Chai 1 → hasDecision[0] = false → CHO QUA (vì mặc định false = OK)
T4: Pi trả 'O' cho Chai 1 → hasDecision[0] = true ← ĐÃ MUỘN!
T5: Pi trả 'N' cho Chai 2 → queue[1] = true, hasDecision[1] = true
T6: Sensor 2 phát hiện Chai 2 → queue[1] = true → ĐẨY
```

**Vấn đề**: Chai đến Sensor 2 **TRƯỚC KHI** Pi kịp trả decision → mặc định cho qua (false = OK).

---

## ✅ GIẢI PHÁP: WAIT FOR DECISION

### Cơ chế mới:
Khi Sensor 2 phát hiện chai, **KIỂM TRA** xem Pi đã trả decision chưa:

```cpp
if (!hasDecision[queueHead]) {
    // Pi chưa trả lời → CHỜ tối đa 1 giây
    while (timeout not reached) {
        checkSerial();  // Đọc serial liên tục
        if (hasDecision[queueHead]) {
            // Nhận được decision → Break
            break;
        }
        delay(10);
    }
    
    if (still no decision) {
        // Timeout → Mặc định OK (cho qua)
    }
}

// Bây giờ đã có decision → Xử lý
if (pendingRejections[queueHead]) {
    KICK!
} else {
    PASS!
}
```

---

## 🔑 CÁC THAY ĐỔI TRONG CODE

### 1. Thêm tracking cho decision
```cpp
bool hasDecision[BUFFER_SIZE];  // Track if Pi has sent decision
unsigned long bottleTimestamp[BUFFER_SIZE];  // When bottle detected
const unsigned long DECISION_TIMEOUT = 1000;  // Wait max 1 second
```

### 2. Khi Sensor 1 phát hiện chai
```cpp
hasDecision[queueTail] = false;  // Chưa có decision
bottleTimestamp[queueTail] = detectionTime;  // Ghi timestamp
```

### 3. Khi Pi trả 'O' hoặc 'N'
```cpp
hasDecision[decisionIndex] = true;  // Đánh dấu đã có decision
```

### 4. **QUAN TRỌNG**: Khi Sensor 2 phát hiện chai
```cpp
if (!hasDecision[queueHead]) {
    // CHỜ decision từ Pi (tối đa 1s)
    while (millis() - waitStart < DECISION_TIMEOUT) {
        checkSerial();  // Đọc serial liên tục
        if (hasDecision[queueHead]) break;
        delay(10);
    }
}

// Bây giờ xử lý với decision đã có
if (pendingRejections[queueHead]) {
    KICK!
} else {
    PASS!
}
```

---

## 📊 WORKFLOW MỚI

### Case 1: Chai OK (Pi trả lời KỊP)
```
T1: Sensor 1 → queue[0] = false, hasDecision[0] = false
T2: Pi trả 'O' → hasDecision[0] = true, pendingRejections[0] = false
T3: Sensor 2 → hasDecision[0] = true → Check: false = OK → PASSING ✅
```

### Case 2: Chai NG (Pi trả lời KỊP)
```
T1: Sensor 1 → queue[0] = false, hasDecision[0] = false
T2: Pi trả 'N' → hasDecision[0] = true, pendingRejections[0] = true
T3: Sensor 2 → hasDecision[0] = true → Check: true = NG → KICKING ✅
```

### Case 3: Chai OK (Pi chưa trả lời - CASE CŨ LỖI)
```
T1: Sensor 1 → queue[0] = false, hasDecision[0] = false
T2: Sensor 2 → hasDecision[0] = FALSE!
    → CHỜ tối đa 1s...
    → Đọc serial liên tục...
    → Pi trả 'O' → hasDecision[0] = true
    → Break khỏi vòng chờ
    → Check: false = OK → PASSING ✅
```

### Case 4: 2 chai gần nhau (CASE CỦA BẠN)
```
T1: Sensor 1 → Chai 1: queue[0] = false, hasDecision[0] = false
T2: Sensor 1 → Chai 2: queue[1] = false, hasDecision[1] = false
T3: Sensor 2 → Chai 1: hasDecision[0] = FALSE!
    → CHỜ...
    → Pi trả 'O' cho Chai 1 → hasDecision[0] = true
    → Check: false = OK → PASSING ✅
T4: Pi trả 'N' cho Chai 2 → hasDecision[1] = true, queue[1] = true
T5: Sensor 2 → Chai 2: hasDecision[1] = true
    → Check: true = NG → KICKING ✅
```

---

## 🎯 TIMEOUT HANDLING

### Nếu Pi không trả lời trong 1 giây:
```
[Sensor 2] Bottle at index 0 detected → Waiting for Pi decision...
  [TIMEOUT] No decision from Pi → DEFAULT: OK → PASSING
```

**Lý do mặc định OK (cho qua):**
- An toàn hơn: tránh đẩy nhầm chai tốt
- Nếu Pi lỗi/treo, hệ thống vẫn cho chai qua thay vì đứng hẳn

**Có thể đổi thành mặc định NG (đẩy tất cả):**
```cpp
if (!gotDecision) {
    pendingRejections[queueHead] = true;  // Mặc định NG
}
```

---

## 📝 LOG DEBUG MỚI

### Log bình thường (Pi trả lời kịp):
```
[Sensor 1] Bottle at index 0 detected → AI triggered | Queue: 1
D,12345
[Pi Decision] OK → Bottle at index 0 will pass
[Sensor 2] Bottle at index 0 detected → OK → PASSING
```

### Log khi phải chờ:
```
[Sensor 1] Bottle at index 0 detected → AI triggered | Queue: 1
D,12345
[Sensor 2] Bottle at index 0 detected → Waiting for Pi decision...
[Pi Decision] OK → Bottle at index 0 will pass
  Decision received! → OK → PASSING
```

### Log timeout (Pi lỗi):
```
[Sensor 1] Bottle at index 0 detected → AI triggered | Queue: 1
D,12345
[Sensor 2] Bottle at index 0 detected → Waiting for Pi decision...
  [TIMEOUT] No decision from Pi → DEFAULT: OK → PASSING
```

### Log 2 chai gần nhau:
```
[Sensor 1] Bottle at index 0 detected → AI triggered | Queue: 1
D,12345
[Sensor 1] Bottle at index 1 detected → AI triggered | Queue: 2
D,12389
[Sensor 2] Bottle at index 0 detected → Waiting for Pi decision...
[Pi Decision] OK → Bottle at index 0 will pass
  Decision received! → OK → PASSING
[Pi Decision] NG → Bottle at index 1 marked for rejection | Queue: 1
[Sensor 2] Bottle at index 1 detected → NG → KICKING!
```

---

## ⚙️ PARAMETERS CÓ THỂ ĐIỀU CHỈNH

### DECISION_TIMEOUT (dòng 64)
```cpp
const unsigned long DECISION_TIMEOUT = 1000;  // 1 giây
```

**Điều chỉnh:**
- Nếu Pi **XỬ LÝ NHANH** (< 500ms): giảm xuống `500` hoặc `700`
- Nếu Pi **XỬ LÝ CHẬM** (> 1s): tăng lên `1500` hoặc `2000`
- **Không nên quá thấp** (< 300ms): Pi không kịp xử lý AI
- **Không nên quá cao** (> 3s): chai chờ lâu, hệ thống chậm

### Mặc định khi timeout
```cpp
// Hiện tại: Mặc định OK (cho qua)
pendingRejections[queueHead] = false;

// Có thể đổi thành: Mặc định NG (đẩy)
pendingRejections[queueHead] = true;
```

---

## 🧪 TESTING

### Test case quan trọng nhất: 2 CHAI GẦN NHAU

#### Setup:
1. Đặt 2 chai gần nhau (cách ~5-10cm)
2. Chai 1: OK (không lỗi)
3. Chai 2: NG (có lỗi)

#### Expected result:
```
✅ Chai 1 (OK) → QUA KHÔNG BỊ ĐẨY
✅ Chai 2 (NG) → BỊ ĐẨY RA
```

#### Log phải thấy:
```
[Sensor 1] Bottle at index 0 ...  ← Chai 1
[Sensor 1] Bottle at index 1 ...  ← Chai 2
[Sensor 2] ... index 0 → Waiting...  ← Chai 1 chờ decision
[Pi Decision] OK → index 0 ...  ← Pi trả OK cho Chai 1
  Decision received! → OK → PASSING  ← Chai 1 qua
[Pi Decision] NG → index 1 ...  ← Pi trả NG cho Chai 2
[Sensor 2] ... index 1 → NG → KICKING!  ← Chai 2 bị đẩy
```

### Nếu vẫn sai:
1. Kiểm tra Serial log xem decision có đúng index không
2. Kiểm tra thời gian Pi xử lý (nếu > 1s, tăng DECISION_TIMEOUT)
3. Kiểm tra Serial connection (baud rate, cable)

---

## 💡 TẠI SAO GIẢI PHÁP NÀY HIỆU QUẢ?

### Trước đây:
- **Asynchronous**: Arduino không chờ Pi, xử lý ngay khi Sensor 2 trigger
- **Race condition**: Nếu Pi chậm, chai đã qua Sensor 2 trước khi có decision

### Bây giờ:
- **Synchronous (có timeout)**: Arduino CHỜ Pi trả lời trước khi quyết định
- **No race condition**: Luôn có decision trước khi đẩy/cho qua
- **Fallback**: Nếu Pi lỗi, mặc định cho qua (không đứng hẳn)

---

## ⚠️ LƯU Ý

1. **DECISION_TIMEOUT = 1s là hợp lý**
   - Pi xử lý AI thường < 500ms
   - 1s đủ buffer cho Pi chậm hoặc load cao

2. **Không nên timeout quá thấp**
   - < 300ms: Pi không kịp
   - Sẽ gặp nhiều timeout → mặc định OK/NG

3. **Khoảng cách Sensor 1 - Sensor 2**
   - Nếu quá gần: chai đến Sensor 2 quá nhanh
   - Nên có ít nhất 1-1.5 giây giữa 2 sensor

4. **Nếu hệ thống vẫn đẩy sai:**
   - Tăng DECISION_TIMEOUT lên 1500 hoặc 2000
   - Kiểm tra Python có gửi 'O'/'N' đúng thứ tự không
   - Kiểm tra Serial baud rate (phải là 9600)

---

*Cập nhật: 2025-12-17 | Wait-for-Decision Fix*

