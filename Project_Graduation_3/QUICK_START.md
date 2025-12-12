# Quick Start Guide
## Coca-Cola Bottle Sorting System

---

## ⚡ 5-Minute Setup

### 1. Hardware Connection

```
┌─────────────────┐
│  Raspberry Pi 5 │
│     (8GB)       │
└────┬──────┬─────┘
     │      │
     │      └─────────────┐
     │                    │
┌────▼─────┐      ┌──────▼──────┐
│USB Camera│      │Arduino Uno  │
└──────────┘      └─┬────┬────┬─┘
                    │    │    │
              ┌─────┘    │    └──────┐
              │          │           │
          ┌───▼──┐   ┌──▼───┐   ┌──▼───┐
          │IR    │   │Servo │   │Relay │
          │Sensor│   │(Pin9)│   │(Pin4)│
          │(Pin2)│   └──────┘   └──┬───┘
          └──────┘                 │
                              ┌────▼────┐
                              │Conveyor │
                              │  Belt   │
                              └─────────┘
```

### 2. Software Installation

```bash
cd Project_Graduation_3
pip3 install -r requirements.txt
```

### 3. Configure Arduino Port

```bash
# Find Arduino port
ls /dev/ttyUSB*

# Edit config.py
nano config.py
# Change: ARDUINO_PORT = '/dev/ttyUSB0'
```

### 4. Upload Arduino Code

1. Open Arduino IDE
2. Open `arduino/arduino.ino`
3. Select Board: Arduino Uno
4. Select Port: /dev/ttyUSB0
5. Click Upload

### 5. Run System

```bash
python3 main.py
```

---

## 🎮 How to Use

### Step 1: Start System
1. Click **"START SYSTEM"** button
2. Conveyor will start automatically
3. Green status bar shows "RUNNING"

### Step 2: Place Bottles
- Put bottles on RIGHT side of conveyor
- Bottles will move RIGHT → LEFT
- Watch them cross the cyan line

### Step 3: View Results
- Real-time classification shown
- Statistics update automatically
- Images saved to `captures/` folder

### Step 4: View History
- Click **"View History"** button
- See all past inspections
- Export data if needed

### Step 5: Stop System
- Click **"STOP SYSTEM"** button
- Conveyor will stop
- System ready to restart

---

## 🚨 Troubleshooting

### Camera Not Working
```bash
# Check camera
ls /dev/video*

# Test camera
python3 -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

**Fix:**
- Plug/unplug USB camera
- Change `CAMERA_ID` in config.py
- Set `USE_DUMMY_CAMERA = True` for testing

---

### Arduino Not Connecting
```bash
# Check port
ls /dev/ttyUSB* /dev/ttyACM*

# Check permissions
sudo usermod -a -G dialout $USER
sudo reboot
```

**Fix:**
- Check USB cable
- Re-upload Arduino code
- Change `ARDUINO_PORT` in config.py
- Set `USE_DUMMY_HARDWARE = True` for testing

---

### Model Not Loading
**Error:** `Model file not found`

**Fix:**
```bash
# Check model exists
ls model/best.pt

