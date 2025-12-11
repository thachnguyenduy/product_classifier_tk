# 🚀 Quick Start Guide

## For Testing (Without Hardware)

```bash
# 1. Install dependencies
pip3 install opencv-python numpy pillow pyserial

# 2. Enable dummy mode
# Edit config.py:
USE_DUMMY_CAMERA = True
USE_DUMMY_HARDWARE = True

# 3. Run
python3 main.py
```

## For Production (With Hardware)

```bash
# 1. Install all dependencies
pip3 install -r requirements.txt

# 2. Install NCNN
sudo apt-get install python3-ncnn

# 3. Upload Arduino code
# Open arduino/sorting_control.ino in Arduino IDE
# Upload to Arduino Uno

# 4. Configure ports in config.py
ARDUINO_PORT = '/dev/ttyUSB0'  # Check with: ls /dev/tty*

# 5. Place model files in model/
# - best.ncnn.param
# - best.ncnn.bin

# 6. Run
python3 main.py
```

## Calibration Steps

1. **Adjust Virtual Line**
   - Run system
   - Watch video feed
   - Adjust `VIRTUAL_LINE_X` in config.py
   - Restart

2. **Test Detection**
   - Place bottle in view
   - Move it across the cyan line
   - Check if it's added to queue

3. **Test IR Trigger**
   - Start system
   - Block IR sensor manually
   - Arduino should send 'T'
   - Oldest queue item should be processed

4. **Test Servo**
   - Queue an NG item
   - Trigger IR sensor
   - Servo should kick

## Troubleshooting

**Queue is empty when trigger fires:**
- Increase `DETECTION_COOLDOWN`
- Check if bottles are being detected (watch queue panel)

**Multiple detections for one bottle:**
- Increase `DETECTION_COOLDOWN` (try 1.5s or 2.0s)
- Decrease `CROSSING_TOLERANCE`

**Bottles detected but not in queue:**
- Check terminal output for AI errors
- Verify NCNN model is loaded

**Servo doesn't kick:**
- Check Arduino serial monitor
- Verify wiring (Pin 9)
- Check if 'K' command is sent (terminal logs)

