# GIẢI THÍCH LOGIC FIFO (First In, First Out)

## 🐛 VẤN ĐỀ TRƯỚC ĐÂY

### Tình huống:
Có 2 chai cùng lúc trên băng chuyền:

```
[Chai 1 OK] → [Chai 2 NG] → đang chạy về phía servo
```

### Bug cũ:
1. Sensor 1 phát hiện Chai 1 → thêm vào queue[0] = false (OK)
2. Sensor 1 phát hiện Chai 2 → thêm vào queue[1] = false (OK)
3. Pi xử lý Chai 1 → trả 'O' (OK) ✅
4. Pi xử lý Chai 2 → trả 'N' (NG)
5. **BUG**: Code đánh dấu `queue[queueTail-1]` = queue[1] = true
   - Nhưng queue[1] là Chai 2, đúng!
6. Sensor 2 phát hiện Chai 1 → kiểm tra queue[queueHead] = queue[0] = false → CHO QUA ✅
7. Sensor 2 phát hiện Chai 2 → kiểm tra queue[1] = true → ĐẨY ✅

**Tưởng như đúng? KHÔNG!** Nếu Pi xử lý chậm:

1. Sensor 1: Chai 1 → queue[0] = false
2. **Sensor 1: Chai 2 → queue[1] = false** (Pi chưa trả lời cho Chai 1)
3. **Pi trả 'N' cho Chai 1** → Code đánh dấu queue[queueTail-1] = **queue[1] = true** ← SAI!
4. Sensor 2: Chai 1 → queue[0] = false → **CHO QUA** ← SAI! Pi đã bảo NG!
5. Sensor 2: Chai 2 → queue[1] = true → **ĐẨY** ← SAI! Chai 2 là OK!

**Kết quả: Chai OK bị đẩy, chai NG được qua → SAI NGƯỢC!!!**

---

## ✅ GIẢI PHÁP MỚI: FIFO với `decisionIndex`

### Cơ chế:
Thêm 3 con trỏ (pointers):

```
queueHead        : Chai tiếp theo sẽ đến Sensor 2 (oldest)
decisionIndex    : Chai tiếp theo đang chờ Pi trả lời
queueTail        : Vị trí để thêm chai mới (newest)
```

### Luồng hoạt động:

```
[Sensor 1] → Add to queue → [Waiting for Pi] → [Sensor 2] → Remove from queue
             queueTail++      decisionIndex       queueHead++
```

### Ví dụ cụ thể:

#### **T0: Ban đầu**
```
Queue: [ empty, empty, empty, ... ]
queueHead = 0
decisionIndex = 0
queueTail = 0
queueCount = 0
```

#### **T1: Sensor 1 phát hiện Chai 1**
```
Queue: [ false(Chai1), empty, empty, ... ]
           ^
         queueTail
queueHead = 0
decisionIndex = 0  ← Chai 1 đang chờ Pi
queueTail = 1
queueCount = 1
```

#### **T2: Sensor 1 phát hiện Chai 2** (Pi chưa trả lời Chai 1)
```
Queue: [ false(Chai1), false(Chai2), empty, ... ]
         ^             ^
     queueHead     queueTail
decisionIndex = 0  ← Chai 1 vẫn đang chờ Pi
queueTail = 2
queueCount = 2
```

#### **T3: Pi trả 'O' cho Chai 1**
```
Queue: [ false(Chai1=OK), false(Chai2), empty, ... ]
         ^
     queueHead
decisionIndex = 1  ← Di chuyển sang Chai 2
queueTail = 2
queueCount = 2
```

#### **T4: Pi trả 'N' cho Chai 2**
```
Queue: [ false(Chai1=OK), TRUE(Chai2=NG), empty, ... ]
         ^
     queueHead
decisionIndex = 2  ← Di chuyển sang chai tiếp theo
queueTail = 2
queueCount = 2
```

#### **T5: Sensor 2 phát hiện Chai 1**
```
Kiểm tra: queue[queueHead=0] = false → OK → CHO QUA ✅
Queue: [ REMOVED, true(Chai2=NG), empty, ... ]
                  ^
              queueHead (moved)
queueHead = 1
decisionIndex = 2
queueTail = 2
queueCount = 1
```

#### **T6: Sensor 2 phát hiện Chai 2**
```
Kiểm tra: queue[queueHead=1] = true → NG → ĐẨY ✅
Queue: [ REMOVED, REMOVED, empty, ... ]
                           ^
                       queueHead
queueHead = 2
decisionIndex = 2
queueTail = 2
queueCount = 0
```

---