# Download or retrain model
# Place in model/best.pt
```

---

### System Running Slow
**Symptoms:** Laggy video, slow detection

**Fix:**
1. Lower resolution in config.py:
```python
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240
```

2. Increase confidence threshold:
```python
CONFIDENCE_THRESHOLD = 0.35
```

3. Close other programs

---

## 📝 Default Settings

### Virtual Line
- **Position:** X = 320 (center of 640px)
- **Direction:** RIGHT → LEFT
- **Adjust in:** `config.py` → `VIRTUAL_LINE_X`

### Detection
- **Confidence:** 0.25 (25%)
- **NMS:** 0.45 (45%)
- **Adjust in:** `config.py`

### Serial
- **Port:** /dev/ttyUSB0
- **Baudrate:** 9600
- **Adjust in:** `config.py` → `ARDUINO_PORT`

---

## 🎯 Classification Rules

### OK Product
✅ Must have ALL:
- `cap`
- `filled`
- `label`

✅ Must have NONE:
- `Cap-Defect`
- `Filling-Defect`
- `Label-Defect`
- `Wrong-Product`

### NG Product
❌ If ANY defect detected
❌ If ANY good component missing

---

## 📂 Important Files

| File | Purpose |
|------|---------|
| `main.py` | Run this to start system |
| `config.py` | All settings here |
| `arduino/arduino.ino` | Upload to Arduino |
| `model/best.pt` | YOLO model file |
| `database/product.db` | Results database |
| `captures/ok/` | OK product images |
| `captures/ng/` | NG product images |

---

## 🧪 Testing Mode

For testing without hardware:

**Edit `config.py`:**
```python
USE_DUMMY_CAMERA = True     # Simulate camera
USE_DUMMY_HARDWARE = True   # Simulate Arduino
```

**Run:**
```bash
python3 main.py
```

System will run with simulated data for UI testing.

---

## 📊 Where to Find Results

### Real-time
- **UI:** Main window shows live results
- **Console:** Detailed logs printed

### Historical
- **Database:** `database/product.db`
- **Images:** `captures/ok/` and `captures/ng/`
- **UI:** Click "View History" button

### Export Data
```bash
# Using SQLite
sqlite3 database/product.db

# View all records
SELECT * FROM inspections ORDER BY id DESC LIMIT 10;

# Export to CSV
.mode csv
.output results.csv
SELECT * FROM inspections;
.quit
```

---

## 🔧 Common Adjustments

### Change Line Position
```python
# config.py
VIRTUAL_LINE_X = 400  # Move right
VIRTUAL_LINE_X = 200  # Move left
```

### Change Detection Sensitivity
```python
# config.py
CONFIDENCE_THRESHOLD = 0.15  # More sensitive (more detections)
CONFIDENCE_THRESHOLD = 0.40  # Less sensitive (fewer detections)
```

### Change Servo Position
```arduino
// arduino.ino
const int SERVO_IDLE = 0;      // Adjust idle position
const int SERVO_BLOCK = 120;   // Adjust block position
```

---

## 💡 Tips for Best Results

### Camera Position
- ✅ Good lighting (no shadows)
- ✅ Fixed position (no shaking)
- ✅ Clear view of bottles
- ✅ Height: 30-50cm above conveyor

### Conveyor Speed
- ✅ Moderate speed (not too fast)
- ✅ Consistent (no jerking)
- ✅ Adjust line position if needed

### Bottle Placement
- ✅ Upright position
- ✅ Single file (not overlapping)
- ✅ Enter from RIGHT side

---

## 📞 Need Help?

### Check These First:
1. ✅ All cables connected?
2. ✅ Arduino code uploaded?
3. ✅ Model file exists?
4. ✅ Camera working?
5. ✅ Correct port in config?

### Debug Mode:
```python
# config.py
DEBUG_MODE = True
VERBOSE_LOGGING = True
```

This will print detailed information to console.

---

## 🎓 For Graduation Defense

### Prepare:
1. ✅ Test system completely
2. ✅ Prepare sample bottles (OK and NG)
3. ✅ Clean database or prepare demo data
4. ✅ Check lighting in demo room
5. ✅ Have backup plan (dummy mode)

### Demo Checklist:
- [ ] Power on Raspberry Pi
- [ ] Connect camera
- [ ] Connect Arduino
- [ ] Upload Arduino code
- [ ] Run `python3 main.py`
- [ ] Click START SYSTEM
- [ ] Place bottles
- [ ] Show results
- [ ] Show history
- [ ] Explain classification logic

---

## 🚀 Ready to Go!

**Everything configured?**

```bash
cd Project_Graduation_3
python3 main.py
```

**Click START SYSTEM and you're running!**

---

**Questions? Check README.md and GRADUATION_DEFENSE_GUIDE.md**

---

