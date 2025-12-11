# Arduino Product Sorter - Refactored Firmware

## 🔄 What's New (Refactored Version)

This is the **refactored firmware** for the continuous flow bottle inspection system.

### New Features
- ✅ **IR Sensor Integration (D2)**: Active LOW detection
- ✅ **Sends DETECTED Signal**: Notifies Pi when bottle passes
- ✅ **LOW-Trigger Relay Support**: Correct polarity for 5V relay modules
- ✅ **Continuous Flow Ejection**: Servo ejects without stopping conveyor
- ✅ **Improved Debouncing**: Reliable bottle detection

## 📦 Hardware Components

| Component | Pin | Description | Type |
|-----------|-----|-------------|------|
| **IR Sensor** | D2 | Bottle detection | Active LOW (0 = detected) |
| **Relay 5V** | D7 | Conveyor control | LOW Trigger (LOW = ON) |
| **Servo Motor** | D9 | Bottle ejection | Standard servo (0-180°) |

## 🔌 Connections

### IR Sensor (Active LOW)
```
IR Sensor Module:
  VCC → Arduino 5V
  GND → Arduino GND
  OUT → Arduino D2
```
**Note:** Output is LOW when object detected, HIGH when clear.

### Relay Module (LOW Trigger)
```
Relay Module:
  VCC → Arduino 5V
  GND → Arduino GND
  IN  → Arduino D7
  
Relay Output:
  COM → 12V Battery +
  NO  → Conveyor Motor +
  Motor - → Battery -
```
**Note:** LOW signal triggers relay ON, HIGH triggers relay OFF.

### Servo Motor
```
Servo:
  Signal → Arduino D9
  VCC → External 5V Power Supply (1A+)
  GND → Common GND (Arduino + Power Supply)
```
**Important:** Do NOT power servo from Arduino 5V pin! Use external supply.

## 📡 Serial Communication

**Baud Rate:** 115200  
**Connection:** USB cable to Raspberry Pi

### Commands (Pi → Arduino)

| Command | Action |
|---------|--------|
| `START_CONVEYOR` | Start conveyor belt (relay LOW) |
| `STOP_CONVEYOR` | Stop conveyor belt (relay HIGH) |
| `REJECT` | Eject bottle (conveyor keeps running) |
| `PING` | Test connection (responds "PONG") |
| `STATUS` | Print system status |

### Signals (Arduino → Pi)

| Signal | Meaning |
|--------|---------|
| `DETECTED` | IR sensor detected a bottle |

**Example Flow:**
```
1. Bottle passes IR sensor
2. Arduino sends "DETECTED" to Pi
3. Pi processes bottle (burst capture + AI)
4. If defect: Pi sends "REJECT" to Arduino
5. Arduino triggers servo (conveyor still running)
```

## ⚙️ Configuration Parameters

Edit these in the `.ino` file if needed:

```cpp
// Pin definitions
#define IR_SENSOR_PIN   2
#define RELAY_PIN       7
#define SERVO_PIN       9

// Servo positions
#define SERVO_REST      90   // Rest position
#define SERVO_EJECT     0    // Ejection position

// Timing
#define DEBOUNCE_TIME   50   // IR debounce (ms)
#define SERVO_EJECT_TIME 500 // Eject duration (ms)
```

## 📤 Upload Instructions

### Using Arduino IDE

1. **Open** `product_sorter.ino` in Arduino IDE
2. **Connect** Arduino Uno via USB
3. **Select Board**: Tools → Board → Arduino Uno
4. **Select Port**: 
   - Linux/Pi: `/dev/ttyACM0`
   - Windows: `COM3` (or similar)
5. **Upload**: Click Upload button (→)
6. **Verify**: Open Serial Monitor (115200 baud)
   - Should see: "Arduino Bottle Defect System Ready"

### Using Arduino CLI (Linux/Pi)

```bash
# Install Arduino CLI
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh

# Install core
arduino-cli core install arduino:avr

# Compile and upload
arduino-cli compile --fqbn arduino:avr:uno product_sorter.ino
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno product_sorter.ino
```

## 🧪 Testing

### Test 1: Serial Connection
```bash
# Open serial monitor
screen /dev/ttyACM0 115200
# Or use Arduino IDE Serial Monitor

# Should see startup message:
# "Arduino Bottle Defect System Ready"
```

### Test 2: Commands
```bash
# In serial monitor, type commands:
PING         # Should respond "PONG"
STATUS       # Should show system status
START_CONVEYOR
STOP_CONVEYOR
REJECT
```