## 🔑 CÁC NGUYÊN TẮC QUAN TRỌNG

### 1. **FIFO Strict (Thứ tự nghiêm ngặt)**
- Pi **PHẢI** trả lời theo đúng thứ tự chai được phát hiện
- Nếu Pi nhận D1, D2, D3 → Phải trả O/N cho D1, sau đó D2, sau đó D3

### 2. **decisionIndex luôn giữa queueHead và queueTail**
```
queueHead ≤ decisionIndex ≤ queueTail (trong circular buffer)
```

- `queueHead`: Chai đã có decision, đang đợi Sensor 2
- `decisionIndex`: Chai đang chờ Pi trả lời
- `queueTail`: Vị trí để thêm chai mới

### 3. **Mỗi decision ('O' hoặc 'N') đều di chuyển decisionIndex**
- Không phân biệt OK hay NG
- Luôn áp dụng cho chai tại `decisionIndex`
- Sau đó `decisionIndex++`

### 4. **Sensor 2 chỉ kiểm tra queueHead**
- Không quan tâm `decisionIndex` hoặc `queueTail`
- Chỉ xử lý chai đã có decision (giữa queueHead và decisionIndex)

---

## 📊 DEBUG OUTPUT

### Log format mới:
```
[Sensor 1] Bottle detected → AI triggered | Queue: 1
D,12345

[Pi Decision] OK → Bottle at index 0 will pass
[Pi Decision] NG → Bottle at index 1 marked for rejection | Queue: 2

[Sensor 2] Bottle at index 0 detected → OK → PASSING
[Sensor 2] Bottle at index 1 detected → NG → KICKING!
```

### Cách đọc:
- **"at index X"**: Vị trí chai trong circular buffer (0-19)
- **Queue count**: Tổng số chai đang trong hệ thống
- **OK → PASSING**: Chai OK, không đẩy
- **NG → KICKING**: Chai NG, đẩy ra

---

## ⚠️ LƯU Ý

### Điều kiện để hệ thống hoạt động đúng:

1. **Khoảng cách Sensor 1 - Sensor 2 đủ lớn**
   - Phải đủ thời gian để Pi xử lý AI (~500-1000ms)
   - Nếu chai chạy quá nhanh → tăng khoảng cách hoặc giảm tốc băng chuyền

2. **Pi trả lời theo đúng thứ tự**
   - Python code đã xử lý đúng FIFO
   - Mỗi 'D' nhận được → xử lý → trả 'O' hoặc 'N'

3. **Không có chai vượt nhau**
   - Chai phải chạy theo thứ tự trên băng chuyền
   - Không có chai nào vượt chai trước nó

4. **Buffer đủ lớn**
   - BUFFER_SIZE = 20 đủ cho hầu hết trường hợp
   - Nếu chai chạy rất nhanh → tăng lên 30

---

## 🧪 TESTING

### Test case 1: 1 chai OK
```
Expected:
[Sensor 1] → [Pi OK] → [Sensor 2] → PASSING ✅
```

### Test case 2: 1 chai NG
```
Expected:
[Sensor 1] → [Pi NG] → [Sensor 2] → KICKING ✅
```

### Test case 3: 2 chai OK, OK
```
Expected:
[Sensor 1] Chai1 → [Pi OK] → [Sensor 2] Chai1 → PASSING ✅
[Sensor 1] Chai2 → [Pi OK] → [Sensor 2] Chai2 → PASSING ✅
```

### Test case 4: 2 chai OK, NG
```
Expected:
[Sensor 1] Chai1 → [Pi OK] → [Sensor 2] Chai1 → PASSING ✅
[Sensor 1] Chai2 → [Pi NG] → [Sensor 2] Chai2 → KICKING ✅
```

### Test case 5: 2 chai NG, OK
```
Expected:
[Sensor 1] Chai1 → [Pi NG] → [Sensor 2] Chai1 → KICKING ✅
[Sensor 1] Chai2 → [Pi OK] → [Sensor 2] Chai2 → PASSING ✅
```

### Test case 6: Pi chậm (Sensor 1 phát hiện cả 2 chai trước khi Pi trả lời)
```
Expected:
[Sensor 1] Chai1 (queue[0])
[Sensor 1] Chai2 (queue[1])
[Pi OK] → mark queue[0] = false, decisionIndex → 1
[Pi NG] → mark queue[1] = true, decisionIndex → 2
[Sensor 2] Chai1 → queue[0] = false → PASSING ✅
[Sensor 2] Chai2 → queue[1] = true → KICKING ✅
```

---

*Cập nhật: 2025-12-17 | FIFO Logic with decisionIndex*

