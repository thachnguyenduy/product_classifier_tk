# 🧪 System Testing Guide

## Pre-flight Checklist

Before running the system, verify:

- [ ] NCNN model files in `model/` (best.ncnn.param & best.ncnn.bin)
- [ ] Arduino uploaded with `arduino/sorting_control.ino`
- [ ] Arduino connected (check `ls /dev/ttyUSB*`)
- [ ] Camera connected (check `ls /dev/video*`)
- [ ] Python dependencies installed (`pip3 install -r requirements.txt`)

## Test Scenarios

### Test 1: UI Only (No Hardware)

**Objective:** Verify UI loads and responds

```bash
# Edit config.py
USE_DUMMY_CAMERA = True
USE_DUMMY_HARDWARE = True

# Run
python3 main.py

# Expected:
# - Window opens
# - Dummy camera shows "DUMMY CAMERA" text
# - Buttons are responsive
# - Queue updates every 5 seconds (dummy trigger)
```

### Test 2: Camera Only

**Objective:** Verify camera capture and virtual line

```bash
# Edit config.py
USE_DUMMY_CAMERA = False
USE_DUMMY_HARDWARE = True

# Run
python3 main.py

# Expected:
# - Real camera feed displayed
# - Cyan virtual line visible
# - Moving object across line triggers detection
```

### Test 3: Arduino Communication

**Objective:** Verify serial communication

```bash
# Edit config.py
USE_DUMMY_CAMERA = True
USE_DUMMY_HARDWARE = False

# Run
python3 main.py

# Test:
# 1. Block IR sensor manually
# 2. Check terminal: Should see "Received: 'T'"
# 3. Queue should pop and send 'K' or 'O'
```

### Test 4: Full System Integration

**Objective:** End-to-end test

```bash
# Edit config.py
USE_DUMMY_CAMERA = False
USE_DUMMY_HARDWARE = False

# Run
python3 main.py

# Test flow:
# 1. Start system
# 2. Place bottle in view
# 3. Move it across cyan line
# 4. Verify detection added to queue
# 5. Let bottle reach IR sensor
# 6. Verify servo kicks (if NG) or does nothing (if OK)
```

## Expected Behavior

### Good Flow (OK Bottle)

```
1. Bottle crosses virtual line
   → [UI] "Bottle detected at (320, 240)"
   → [AI] Detects: cap, filled, label
   → [AI] Result: O | Reason: Sản phẩm đạt chuẩn
   → Queue: +1 item

2. Bottle reaches IR sensor
   → [Arduino] Sends 'T'
   → [Hardware] Received: 'T'
   → [UI] Pop queue (FIFO)
   → [UI] Result: O
   → [Hardware] Sent: 'O'
   → Servo: No action
```

### Defect Flow (NG Bottle)

```
1. Bottle crosses virtual line
   → [UI] "Bottle detected at (320, 240)"
   → [AI] Detects: cap, filled, label, Cap-Defect
   → [AI] Result: N | Reason: Phát hiện lỗi: Cap-Defect
   → Queue: +1 item

2. Bottle reaches IR sensor
   → [Arduino] Sends 'T'
   → [Hardware] Received: 'T'
   → [UI] Pop queue (FIFO)
   → [UI] Result: N
   → [Hardware] Sent: 'K'
   → Servo: KICK! (0° → 100° → 0°)
```

## Common Issues & Solutions

### Issue: "Queue is empty when trigger fires"

**Symptoms:**
- IR sensor triggers
- Terminal shows "Queue is empty!"
- No bottle was detected by camera

**Solutions:**
1. Check if bottles are being detected:
   - Watch the queue panel
   - Should show items being added
2. Increase cooldown:
   ```python
   DETECTION_COOLDOWN = 2.0  # Try 2 seconds
   ```
3. Verify virtual line position:
   - Line should be early in bottle path
   - Adjust `VIRTUAL_LINE_X`

### Issue: "Multiple detections for one bottle"

**Symptoms:**
- One bottle crosses line
- Multiple items added to queue

**Solutions:**
1. Increase cooldown:
   ```python
   DETECTION_COOLDOWN = 1.5  # Increase to 1.5s
   ```
2. Decrease tolerance:
   ```python
   CROSSING_TOLERANCE = 10  # Reduce to 10 pixels
   ```

### Issue: "NCNN output shape error"

**Symptoms:**
- Detection fails
- Terminal shows shape errors

**Solutions:**
1. Check model format:
   ```bash
   # Verify files exist
   ls -lh model/*.ncnn.*
   ```
2. Enable debug:
   ```python
   DEBUG_MODE = True
   ```
3. Check terminal output for actual shape

### Issue: "Servo doesn't kick"

**Symptoms:**
- NG item popped from queue
- Terminal shows "Sent: 'K'"
- Servo doesn't move

**Solutions:**
1. Check Arduino serial monitor:
   - Open Arduino IDE → Tools → Serial Monitor
   - Should see "Command received: KICK"
2. Check wiring:
   - Servo signal: Pin 9
   - Servo VCC: 5V (external power recommended)
3. Test servo manually:
   ```cpp
   // In Arduino IDE, upload this test:
   #include <Servo.h>
   Servo s;
   void setup() {
     s.attach(9);
     s.write(100);  // Should move
     delay(1000);
     s.write(0);
   }
   void loop() {}
   ```

## Performance Benchmarks

### Expected Processing Times

- Camera capture: ~30 FPS (33ms/frame)
- AI inference: 50-200ms (depends on hardware)
- NMS: 5-10ms
- Total detection: 100-250ms

### Expected Accuracy

- Detection rate: >95%
- False positives: <5%
- False negatives: <5%

## Debug Mode

Enable verbose logging:

```python
# config.py
DEBUG_MODE = True
VERBOSE_LOGGING = True
```

Terminal output will show:
```
[AI] NCNN output shape: (8400, 12)
[AI] Transposed to: (8400, 12)
[AI] Raw detections: 47, After NMS: 5
[AI] Components: cap=True, filled=True, label=True
[AI] Defects: []
[AI] Result: O | Reason: Sản phẩm đạt chuẩn | Time: 125.3ms
```

## Calibration Procedure

### Step 1: Find Optimal Virtual Line Position

```python
# Try different positions
VIRTUAL_LINE_X = 200  # Earlier detection
VIRTUAL_LINE_X = 320  # Center (default)
VIRTUAL_LINE_X = 400  # Later detection
```

Test each and choose based on:
- Detection reliability
- Processing time availability
- Physical layout

### Step 2: Tune Detection Cooldown

```python
# Start with default
DETECTION_COOLDOWN = 1.0

# If double detections occur:
DETECTION_COOLDOWN = 1.5  # or 2.0

# If bottles missed:
DETECTION_COOLDOWN = 0.5
```

### Step 3: Adjust AI Thresholds

```python
# More sensitive (more detections, more false positives)
CONFIDENCE_THRESHOLD = 0.3
NMS_THRESHOLD = 0.3

# Less sensitive (fewer detections, fewer false positives)
CONFIDENCE_THRESHOLD = 0.7
NMS_THRESHOLD = 0.6
```

### Step 4: Verify Timing

1. Start system
2. Place bottle at virtual line
3. Note time (T1)
4. Move bottle to IR sensor
5. Note time when sensor triggers (T2)
6. Calculate travel time: T2 - T1

This helps verify queue timing is correct.

---

**After all tests pass, your system is ready for production! 🚀**

