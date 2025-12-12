# Coca-Cola Bottle Sorting System

**Graduation Project - Industrial AI Quality Control**

---

## 📋 Project Overview

An AI-powered quality control system for Coca-Cola bottle sorting using computer vision, object tracking, and line crossing detection. The system automatically classifies bottles as OK or NG (Not Good) based on detected defects and component presence.

### Key Features

- ✅ Real-time AI detection using YOLO
- 🎯 Object tracking with unique IDs
- 📏 Software-based line crossing detection
- 🤖 Automated classification (OK/NG)
- 🔌 Arduino integration for physical control
- 💾 SQLite database for result logging
- 🖥️ Tkinter-based user interface
- 📸 Automatic snapshot capture

---

## 🏗️ System Architecture

### Hardware Components

- **Raspberry Pi 5 (8GB)**: Main controller
  - AI inference
  - Object tracking
  - Line crossing detection
  - Database management
  - UI display

- **Arduino Uno**: Physical hardware controller
  - IR sensor reading
  - Servo motor control
  - Relay control (conveyor)

- **USB Camera**: Video capture
- **IR Sensor**: Physical bottle detection
- **Servo 9g**: NG bottle blocking
- **Relay 5V**: Conveyor control

### Conveyor Direction

```
    RIGHT ─────→─────→─────→ LEFT
                   |
             Virtual Line
          (Classification Point)
```

Bottles move from **RIGHT to LEFT** in the camera frame.

---

## 🧠 AI Model & Classification

### Class Names (EXACT ORDER - DO NOT CHANGE)

```python
CLASS_NAMES = [
    'Cap-Defect',      # 0 - Defect
    'Filling-Defect',  # 1 - Defect
    'Label-Defect',    # 2 - Defect
    'Wrong-Product',   # 3 - Defect
    'cap',             # 4 - Good component
    'coca',            # 5 - Identity (NOT for classification)
    'filled',          # 6 - Good component
    'label'            # 7 - Good component
]
```

### Classification Logic (CRITICAL)

**Result = NG (Not Good) if:**
- ANY defect class detected (Cap-Defect, Filling-Defect, Label-Defect, Wrong-Product)
- ANY good component missing (cap, filled, label)

**Result = OK if:**
- ALL good classes present (cap + filled + label)
- NO defects detected

**Important Notes:**
- `coca` class is used ONLY for product identity confirmation
- `coca` MUST NOT be used alone for OK/NG classification
- DO NOT use confidence scores for classification
- Classification is based ONLY on detected class labels

---

## 🎯 Line Crossing Detection

### Virtual Line Concept

A vertical line is drawn at `x = VIRTUAL_LINE_X` (default: 320 pixels).

### Detection Logic

1. **Before Line**: Bottle is on the RIGHT side
   - AI continuously detects and tracks bottle
   - Accumulates all detected class names
   - No classification yet

2. **Crossing Line**: Bottle moves from RIGHT to LEFT
   - Previous x-position > line_x
   - Current x-position ≤ line_x
   - **Classification is FINALIZED**
   - **Result is LOCKED** (no further changes)

3. **After Line**: Bottle is on the LEFT side
   - Classification result sent to Arduino ('O' or 'N')
   - Added to queue for IR sensor processing

### Tracking Rules

- Each bottle has unique `object_id`
- Multiple detections within 100 pixels are grouped (same bottle)
- Objects not seen for 3 seconds are removed
- Classification happens ONLY at line crossing

---

## 🔌 Communication Protocol

### Raspberry Pi → Arduino

| Command | Meaning | Action |
|---------|---------|--------|
| `'O'` | OK product | Servo allows bottle to pass |
| `'N'` | NG product | Servo blocks bottle |
| `'S'` | Start | Conveyor starts running |
| `'P'` | Pause | Conveyor stops |

### Arduino → Raspberry Pi

| Command | Meaning | Action |
|---------|---------|--------|
| `'T'` | Trigger | IR sensor detected bottle |

### System Flow

```
1. Bottle enters from RIGHT
2. AI tracks bottle, accumulates detections
3. Bottle crosses virtual line
4. Classification finalized → Send 'O' or 'N' to Arduino
5. Bottle continues moving LEFT
6. IR sensor triggers → Arduino actuates servo
7. Servo blocks NG bottles, allows OK bottles
```

---

## 📁 Project Structure

