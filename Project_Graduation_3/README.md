# 🥤 Coca-Cola Sorting System - FIFO Queue Mode

**AI-Powered Quality Control using Raspberry Pi 5 & Arduino**

---

## 📋 Overview

This system uses **FIFO Queue Logic** with a **Virtual Line** at the camera position and a **Physical Trigger** (IR sensor) at the end of the conveyor.

### Key Features

- ✅ **Virtual Line Detection**: Camera detects bottles crossing a cyan line
- ✅ **NCNN AI Model**: Fast object detection with NMS
- ✅ **FIFO Queue**: Results queued at camera, processed at sensor
- ✅ **Real-time UI**: Tkinter interface with live video and queue visualization
- ✅ **Arduino Control**: Servo kicks NG bottles when triggered
- ✅ **SQLite Logging**: Complete history and statistics

---

## 🛠️ Hardware Setup

### Components

1. **Raspberry Pi 5** (8GB) - Main controller
2. **Arduino Uno** - Sensor and servo control
3. **Camera** - USB or Pi Camera
4. **IR Sensor** - Detects bottles (Digital Pin 2)
5. **Servo SG90** - Kicks NG bottles (Digital Pin 9)
6. **Relay** - Optional (for conveyor control)

### Physical Layout

```
[Camera] -----> [Conveyor Belt] -----> [IR Sensor] -> [Servo]
   |                                          |            |
Virtual Line                            Physical       Action
(Detection)                             Trigger        Point
```

### Wiring

**Arduino Connections:**
- IR Sensor: Pin 2 (INPUT_PULLUP)
- Servo Signal: Pin 9
- Servo VCC: 5V
- Servo GND: GND

**Raspberry Pi to Arduino:**
- USB Serial Connection

---

## 📦 Installation

### 1. Clone or Copy Project

```bash
cd /home/pi
cp -r Project_Graduation_3 ~/
cd ~/Project_Graduation_3
```

### 2. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Install NCNN (Raspberry Pi)

```bash
# Option 1: From package manager (if available)
sudo apt-get install python3-ncnn

# Option 2: Build from source
git clone https://github.com/Tencent/ncnn
cd ncnn
mkdir build && cd build
cmake ..
make -j4
sudo make install
```

### 4. Upload Arduino Code

1. Open `arduino/sorting_control.ino` in Arduino IDE
2. Select Board: "Arduino Uno"
3. Select Port (e.g., `/dev/ttyUSB0`)
4. Click Upload

### 5. Place Model Files

Copy your NCNN model files to `model/`:

```bash
model/
├── best.ncnn.param
└── best.ncnn.bin
```

---

## ⚙️ Configuration

Edit `config.py` to customize settings:

### Key Settings

```python
# Virtual Line Position
VIRTUAL_LINE_X = 320  # Pixel position (center of frame)
CROSSING_TOLERANCE = 20  # Pixels
DETECTION_COOLDOWN = 1.0  # Seconds

# AI Thresholds
CONFIDENCE_THRESHOLD = 0.5
NMS_THRESHOLD = 0.45

# Arduino Port
ARDUINO_PORT = '/dev/ttyUSB0'  # Linux
# ARDUINO_PORT = 'COM3'  # Windows
```

---

## 🚀 Usage

### Run the System

```bash
python3 main.py
```

### UI Instructions

1. **Click "START SYSTEM"**
   - Camera starts detecting bottles
   - Queue begins filling

2. **Virtual Line Detection**
   - Bottles crossing cyan line are detected
   - AI classifies each bottle
   - Results added to FIFO queue

3. **IR Sensor Trigger**
   - When bottle reaches sensor, it sends 'T'
   - Oldest result popped from queue
   - If NG → Servo kicks

4. **Monitor Queue**
   - Right panel shows current queue
   - Statistics display OK/NG counts

### Testing Without Hardware

```python
# In config.py
USE_DUMMY_CAMERA = True
USE_DUMMY_HARDWARE = True
```

---

## 🧠 AI Model Specifications

