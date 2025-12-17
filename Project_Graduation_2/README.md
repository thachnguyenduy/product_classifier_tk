# 🥤 Coca-Cola Sorting System - CONTINUOUS MODE

Advanced bottle inspection system using Raspberry Pi 5 and Arduino Uno with **continuous conveyor operation** and circular buffer queue for precise rejection timing.

## 🌟 Key Features

### **CONTINUOUS MODE** (No Conveyor Stopping)
- ✅ Conveyor runs continuously (higher throughput)
- ✅ Circular buffer queue handles multiple bottles simultaneously
- ✅ Precise timing-based rejection (4.5 second travel time)
- ✅ "Control First" strategy: Hardware control prioritized over UI updates

### AI-Powered Inspection
- ✅ NCNN model for fast inference (~50-150ms on Pi 5)
- ✅ Proper NMS (Non-Maximum Suppression) using `cv2.dnn.NMSBoxes`
- ✅ Detects 8 classes: 4 defects + 4 components
- ✅ Strict sorting logic: Defects OR missing components = NG

### Hardware Integration
- ✅ Fast serial communication (immediate decision transmission)
- ✅ Threaded camera with manual exposure (reduces motion blur)
- ✅ Non-blocking Arduino code with circular buffer
- ✅ Supports up to 20 bottles in processing zone

### User Interface
- ✅ Live video stream (30 FPS)
- ✅ Real-time inspection results with bounding boxes
- ✅ Statistics dashboard
- ✅ Inspection history viewer
- ✅ Professional Tkinter GUI

---

## 📋 System Requirements

### Hardware
- **Raspberry Pi 5** (8GB recommended) or Pi 4
- **Arduino Uno** (or compatible)
- **USB Camera** (or Pi Camera)
- **IR Sensor** (bottle detection)
- **Relay Module** (LOW trigger for conveyor control)
- **Servo Motor** (SG90 for rejection mechanism)
- **Conveyor Belt** (continuous operation)

### Software
- **Raspberry Pi OS** (Bullseye or newer)
- **Python 3.8+**
- **Arduino IDE** (for uploading Arduino code)

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
pip3 install -r requirements.txt

# Install NCNN (if not already installed)
pip3 install ncnn
```

### 2. Upload Arduino Code

1. Open `arduino/sorting_control.ino` in Arduino IDE
2. **IMPORTANT**: Adjust `TRAVEL_TIME` variable (line 28) to match your physical setup
   - Measure time from IR sensor to servo position
   - Default: 4500ms (4.5 seconds)
3. Upload to Arduino Uno

### 3. Configure System

Edit `config.py`:

```python
# CRITICAL: Must match Arduino's TRAVEL_TIME
TRAVEL_TIME_MS = 4500

# Camera settings
CAMERA_ID = 0
CAMERA_EXPOSURE = -4  # Adjust for your lighting

# Arduino port
ARDUINO_PORT = '/dev/ttyUSB0'  # or '/dev/ttyACM0'

# Model path
MODEL_PATH = "model/best_ncnn_model"
```

### 4. Run System

```bash
python3 main.py
```

---

## 🔧 Calibration Guide

### Step 1: Measure Travel Time

This is **CRITICAL** for accurate rejection!

1. Place a bottle at IR sensor position
2. Start a stopwatch
3. Manually move conveyor
4. Stop when bottle reaches servo position
5. Record time in milliseconds

**Example**: If it takes 4.5 seconds, set:
- Arduino: `TRAVEL_TIME = 4500;`
- Python: `TRAVEL_TIME_MS = 4500`

### Step 2: Adjust Camera Exposure

For moving conveyor, shorter exposure reduces motion blur:

```python
# config.py
CAMERA_EXPOSURE = -4  # Start here

# Too bright? Decrease: -6, -8
# Too dark? Increase: -2, 0
```

### Step 3: Tune AI Confidence

```python
# config.py
CONFIDENCE_THRESHOLD = 0.5  # Default

