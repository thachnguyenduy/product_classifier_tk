# Sơ Đồ Hệ Thống

## 📊 Kiến Trúc Tổng Quan

```
┌─────────────────────────────────────────────────────────────┐
│                    RASPBERRY PI 5 (8GB)                     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Camera     │  │   YOLOv8     │  │   Tkinter    │    │
│  │   Module     │→ │   AI Model   │→ │     GUI      │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                           ↓                                 │
│                    ┌──────────────┐                        │
│                    │   Hardware   │                        │
│                    │  Controller  │                        │
│                    └──────┬───────┘                        │
└───────────────────────────┼─────────────────────────────────┘
                            │ USB Serial
                            │ /dev/ttyACM0
                            │ 115200 baud
┌───────────────────────────┼─────────────────────────────────┐
│                    ARDUINO UNO                              │
│                                                             │
│  Pin D7 ──→ Relay ──→ Motor 12V ──→ Băng chuyền          │
│  Pin D9 ──→ Servo SG90 ──→ Gạt sản phẩm lỗi              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Luồng Xử Lý

```
[1] Camera chụp ảnh
        ↓
[2] YOLOv8 phân tích
        ↓
[3] Phát hiện classes:
    • cap, coca, filled, label → GOOD ✅
    • Cap-Defect, Filling-Defect, Label-Defect, Wrong-Product → BAD ❌
        ↓
[4] Nếu GOOD:
    → Không làm gì
    → Lưu vào database
        ↓
[5] Nếu BAD:
    → Gửi lệnh "EJECT" tới Arduino
    → Lưu vào database
        ↓
[6] Arduino thực hiện:
    [a] RELAY_OFF → Dừng băng chuyền (300ms)
    [b] SERVO_LEFT → Gạt sản phẩm (800ms)
    [c] SERVO_CENTER → Trả servo về (500ms)
    [d] RELAY_ON → Chạy băng chuyền
        ↓
[7] Quay lại bước [1]
```

## 🗂️ Cấu Trúc Code

```
product_classifier_tk/
│
├── main.py                    # Entry point
│   └─→ Khởi tạo GUI, camera, AI, database, hardware
│
├── ui/                        # Giao diện Tkinter
│   ├── main_window.py        # Cửa sổ chính
│   │   ├─→ Hiển thị camera realtime
│   │   ├─→ Vẽ bounding boxes
│   │   ├─→ Buttons điều khiển
│   │   └─→ Status bar (FPS, Result, Confidence)
│   │
│   └── history_window.py     # Cửa sổ lịch sử
│       ├─→ Hiển thị database
│       ├─→ Filter GOOD/BAD
│       └─→ Export CSV
│
├── core/                      # Core modules
│   ├── camera.py             # Camera streaming
│   │   └─→ Thread đọc frame liên tục
│   │
│   ├── ai.py                 # YOLOv8 inference
│   │   ├─→ Load model
│   │   ├─→ Predict frame
│   │   └─→ Phân loại GOOD/BAD
│   │
│   ├── database.py           # SQLite operations
│   │   ├─→ Insert result
│   │   ├─→ Fetch results
│   │   └─→ Export CSV
│   │
│   └── hardware.py           # Arduino controller
│       ├─→ Serial communication
│       ├─→ start_conveyor()
│       ├─→ stop_conveyor()
│       └─→ eject_bad_product()
│
├── arduino/                   # Arduino code
│   ├── product_sorter.ino    # Main sketch
│   │   ├─→ Nhận lệnh serial
│   │   ├─→ Điều khiển relay (D7)
│   │   └─→ Điều khiển servo (D9)
│   │
│   └── README.md             # Hướng dẫn Arduino
│
├── model/
│   └── my_model.pt           # YOLOv8 trained model
│
├── database/
│   └── products.db           # SQLite database
│
└── captures/                  # Ảnh đã chụp
```

## 🔌 Giao Tiếp Serial

### Raspberry Pi → Arduino:
```python
# Trong core/hardware.py
serial_conn.write(b"RELAY_ON\n")
serial_conn.write(b"EJECT\n")
```

### Arduino → Raspberry Pi:
```cpp
// Trong arduino/product_sorter.ino
Serial.println("OK: Conveyor started");
Serial.println("Eject sequence complete");
```

## 📊 Database Schema

```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    result TEXT,           -- "GOOD" hoặc "BAD"
    confidence REAL        -- 0.0 - 1.0
);
```

## 🎯 Classes trong Model

### Normal Parts (GOOD):
| Class | Ý nghĩa | Box Color |
|-------|---------|-----------|
| cap | Nắp chai OK | 🟢 Xanh |
| coca | Chai Coca | 🟢 Xanh |
| filled | Nước đầy đủ | 🟢 Xanh |
| label | Nhãn dán OK | 🟢 Xanh |

### Defects (BAD):
| Class | Ý nghĩa | Box Color |
|-------|---------|-----------|
| Cap-Defect | Nắp lỗi | 🔴 Đỏ |
| Filling-Defect | Nước thiếu | 🔴 Đỏ |
| Label-Defect | Nhãn lỗi | 🔴 Đỏ |
| Wrong-Product | Sản phẩm sai | 🔴 Đỏ |

## ⚡ Hardware Actions

### Start Conveyor:
```
Python: hw.start_conveyor()
   ↓