### Classes (8 Total)

| ID | Class Name       | Type    |
|----|------------------|---------|
| 0  | Cap-Defect       | Defect  |
| 1  | Filling-Defect   | Defect  |
| 2  | Label-Defect     | Defect  |
| 3  | Wrong-Product    | Defect  |
| 4  | cap              | Good    |
| 5  | coca             | Good    |
| 6  | filled           | Good    |
| 7  | label            | Good    |

### Sorting Logic

**NG (Not Good) if:**
- Any Defect (0-3) detected
- Missing `cap` (class 4)
- Missing `filled` (class 6)
- Missing `label` (class 7)

**OK otherwise**

### NMS (Non-Maximum Suppression)

Using `cv2.dnn.NMSBoxes`:
```python
indices = cv2.dnn.NMSBoxes(
    boxes,
    confidences,
    conf_threshold=0.5,
    nms_threshold=0.45
)
```

---

## 📊 File Structure

```
Project_Graduation_3/
├── arduino/
│   └── sorting_control.ino    # Arduino code
├── captures/
│   ├── ok/                    # OK snapshots
│   └── ng/                    # NG snapshots
├── core/
│   ├── __init__.py
│   ├── ai.py                  # NCNN + NMS implementation ⭐
│   ├── camera.py              # Threaded camera
│   ├── database.py            # SQLite handler
│   └── hardware.py            # Serial communication
├── database/
│   └── product.db             # Auto-created
├── model/
│   ├── best.ncnn.param        # NCNN model (you provide)
│   └── best.ncnn.bin          # NCNN model (you provide)
├── ui/
│   ├── __init__.py
│   ├── main_window.py         # Main UI with Virtual Line
│   └── history_window.py      # History viewer
├── config.py                  # Configuration ⚙️
├── main.py                    # Entry point
├── requirements.txt
└── README.md
```

---

## 🔧 Troubleshooting

### Issue: NCNN Not Found

**Solution:**
```bash
# System will use dummy fallback automatically
# To fix properly:
pip3 install ncnn  # or build from source
```

### Issue: Camera Not Opening

**Solution:**
```bash
# Check camera ID
ls /dev/video*

# Update config.py
CAMERA_ID = 0  # or 1, 2, etc.
```

### Issue: Arduino Not Detected

**Solution:**
```bash
# Check port
ls /dev/ttyUSB*
ls /dev/ttyACM*

# Update config.py
ARDUINO_PORT = '/dev/ttyUSB0'  # or /dev/ttyACM0

# Check permissions
sudo usermod -a -G dialout $USER
# Then logout and login
```

### Issue: Queue Mismatch

If bottles are kicked incorrectly, check:
1. **Cooldown**: Increase `DETECTION_COOLDOWN` if multiple detections occur
2. **Timing**: Ensure bottles reach sensor in same order as detected
3. **Queue Display**: Monitor queue to verify FIFO order

---

## 🎯 Calibration Tips

### 1. Virtual Line Position

Adjust `VIRTUAL_LINE_X` based on your camera view:
- Center (320): Good for symmetric detection
- Earlier (200): More time for processing
- Later (400): Less time but more accurate

### 2. Crossing Tolerance

Adjust `CROSSING_TOLERANCE`:
- Too small (5-10): May miss bottles
- Too large (30-50): May double-detect
- Recommended: 20 pixels

### 3. Detection Cooldown

Adjust `DETECTION_COOLDOWN`:
- Slower belt: 0.5s
- Medium belt: 1.0s (default)
- Fast belt: 1.5s

---

## 📸 Screenshots

*(Add your screenshots here)*

---

## 📝 License

MIT License - Feel free to use and modify

---

## 👨‍💻 Author

Final Year Project 2024

---

## 🙏 Acknowledgments

- NCNN by Tencent: https://github.com/Tencent/ncnn
- OpenCV: https://opencv.org/
- Python Serial: https://pyserial.readthedocs.io/

---

**Happy Sorting! 🥤✨**

