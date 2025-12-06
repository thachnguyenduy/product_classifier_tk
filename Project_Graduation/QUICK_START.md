# ⚡ Quick Start Guide

Get the Coca-Cola Sorting System running in 5 minutes!

## 🎯 Prerequisites

- Raspberry Pi 5 with OS installed
- Arduino Uno with code uploaded
- Camera connected
- Hardware assembled and wired

## 🚀 Installation (One-Time)

### Step 1: Navigate to Project

```bash
cd /path/to/Project_Graduation
```

### Step 2: Install Dependencies

```bash
pip3 install -r requirements.txt
```

### Step 3: Grant Permissions (Linux Only)

```bash
sudo usermod -a -G dialout,video $USER
# Then logout and login
```

## ▶️ Running the System

### Option 1: Direct Run

```bash
python3 main.py
```

### Option 2: Use Script

```bash
chmod +x run.sh
./run.sh
```

## 🎮 Operation

1. **Application Opens**: See main window with camera feed
2. **Click "START SYSTEM"**: Begin monitoring
3. **Place Bottles**: Put on conveyor belt
4. **Automatic Sorting**: System handles detection, inspection, sorting
5. **View Results**: Check snapshot and result on right panel
6. **Stop When Done**: Click "STOP SYSTEM"

## 🧪 Test Mode (No Hardware)

Edit `main.py`:

```python
config = {
    'use_dummy_camera': True,     # Simulate camera
    'use_dummy_hardware': True    # Simulate Arduino
}
```

Then run:
```bash
python3 main.py
```

- Dummy mode simulates detections every 5 seconds
- Random OK/NG results for testing UI

## 📝 Configuration

Common settings in `main.py`:

```python
config = {
    'camera_id': 0,                # USB camera (or video file path)
    'arduino_port': '/dev/ttyUSB0', # Serial port (COM3 on Windows)
    'model_path': 'model/best_ncnn_model'  # AI model location
}
```

## 🐛 Common Issues

### Camera Not Opening?
```bash
# Test camera
python3 -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

### Arduino Not Connecting?
```bash
# Check available ports
ls /dev/ttyUSB* /dev/ttyACM*  # Linux
# or
# Check Device Manager on Windows
```

### Permission Denied?
```bash
sudo chmod 666 /dev/ttyUSB0  # Temporary fix
# or
sudo usermod -a -G dialout $USER  # Permanent fix (need logout)
```

## 📊 Features

- **Live Video**: 30 FPS camera feed
- **Real-time AI**: NCNN inference on Pi
- **History**: View all past inspections
- **Statistics**: OK/NG rates, defect analysis
- **Auto-save**: Images saved to `captures/ok/` and `captures/ng/`

## 🔍 Monitoring

### Terminal Output
- Watch for `[Arduino]` messages (detection events)
- Check `[AI]` predictions
- Monitor `[Hardware]` communication

### UI Indicators
- **Status**: Red (STOPPED) / Green (RUNNING)
- **FPS**: Camera performance
- **Statistics**: Session totals

## 📁 Output Files

- **Database**: `database/product.db` (SQLite)
- **OK Images**: `captures/ok/OK_*.jpg`
- **NG Images**: `captures/ng/NG_*.jpg`

## ⚙️ Calibration

### Adjust Servo Timing

Edit `arduino/sorting_control.ino`:

```cpp
const int MOVE_TO_SERVO_DELAY = 1500;  // Time to reach servo (ms)
const int SERVO_KICK = 90;             // Kick angle (degrees)
```

### Adjust AI Sensitivity

Edit `core/ai.py`:

```python
self.confidence_threshold = 0.5  # Detection threshold (0.0 - 1.0)
```

## 🎯 Workflow

```
Bottle → IR Sensor → Arduino Stops Conveyor
                   ↓
            Send 'D' to Pi
                   ↓
         Pi Captures Image
                   ↓
         AI Runs Inference
                   ↓
    Check: Defects? Components?
                   ↓
        ┌──────────┴──────────┐
        ↓                      ↓
       OK                     NG
        ↓                      ↓
   Send 'O'              Send 'N'
        ↓                      ↓
  Pass Bottle          Kick Off Servo
        ↓                      ↓
   Continue Conveyor    Continue Conveyor
```

## 📖 More Help

- **Full Setup**: See `SETUP_GUIDE.md`
- **README**: See `README.md`
- **Code Comments**: Check individual `.py` files
- **Arduino Debug**: Open Serial Monitor (9600 baud)

## ✅ Quick Health Check

Run this after installation:

```bash
# Test 1: Python packages
python3 -c "import cv2, serial, PIL; print('✓ Packages OK')"

# Test 2: Camera
python3 -c "import cv2; print('✓ Camera OK' if cv2.VideoCapture(0).isOpened() else '✗ Camera FAIL')"

# Test 3: Model files
ls model/best_ncnn_model/*.ncnn.* && echo "✓ Model OK" || echo "✗ Model MISSING"

# Test 4: Arduino (if connected)
python3 -c "import serial; s=serial.Serial('/dev/ttyUSB0',9600); print('✓ Arduino OK'); s.close()"
```

---

**Ready to sort!** 🥤✨

For detailed setup instructions, see `SETUP_GUIDE.md`.