```
Project_Graduation_3/
├── arduino/
│   └── arduino.ino          # Arduino controller code
├── captures/
│   ├── ok/                  # OK product images
│   └── ng/                  # NG product images
├── core/
│   ├── ai.py               # YOLO detection + tracking + line crossing
│   ├── camera.py           # USB camera handling
│   ├── hardware.py         # Serial communication with Arduino
│   └── database.py         # SQLite database
├── database/
│   └── product.db          # SQLite database file
├── model/
│   └── best.pt             # YOLO model (current)
├── ui/
│   ├── main_window.py      # Main Tkinter window
│   └── history_window.py   # History viewer
├── config.py               # Configuration settings
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

---

## 🚀 Installation & Setup

### 1. System Requirements

- Raspberry Pi 5 (8GB) with Raspberry Pi OS
- Python 3.8 or higher
- Arduino Uno with USB cable
- USB Camera

### 2. Install Python Dependencies

```bash
cd Project_Graduation_3
pip3 install -r requirements.txt
```

### 3. Arduino Setup

1. Open `arduino/arduino.ino` in Arduino IDE
2. Select board: **Arduino Uno**
3. Select correct port (e.g., `/dev/ttyUSB0`)
4. Upload code to Arduino

### 4. Configure Serial Port

Edit `config.py`:

```python
ARDUINO_PORT = '/dev/ttyUSB0'  # Change if different
```

To find Arduino port:
```bash
ls /dev/ttyUSB*
# or
ls /dev/ttyACM*
```

### 5. Camera Configuration

Edit `config.py`:

```python
CAMERA_ID = 0  # Change if using different camera
```

---

## ▶️ Running the System

### Start System

```bash
python3 main.py
```

### UI Instructions

1. Click **"START SYSTEM"** button
2. Conveyor will start automatically
3. Place bottles on conveyor (moving RIGHT → LEFT)
4. Watch real-time detection and classification
5. Results are logged to database
6. Click **"STOP SYSTEM"** to pause
7. Click **"View History"** to see past results

---

## 🧪 Testing Mode

For testing without hardware, edit `config.py`:

```python
USE_DUMMY_CAMERA = True     # Test without camera
USE_DUMMY_HARDWARE = True   # Test without Arduino
```

---

## 🛠️ Configuration

Key settings in `config.py`:

### AI Model
```python
MODEL_PATH_YOLO = "model/best.pt"
CONFIDENCE_THRESHOLD = 0.25
```

### Line Crossing
```python
VIRTUAL_LINE_X = 320        # X position of virtual line
CROSSING_TOLERANCE = 10     # Detection tolerance (pixels)
```

### Hardware
```python
ARDUINO_PORT = '/dev/ttyUSB0'
ARDUINO_BAUDRATE = 9600
PIN_IR_SENSOR = 2
PIN_SERVO = 9
PIN_RELAY = 4
```

---

## 📊 Database Schema

### Inspections Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| timestamp | TEXT | Detection timestamp |
| object_id | INTEGER | Tracking ID |
| detected_labels | TEXT | Detected class names |
| result | TEXT | 'OK' or 'NG' |
| reason | TEXT | Classification reason |
| image_path | TEXT | Saved image path |
| processing_time | REAL | Processing time (seconds) |

### Statistics Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| date | TEXT | Date (YYYY-MM-DD) |
| total_count | INTEGER | Total bottles |
| ok_count | INTEGER | OK bottles |
| ng_count | INTEGER | NG bottles |

---

## 🚨 Troubleshooting

### Camera Not Opening
```bash
# Check camera
ls /dev/video*

# Test camera
v4l2-ctl --list-devices
```

### Arduino Not Connecting
```bash
# Check port
ls /dev/ttyUSB* /dev/ttyACM*

# Check permissions
sudo usermod -a -G dialout $USER
# Then reboot
```

### YOLO Model Not Loading
- Ensure `model/best.pt` exists
- Check file permissions
- Install ultralytics: `pip3 install ultralytics`

### Serial Communication Issues
- Check baudrate matches (9600)
- Verify Arduino is not already open in IDE Serial Monitor
- Check USB cable quality

---

## 📝 Important Notes

### Class Names
⚠️ **DO NOT** change class names or order in `config.py`. They must match exactly with the trained model.

### Conveyor Direction
⚠️ **MUST** be RIGHT → LEFT. Do not reverse direction or change line crossing logic.

### Classification Logic
⚠️ **DO NOT** modify classification rules. They follow exact industrial requirements:
- NG if ANY defect
- OK if ALL good components present and NO defects

### Future Upgrade
🔄 NCNN model will replace YOLO in the future **WITHOUT changing any logic**. The system is designed to be model-agnostic.

---

## 👥 Project Team

**Graduation Project**

- Hardware: Raspberry Pi 5, Arduino Uno
- Software: Python, Tkinter, OpenCV, YOLO
- Database: SQLite
- Communication: Serial (USB)

---

## 📄 License

Educational project for graduation thesis.

---

## 📞 Support

For issues or questions:
1. Check this README
2. Review code comments
3. Check `config.py` settings
4. Test in DUMMY mode first

---

## 🎓 Graduation Defense Notes

Key points for defense:

1. **Industrial Logic**: System follows real industrial quality control processes
2. **Software Sensor**: Virtual line crossing eliminates need for physical sensor
3. **Tracking**: Unique IDs prevent duplicate detection
4. **Classification Rules**: Based on detected classes, not confidence scores
5. **Scalability**: Easy to add more classes or change rules
6. **Real-time**: Continuous operation without stopping conveyor
7. **Database**: All results logged for quality analysis
8. **Hardware Integration**: Raspberry Pi + Arduino cooperation

---

**END OF README**

