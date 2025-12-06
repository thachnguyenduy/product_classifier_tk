# 🚀 Setup Guide - Coca-Cola Sorting System

Complete step-by-step guide to set up the system from scratch.

## 📋 Prerequisites

### Hardware Checklist
- ✅ Raspberry Pi 5 (4GB+ RAM recommended)
- ✅ Arduino Uno with USB cable
- ✅ USB Camera or Pi Camera Module V2/V3
- ✅ IR Proximity Sensor (e.g., FC-51)
- ✅ 1-Channel Relay Module (LOW trigger)
- ✅ SG90 Servo Motor
- ✅ 12V DC Motor + Driver for conveyor
- ✅ Breadboard and jumper wires
- ✅ 5V and 12V power supplies

### Software Checklist
- ✅ Raspberry Pi OS (64-bit recommended)
- ✅ Python 3.7+
- ✅ Arduino IDE 2.0+

---

## 🔧 Part 1: Raspberry Pi Setup

### 1.1 Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Install Python Dependencies

```bash
sudo apt install python3-pip python3-opencv python3-pil python3-tk -y
```

### 1.3 Install Python Packages

```bash
pip3 install -r requirements.txt
```

### 1.4 Install NCNN (Optional but Recommended)

```bash
# Download pre-built NCNN for Raspberry Pi
# Or build from source: https://github.com/Tencent/ncnn

# If building from source:
sudo apt install cmake build-essential -y
git clone https://github.com/Tencent/ncnn.git
cd ncnn
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release -DNCNN_VULKAN=OFF ..
make -j4
sudo make install
```

### 1.5 Camera Permissions

```bash
# Add user to video group
sudo usermod -a -G video $USER

# Reboot
sudo reboot
```

---

## 🔌 Part 2: Hardware Wiring

### Arduino Uno Connections

| Component | Arduino Pin | Notes |
|-----------|-------------|-------|
| IR Sensor VCC | 5V | Power |
| IR Sensor GND | GND | Ground |
| IR Sensor OUT | Digital Pin 2 | Detection signal |
| Relay IN | Digital Pin 4 | Control signal |
| Relay VCC | 5V | Power |
| Relay GND | GND | Ground |
| Servo Orange | Digital Pin 9 | PWM signal |
| Servo Red | 5V | Power |
| Servo Brown | GND | Ground |

### Relay to Motor Driver

| Relay | Motor Driver |
|-------|--------------|
| COM | Power supply + |
| NO (Normally Open) | Motor driver VCC |

**Important**: Relay is **LOW trigger** (LOW = Run, HIGH = Stop)

### IR Sensor Placement

- Mount sensor 5-10cm above conveyor
- Adjust sensitivity knob for reliable detection
- Test: LED should turn ON when bottle passes

---

## 💻 Part 3: Arduino Setup

### 3.1 Install Arduino IDE

Download from: https://www.arduino.cc/en/software

Or on Linux:
```bash
sudo apt install arduino -y
```

### 3.2 Install Servo Library

Open Arduino IDE:
1. Go to **Sketch → Include Library → Manage Libraries**
2. Search for "Servo"
3. Install **Servo by Arduino**

### 3.3 Upload Code

1. Open `arduino/sorting_control.ino`
2. Select **Tools → Board → Arduino Uno**
3. Select **Tools → Port → /dev/ttyUSB0** (or /dev/ttyACM0)
4. Click **Upload** (→ button)

### 3.4 Verify Upload

Open **Serial Monitor** (Ctrl+Shift+M):
- Set baud rate to **9600**
- Should see: "Coca-Cola Sorting System Ready"

### 3.5 Grant Serial Permissions (Linux)

```bash
sudo usermod -a -G dialout $USER
# Logout and login for changes to take effect
```

---

## 🧪 Part 4: Testing Components

### 4.1 Test Camera

```bash
python3 << EOF
import cv2
cap = cv2.VideoCapture(0)
if cap.isOpened():
    print("✓ Camera OK")
    ret, frame = cap.read()
    if ret:
        print(f"✓ Resolution: {frame.shape[1]}x{frame.shape[0]}")
else:
    print("✗ Camera FAILED")
cap.release()
EOF
```

### 4.2 Test Arduino Connection

```bash
python3 << EOF
import serial
import time

try:
    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=2)
    time.sleep(2)
    print("✓ Arduino connected")
    
    # Read some lines
    for _ in range(5):
        line = ser.readline().decode('utf-8').strip()
        if line:
            print(f"  Arduino says: {line}")
    
    ser.close()
except Exception as e:
    print(f"✗ Arduino connection failed: {e}")
EOF
```

### 4.3 Test IR Sensor

With Arduino connected and code uploaded:
1. Open Serial Monitor
2. Pass an object in front of sensor
3. Should see: "Bottle detected! Conveyor stopped."

### 4.4 Test Servo

Manually trigger servo in Serial Monitor:
1. Stop conveyor (pass object)
2. Send `N` in Serial Monitor
3. Servo should move and return

---

## 🎯 Part 5: Model Verification

### 5.1 Check Model Files

