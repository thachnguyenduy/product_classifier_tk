# ⚡ Quick Start Guide - Continuous Sorting System

Get your system running in 5 minutes!

## 📦 Prerequisites

- Raspberry Pi 5 (or Pi 4) with Raspberry Pi OS
- Arduino Uno with uploaded code
- USB Camera connected
- Hardware assembled (IR sensor, relay, servo)

---

## 🚀 Installation (3 Steps)

### Step 1: Install Dependencies

```bash
# Update system
sudo apt update

# Install Python packages
pip3 install opencv-python numpy Pillow pyserial ncnn

# Or use requirements file
pip3 install -r requirements.txt
```

### Step 2: Configure System

Edit `config.py`:

```python
# CRITICAL: Set your travel time (measure physically!)
TRAVEL_TIME_MS = 4500  # Adjust to your setup

# Set Arduino port
ARDUINO_PORT = '/dev/ttyUSB0'  # or '/dev/ttyACM0'

# Set camera
CAMERA_ID = 0
CAMERA_EXPOSURE = -4  # Adjust for lighting
```

### Step 3: Upload Arduino Code

1. Open `arduino/sorting_control.ino`
2. Set `TRAVEL_TIME = 4500;` (line 28) to match your config
3. Upload to Arduino

---

## ▶️ Run System

```bash
python3 main.py
```

Or use the startup script:

```bash
./run.sh
```

---

## 🎮 Using the System

### Main Window

```
1. Click "START SYSTEM"
2. Place bottles on conveyor
3. System automatically detects and sorts
4. View results in real-time
5. Click "STOP SYSTEM" when done
```

### What You'll See

- **Left Panel**: Live camera feed (30 FPS)
- **Middle Panel**: Last inspection result with bounding boxes
- **Right Panel**: Controls and statistics

---

## ⚙️ First-Time Calibration

### 1. Measure Travel Time (CRITICAL!)

```
a) Place bottle at IR sensor
b) Start stopwatch
c) Move conveyor
d) Stop when bottle reaches servo
e) Record time in milliseconds

Example: 4.5 seconds = 4500ms
```

Update in **TWO places**:
- Arduino: `TRAVEL_TIME = 4500;`
- Python: `TRAVEL_TIME_MS = 4500`

### 2. Test with Single Bottle

```
1. Mark a bottle as "NG" (remove cap)
2. Place on conveyor
3. Start system
4. Verify servo kicks at correct position
```

If kick is:
- **Early**: Increase TRAVEL_TIME (+500ms)
- **Late**: Decrease TRAVEL_TIME (-500ms)

### 3. Adjust Camera Exposure

If images are blurry:

```python
# config.py
CAMERA_EXPOSURE = -6  # Shorter exposure = less blur
```

If images are too dark:
- Increase lighting
- Or increase exposure (but may cause blur)

---

## 🐛 Quick Troubleshooting

### Camera not found

```bash
# List available cameras
ls /dev/video*

# Try different camera ID
# In config.py:
CAMERA_ID = 0  # or 1, 2, etc.
```

### Arduino not connecting

```bash
# List serial ports
ls /dev/tty*

# Common ports:
# /dev/ttyUSB0
# /dev/ttyACM0

# Check permissions
sudo usermod -a -G dialout $USER
# Then logout and login
```

### Model not loading

```bash
# Check model files exist
ls model/best_ncnn_model/

# Should see:
# model.ncnn.param
# model.ncnn.bin
```

### Wrong bottles rejected

**Most common cause**: TRAVEL_TIME mismatch

1. Remeasure travel time physically
2. Update Arduino and Python config
3. Test with single bottle

---

## 📊 Testing Checklist

Before production use:

- [ ] Single bottle test (OK bottle passes)
- [ ] Single bottle test (NG bottle rejected)
- [ ] Multiple bottles test (correct ones rejected)
- [ ] No motion blur in captured images
- [ ] AI detects all components correctly
- [ ] Statistics updating correctly
- [ ] Database logging working

---

## 🎯 Performance Targets

- **AI Processing**: <150ms per bottle
- **Throughput**: 30-40 bottles/minute
- **Accuracy**: >95% detection rate
- **Rejection Timing**: ±50ms precision

---

## 📖 Next Steps

1. ✅ **Read**: `README.md` for detailed documentation
2. ✅ **Calibrate**: `CALIBRATION_GUIDE.md` for fine-tuning
3. ✅ **Optimize**: Adjust confidence and NMS thresholds
4. ✅ **Monitor**: Check Arduino serial output for debugging

---

## 💡 Pro Tips

### Tip 1: Use Debug Mode

```python
# config.py
DEBUG_MODE = True
SAVE_DEBUG_IMAGES = True
```

This will:
- Print detailed logs to terminal
- Save annotated images to `captures/debug/`

### Tip 2: Monitor Arduino

Open Arduino Serial Monitor (9600 baud) to see:
- Detection events
- Queue status
- Kick timing
- Statistics

### Tip 3: Test Dummy Mode First

```python
# config.py
USE_DUMMY_CAMERA = True
USE_DUMMY_HARDWARE = True
```

This lets you test the UI without hardware.

### Tip 4: Optimize Lighting

```
Good lighting = Better AI accuracy

Tips:
- Use diffused white LED lights
- Avoid shadows
- Consistent brightness
- White/neutral background
```

---

## 🆘 Need Help?

1. **Check logs**: Terminal output shows detailed info
2. **Arduino monitor**: Serial output shows hardware status
3. **Debug images**: Check `captures/debug/` folder
4. **Documentation**: Read `CALIBRATION_GUIDE.md`

---

**You're ready to go! Start with a single bottle test and gradually increase complexity.** 🚀