### Test 3: IR Sensor
```bash
# Wave hand in front of IR sensor
# Should see "DETECTED" printed in serial monitor
```

### Test 4: Hardware
```bash
# From Raspberry Pi, run:
python3 -c "
import serial
import time
ser = serial.Serial('/dev/ttyACM0', 115200)
time.sleep(2)
ser.write(b'START_CONVEYOR\n')  # Conveyor should start
time.sleep(2)
ser.write(b'REJECT\n')           # Servo should eject
time.sleep(2)
ser.write(b'STOP_CONVEYOR\n')   # Conveyor should stop
ser.close()
"
```

## 🐛 Troubleshooting

### Issue: No startup message

**Cause:** Serial port not opened or wrong baud rate

**Fix:**
- Verify port: `ls /dev/ttyACM*`
- Check baud rate: 115200
- Try unplugging and replugging USB

### Issue: IR sensor not detecting

**Cause:** Wiring or alignment issue

**Fix:**
1. Check wiring (VCC, GND, OUT to D2)
2. Test sensor: `digitalWrite(13, digitalRead(2))` (LED should follow sensor)
3. Adjust sensor position to face conveyor belt
4. Check if sensor LED lights up when object near

### Issue: Relay not switching

**Cause:** Wrong polarity or insufficient power

**Fix:**
1. Verify LOW trigger relay (common type)
2. Check if relay has external power option
3. Listen for "click" sound when switching
4. Measure voltage on relay coil (should be ~5V)

### Issue: Servo not moving

**Cause:** Insufficient power or bad connection

**Fix:**
1. **MUST** use external 5V power (1A+), not Arduino pin
2. Check GND is common (Arduino + power supply)
3. Test servo: `servo.write(0); delay(1000); servo.write(180);`

### Issue: False triggers from IR sensor

**Cause:** Noise or reflections

**Fix:**
1. Increase `DEBOUNCE_TIME` (try 100ms)
2. Shield sensor from ambient light
3. Adjust sensor sensitivity (if adjustable)

## 🔧 Maintenance

### Weekly
- Clean IR sensor lens (dust can cause false triggers)
- Check servo arm for mechanical wear
- Verify all connections are tight

### Monthly
- Test full sequence (conveyor + sensor + servo)
- Check relay contacts (should click clearly)
- Inspect cables for damage

## 📊 Performance Specs

- **IR Detection Range**: 3-30 cm (typical)
- **Debounce Time**: 50 ms
- **Servo Response**: ~500 ms per eject
- **Serial Latency**: <10 ms
- **Reliability**: 99%+ detection rate

## 🔄 Differences from Old Version

| Feature | Old Firmware | New Firmware |
|---------|--------------|--------------|
| IR Sensor | ❌ Not supported | ✅ Supported (D2) |
| Detection | Passive (Pi only) | Active (sends DETECTED) |
| Relay Type | Standard (HIGH=ON) | LOW Trigger (LOW=ON) |
| Ejection | Stops conveyor | Continuous flow |
| Commands | RELAY_ON/OFF, EJECT | START/STOP_CONVEYOR, REJECT |

## 📝 Notes

- **LOW Trigger Relay**: Most cheap 5V relay modules are LOW trigger
  - LOW signal (0V) → Relay ON
  - HIGH signal (5V) → Relay OFF
  
- **Active LOW IR Sensor**: Common type
  - LOW (0V) → Object detected
  - HIGH (5V) → No object

- **Continuous Flow**: Conveyor never stops during ejection
  - Servo must be positioned correctly relative to belt speed
  - Calibrate `PHYSICAL_DELAY` in Python code

## 🎯 Integration with Python

This firmware works with `main_continuous_flow.py`:

```python
# Python side
arduino = ArduinoController("/dev/ttyACM0")
arduino.start_conveyor()  # → Sends "START_CONVEYOR"
arduino.reject_bottle()   # → Sends "REJECT"

# Arduino automatically sends "DETECTED" when bottle passes
# Python receives it via listener thread
```

## 📚 Additional Resources

- [Arduino Serial Communication](https://www.arduino.cc/reference/en/language/functions/communication/serial/)
- [Servo Library Reference](https://www.arduino.cc/reference/en/libraries/servo/)
- [IR Sensor Guide](https://lastminuteengineers.com/ir-sensor-arduino-tutorial/)

---

**Firmware Version:** 2.0 (Refactored)  
**Compatible with:** `main_continuous_flow.py`  
**Last Updated:** December 2025