```bash
ls -lh model/best_ncnn_model/
```

Should show:
- `model.ncnn.param`
- `model.ncnn.bin`

### 5.2 Verify Class Mapping

Check `model/best_ncnn_model/metadata.yaml`:

```yaml
names:
  0: Cap-Defect
  1: Filling-Defect
  2: Label-Defect
  3: Wrong-Product
  4: cap
  5: coca
  6: filled
  7: label
```

---

## ▶️ Part 6: First Run

### 6.1 Configuration

Edit `main.py` if needed:

```python
'camera_id': 0,                    # Change if using different camera
'arduino_port': '/dev/ttyUSB0',    # Change if Arduino on different port
'use_dummy_camera': False,         # Set True to test without camera
'use_dummy_hardware': False        # Set True to test without Arduino
```

### 6.2 Create Directories

```bash
mkdir -p captures/ok captures/ng database
```

### 6.3 Launch Application

```bash
python3 main.py
```

Or use the script:

```bash
chmod +x run.sh
./run.sh
```

### 6.4 Initial Test

1. Application should open GUI
2. Check status messages in terminal
3. Verify camera feed is visible
4. Click **"START SYSTEM"**
5. Place a test bottle
6. Observe inspection process

---

## 🐛 Part 7: Troubleshooting

### Issue: Camera not found

**Solutions:**
1. Check USB connection
2. Try different camera index: `'camera_id': 1`
3. Check permissions: `groups | grep video`
4. Use dummy mode for testing

### Issue: Arduino not connecting

**Solutions:**
1. Check USB cable (must be data cable, not charging-only)
2. Verify port: `ls /dev/ttyUSB* /dev/ttyACM*`
3. Check permissions: `groups | grep dialout`
4. Try different port in config
5. Upload Arduino code again

### Issue: NCNN not working

**Solution:**
System will work in demo mode. For real inference:
1. Build NCNN from source
2. Install ncnn-python package
3. Restart application

### Issue: Relay not working

**Solutions:**
1. Verify LOW trigger setting
2. Check wiring: relay IN to Arduino pin 4
3. Measure voltage: should be ~5V when HIGH, 0V when LOW
4. Test with LED instead of motor first

### Issue: Servo not moving

**Solutions:**
1. Check power supply (SG90 needs 5V, ~500mA)
2. Verify pin 9 connection
3. Test servo separately with Arduino example code
4. Check if servo arm is physically stuck

### Issue: False detections

**Solutions:**
1. Adjust IR sensor sensitivity (potentiometer)
2. Change detection threshold in code
3. Shield sensor from ambient light
4. Increase stabilization delay

---

## ✅ Part 8: Calibration

### 8.1 Sensor Position

1. Place bottle on conveyor
2. Run conveyor slowly
3. Adjust sensor height and angle
4. Test multiple times for consistency

### 8.2 Conveyor Speed

1. Measure bottle detection position
2. Measure servo position
3. Adjust `MOVE_TO_SERVO_DELAY` in Arduino code:
   ```cpp
   const int MOVE_TO_SERVO_DELAY = 1500;  // Milliseconds
   ```

### 8.3 Servo Timing

Adjust in Arduino code:
```cpp
const int SERVO_KICK = 90;         // Angle (0-180)
const int SERVO_KICK_DELAY = 800;  // How long to hold position (ms)
```

### 8.4 AI Confidence Threshold

Edit `core/ai.py`:
```python
self.confidence_threshold = 0.5  # Lower = more sensitive (more NG)
```

---

## 🎓 Part 9: Usage Tips

### Best Practices

1. **Lighting**: Ensure consistent, bright lighting
2. **Background**: Use plain background for camera
3. **Speed**: Don't run conveyor too fast (< 0.5 m/s)
4. **Spacing**: Allow 10cm minimum between bottles
5. **Focus**: Adjust camera focus for sharp images

### Maintenance

- Clean camera lens regularly
- Check sensor for dust/debris
- Verify servo movement is smooth
- Back up database periodically: `cp database/product.db backup/`

### Monitoring

- Check terminal for error messages
- Monitor "Session Statistics" in UI
- Review "Inspection History" regularly
- Export statistics for analysis

---

## 📊 Part 10: Advanced Configuration

### Auto-start on Boot

Create systemd service:

```bash
sudo nano /etc/systemd/system/sorting-system.service
```

Add:
```ini
[Unit]
Description=Coca-Cola Sorting System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Project_Graduation
ExecStart=/usr/bin/python3 /home/pi/Project_Graduation/main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable sorting-system.service
sudo systemctl start sorting-system.service
```

### Network Access

For remote monitoring, set up VNC or SSH X11 forwarding.

---

## 🎉 Setup Complete!

Your Coca-Cola Sorting System is now ready for production use.

**Next Steps:**
1. Run sample tests with known good/bad bottles
2. Tune confidence thresholds if needed
3. Train team on operation
4. Start production runs
5. Monitor and maintain regularly

**Support:**
- Check README.md for additional info
- Review code comments for customization
- Check GitHub issues for common problems

Good luck! 🥤🤖