# Too many false positives? Increase: 0.6, 0.7
# Missing detections? Decrease: 0.4, 0.3
```

### Step 4: Test Circular Buffer

1. Start system
2. Place bottles at 1-second intervals
3. Verify correct bottles are rejected
4. Check Arduino serial monitor for queue status

---

## 📊 How It Works

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTINUOUS WORKFLOW                      │
└─────────────────────────────────────────────────────────────┘

1. CONVEYOR ALWAYS RUNNING
   └─> Relay = LOW (continuous)

2. IR SENSOR DETECTS BOTTLE
   └─> Arduino sends 'D' to Pi
   └─> Arduino records timestamp

3. PI CAPTURES & PROCESSES
   └─> Capture frame (no stopping!)
   └─> AI inference (~50-150ms)
   └─> Apply NMS (remove overlaps)

4. DECISION SENT IMMEDIATELY
   └─> 'O' (OK) or 'N' (NG) to Arduino
   └─> THEN update UI/database

5. ARDUINO SCHEDULES KICK (if NG)
   └─> kick_time = timestamp + TRAVEL_TIME
   └─> Add to circular buffer queue

6. ARDUINO LOOP CHECKS QUEUE
   └─> if (millis() >= kick_time)
   └─> Trigger servo (150ms kick)
   └─> Remove from queue

7. REPEAT (multiple bottles in parallel)
```

### Circular Buffer Explained

```
Buffer Size: 20 slots
Travel Time: 4500ms

Example with 3 bottles:

Time    Event                           Buffer
0ms     Bottle A detected              [A:4500]
1000ms  Bottle B detected              [A:4500, B:5500]
2000ms  Bottle C detected              [A:4500, B:5500, C:6500]
4500ms  Kick A (if NG)                 [B:5500, C:6500]
5500ms  Kick B (if NG)                 [C:6500]
6500ms  Kick C (if NG)                 []
```

---

## 🎯 AI Model Specifications

### Classes (8 total)

**Defects** (Red boxes):
- 0: `Cap-Defect`
- 1: `Filling-Defect`
- 2: `Label-Defect`
- 3: `Wrong-Product`

**Components** (Green boxes):
- 4: `cap`
- 5: `coca`
- 6: `filled`
- 7: `label`

### Sorting Logic

```python
NG (Reject) if:
  - ANY defect detected (classes 0-3)
  OR
  - Missing cap (class 4)
  OR
  - Missing filled (class 6)
  OR
  - Missing label (class 7)

OK (Pass) if:
  - NO defects
  AND
  - Has cap, filled, and label
```

### NMS (Non-Maximum Suppression)

Removes overlapping bounding boxes:

```python
# config.py
NMS_THRESHOLD = 0.45

# Lower (0.3-0.4): Remove more overlaps (strict)
# Higher (0.5-0.6): Keep more boxes (loose)
```

---

## 🖥️ User Interface

### Main Window

```
┌─────────────┬─────────────┬─────────────┐
│ LIVE VIDEO  │ LAST RESULT │ CONTROLS    │
│             │             │             │
│ [Camera]    │ [Annotated] │ ● RUNNING   │
│             │             │             │
│ FPS: 30     │ ✓ OK / ✗ NG │ [START]     │
│             │             │ [STOP]      │
│             │ Reason:     │             │
│             │ All OK      │ STATISTICS  │
│             │             │ Total: 42   │
│             │ Time: 87ms  │ OK: 38      │
│             │             │ NG: 4       │
│             │             │ Rate: 90.5% │
└─────────────┴─────────────┴─────────────┘
```

### Controls

- **START SYSTEM**: Begin automatic sorting
- **STOP SYSTEM**: Stop automatic sorting
- **VIEW HISTORY**: Open inspection log
- **EXIT**: Close application

---

## 📁 Project Structure

```
Project_Graduation/
├── arduino/
│   └── sorting_control.ino      # Circular buffer logic
├── captures/
│   ├── ok/                       # OK bottle images
│   └── ng/                       # NG bottle images
├── core/
│   ├── ai.py                     # NCNN + NMS
│   ├── camera.py                 # Threaded camera
│   ├── database.py               # SQLite logging
│   └── hardware.py               # Serial communication
├── database/
│   └── product.db                # SQLite database
├── model/
│   └── best_ncnn_model/
│       ├── model.ncnn.param
│       └── model.ncnn.bin
├── ui/
│   ├── main_window.py            # Main GUI
│   └── history_window.py         # History viewer
├── config.py                     # Configuration
├── main.py                       # Entry point
├── requirements.txt              # Dependencies
└── README.md                     # This file
```

