# ⚡ Quick Start Guide

## 🚀 5 Minutes Setup

### Step 1: Upload Arduino Firmware
```bash
# Mở Arduino IDE
# File → Open → arduino/product_sorter.ino
# Upload to Arduino Uno
```

### Step 2: Install Python Dependencies
```bash
cd product_classifier_tk
pip3 install -r requirements.txt
```

### Step 3: Test Components (Optional but Recommended)
```bash
python3 test_system_components.py
```

### Step 4: Configure System
Edit `main_continuous_flow_tkinter.py`, tìm class `Config`:
```python
SERIAL_PORT = "/dev/ttyACM0"  # Adjust if needed
CAMERA_INDEX = 0              # Adjust if needed
PHYSICAL_DELAY = 2.0          # MUST CALIBRATE!
```

### Step 5: Run System
```bash
# Recommended: Use Tkinter version
python3 main_continuous_flow_tkinter.py

# Or use script
bash run_tkinter.sh
```

**Controls:** Use buttons on GUI interface

---

## ⚙️ Calibration PHYSICAL_DELAY

**IMPORTANT:** Must calibrate before production use!

1. Measure distance: Camera → Ejector (cm)
2. Measure conveyor speed (cm/s)
3. Calculate: `PHYSICAL_DELAY = distance / speed`
4. Test and fine-tune (±0.1s increments)

Example:
- Distance: 60 cm
- Speed: 30 cm/s
- → `PHYSICAL_DELAY = 2.0` seconds

---

## 🔧 Hardware Connections

### Arduino Pins:
- **D2**: IR Sensor (Active LOW)
- **D7**: Relay (LOW Trigger) → 12V Conveyor
- **D9**: Servo Motor

### Power:
- Arduino: USB from Pi
- Servo: External 5V supply (1A+)
- Conveyor: 12V supply

---

## 📊 Expected Dashboard

```
┌─────────────────────────────────┐
│ Live Feed  │  Latest Defect     │
│ (Camera)   │  (Annotated)       │
├─────────────────────────────────┤
│ Total: 125  Good: 118  Bad: 7   │
│ no_cap: 2  low_level: 3  ...    │
└─────────────────────────────────┘
```

---

## ❓ Troubleshooting

| Issue | Solution |
|-------|----------|
| Camera not found | `ls /dev/video*`, edit `CAMERA_INDEX` |
| Arduino not connected | `ls /dev/ttyACM*`, check USB cable |
| Model not found | Place `my_model.pt` in `model/` folder |
| Wrong eject timing | Calibrate `PHYSICAL_DELAY` |

---

## 📚 Full Documentation

See `CONTINUOUS_FLOW_README.md` for detailed information.

---

**Ready to inspect bottles! 🍾**