Serial: "RELAY_ON\n"
   ↓
Arduino: digitalWrite(RELAY_PIN, HIGH)
   ↓
Relay: ON → Motor chạy
```

### Eject Bad Product:
```
Python: hw.eject_bad_product()
   ↓
Serial: "EJECT\n"
   ↓
Arduino: ejectBadProduct()
   ├─→ RELAY_OFF (dừng băng chuyền)
   ├─→ SERVO_LEFT (gạt sản phẩm)
   ├─→ SERVO_CENTER (trả về)
   └─→ RELAY_ON (chạy băng chuyền)
```

## 🖥️ GUI Layout

```
┌─────────────────────────────────────────────────────────┐
│  File    Tools    View                                  │ Menu Bar
├──────────────────────────────┬──────────────────────────┤
│                              │  [Start Camera]          │
│                              │  [Stop Camera]           │
│                              │  [Start Detection]       │
│      Camera Feed             │  [Stop Detection]        │
│      (640x480)               │  [Start Conveyor]        │
│                              │  [Stop Conveyor]         │
│   🟢 cap (0.92)              │                          │
│   🟢 filled (0.88)           │  ─────────────────       │
│   🔴 Cap-Defect (0.85)       │  [History]               │
│                              │  [Hardware test]         │
├──────────────────────────────┴──────────────────────────┤
│ FPS: 28.5 | Result: BAD | Confidence: 0.85             │ Status Bar
└─────────────────────────────────────────────────────────┘
```

## 🔄 Threading Model

```
Main Thread (Tkinter)
├─→ GUI rendering
├─→ Button handlers
└─→ Update loop (50ms)

Camera Thread
├─→ Đọc frame liên tục
└─→ Tính FPS

Detection Thread (khi enabled)
├─→ Copy frame
├─→ Run YOLOv8
├─→ Update UI
└─→ Trigger hardware (nếu BAD)

Hardware Thread
└─→ Gửi lệnh serial tới Arduino
```

## 📈 Performance

### Raspberry Pi 5:
- **YOLOv8n**: ~15-20 FPS
- **YOLOv8s**: ~10-15 FPS
- **YOLOv8m**: ~5-10 FPS

### Arduino Uno:
- **Serial latency**: <10ms
- **Relay response**: ~5ms
- **Servo movement**: 100-500ms

### Total eject time:
```
300ms (stop) + 800ms (eject) + 500ms (return) = ~1.6 seconds
```

## 🔒 Safety Features

1. **Cleanup on exit**: Dừng băng chuyền, trả servo về giữa
2. **Exception handling**: Tất cả hardware calls có try/except
3. **Simulation mode**: Chạy được trên Windows (không có hardware)
4. **Serial timeout**: 1 second để tránh block
5. **Thread safety**: Lock cho camera frame access

## 📚 Tài Liệu Liên Quan

- `README.md` - Hướng dẫn tổng quan
- `HARDWARE_SETUP.md` - Chi tiết kết nối phần cứng
- `CLASSIFICATION_LOGIC.md` - Logic phân loại chi tiết
- `QUICK_START.md` - Hướng dẫn nhanh
- `arduino/README.md` - Hướng dẫn Arduino