---

## ⚙️ Configuration Reference

### `config.py` - Key Parameters

```python
# AI
CONFIDENCE_THRESHOLD = 0.5    # Detection confidence
NMS_THRESHOLD = 0.45          # Overlap removal

# Timing (CRITICAL!)
TRAVEL_TIME_MS = 4500         # Sensor to servo time

# Camera
CAMERA_EXPOSURE = -4          # Manual exposure
CAMERA_AUTO_EXPOSURE = False  # Disable auto

# Hardware
ARDUINO_PORT = '/dev/ttyUSB0'
ARDUINO_BAUDRATE = 9600

# Logic
REQUIRE_CAP = True
REQUIRE_FILLED = True
REQUIRE_LABEL = True

# Debug
DEBUG_MODE = True
SAVE_DEBUG_IMAGES = True
```

---

## 🐛 Troubleshooting

### Issue: Wrong bottles are rejected

**Cause**: Travel time mismatch

**Solution**:
1. Measure actual travel time physically
2. Update both Arduino and Python config
3. Test with single bottle first

### Issue: Motion blur in images

**Cause**: Exposure too long

**Solution**:
```python
# config.py
CAMERA_EXPOSURE = -6  # Shorter exposure
```

### Issue: Missing detections

**Cause**: Confidence threshold too high

**Solution**:
```python
# config.py
CONFIDENCE_THRESHOLD = 0.3  # Lower threshold
```

### Issue: Overlapping bounding boxes

**Cause**: NMS threshold too high

**Solution**:
```python
# config.py
NMS_THRESHOLD = 0.35  # More aggressive NMS
```

### Issue: Buffer overflow

**Cause**: Too many bottles too fast

**Solution**:
1. Increase buffer size in Arduino:
   ```cpp
   const int BUFFER_SIZE = 30;  // Increase from 20
   ```
2. Slow down conveyor
3. Space bottles further apart

---

## 📈 Performance

### Throughput
- **~30-40 bottles/minute** (with 1.5s spacing)
- **~50-60 bottles/minute** (with 1s spacing, if AI is fast)

### Latency
- **AI Processing**: 50-150ms (NCNN on Pi 5)
- **Serial Communication**: <10ms
- **Total Response**: <200ms

### Accuracy
- **Detection**: >95% (with proper lighting and calibration)
- **Rejection Timing**: ±50ms (with correct TRAVEL_TIME)

---

## 🔐 Safety Features

### Timeout Protection
- Arduino waits max 10 seconds for Pi response
- Default to OK if timeout (safe operation)

### Buffer Overflow Protection
- Warns if queue is full
- Logs error but continues operation

### Error Recovery
- Camera failure → Dummy camera mode
- Arduino disconnect → Dummy hardware mode
- Model load failure → Dummy predictions

---

## 📝 License

This project is for educational purposes.

---

## 👥 Support

For issues or questions:
1. Check `TROUBLESHOOTING.md`
2. Review Arduino serial monitor output
3. Enable `DEBUG_MODE` in `config.py`
4. Check `system.log` file

---

## 🎓 Educational Notes

### Why Continuous Mode?

**Advantages**:
- ✅ Higher throughput (no stopping delays)
- ✅ More realistic industrial application
- ✅ Better for high-speed production lines

**Challenges**:
- ⚠️ Requires precise timing calibration
- ⚠️ Motion blur (solved with manual exposure)
- ⚠️ Multiple bottles in processing zone (solved with circular buffer)

### Key Concepts Demonstrated

1. **Embedded Systems**: Arduino + Raspberry Pi communication
2. **Real-Time Control**: Timing-critical servo actuation
3. **Computer Vision**: NCNN inference, NMS algorithm
4. **Multithreading**: Camera, serial, UI threads
5. **Data Structures**: Circular buffer implementation
6. **System Design**: "Control First" strategy

---

**Built with ❤️ for industrial automation education**
