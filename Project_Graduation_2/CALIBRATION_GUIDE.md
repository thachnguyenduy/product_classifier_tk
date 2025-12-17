# 🎯 Calibration Guide - Continuous Sorting System

## Critical: Travel Time Calibration

The **TRAVEL_TIME** is the most important parameter in the continuous mode system. It determines when the servo kicks to reject a bottle.

### Why It's Critical

```
IR Sensor ────────────────────────> Servo
          <─── TRAVEL_TIME ────>

If TRAVEL_TIME is:
- Too SHORT → Kick happens BEFORE bottle arrives (miss)
- Too LONG → Kick happens AFTER bottle passes (wrong bottle)
- CORRECT → Kick happens exactly when bottle is at servo ✓
```

---

## Step-by-Step Calibration

### Method 1: Physical Measurement (Most Accurate)

1. **Setup**:
   - Place a bottle at the IR sensor position
   - Mark the bottle with tape/marker
   - Have a stopwatch ready

2. **Measure**:
   ```
   a) Start conveyor
   b) Start stopwatch when bottle passes IR sensor
   c) Stop when bottle reaches servo position
   d) Record time in milliseconds
   ```

3. **Calculate**:
   ```
   Example: 4.5 seconds = 4500 milliseconds
   ```

4. **Update Code**:
   
   **Arduino** (`arduino/sorting_control.ino`):
   ```cpp
   // Line 28
   unsigned long TRAVEL_TIME = 4500;  // Your measured value
   ```
   
   **Python** (`config.py`):
   ```python
   # Line 47
   TRAVEL_TIME_MS = 4500  # Must match Arduino!
   ```

5. **Upload and Test**:
   - Upload Arduino code
   - Restart Python program
   - Test with a single bottle

### Method 2: Calculation (If you know conveyor speed)

```
TRAVEL_TIME = Distance / Speed

Example:
- Distance from sensor to servo: 0.9 meters
- Conveyor speed: 0.2 m/s
- TRAVEL_TIME = 0.9 / 0.2 = 4.5 seconds = 4500ms
```

### Method 3: Trial and Error (Last Resort)

1. Start with estimated value (e.g., 4000ms)
2. Run system with one bottle
3. Observe kick timing:
   - Kicks early? Increase TRAVEL_TIME (+500ms)
   - Kicks late? Decrease TRAVEL_TIME (-500ms)
4. Repeat until accurate
5. Fine-tune in smaller increments (±100ms)

---

## Verification Tests

### Test 1: Single Bottle

```
1. Place ONE bottle on conveyor
2. Mark it as "NG" (e.g., remove cap)
3. Start system
4. Observe: Does servo kick exactly when bottle is at servo position?
```

**Expected**: Bottle is pushed off conveyor at correct position

### Test 2: Multiple Bottles

```
1. Place THREE bottles, spaced 2 seconds apart
2. Mark middle bottle as "NG"
3. Start system
4. Observe: Only middle bottle should be rejected
```

**Expected**: Only the NG bottle is kicked, others pass through

### Test 3: Rapid Sequence

```
1. Place FIVE bottles, spaced 1 second apart
2. Mark 1st, 3rd, 5th as "NG"
3. Start system
4. Observe: All three NG bottles rejected at correct positions
```

**Expected**: Circular buffer handles multiple rejections correctly

---

## Camera Exposure Calibration

### Why Manual Exposure?

Moving conveyor causes **motion blur** with auto exposure. Manual exposure fixes this.

### Finding Optimal Exposure

1. **Start with default**:
   ```python
   # config.py
   CAMERA_EXPOSURE = -4
   ```

2. **Test image quality**:
   - Run system
   - Capture a bottle image
   - Check for blur

3. **Adjust based on results**:

   | Issue | Solution | New Value |
   |-------|----------|-----------|
   | Image too bright | Decrease exposure | -6, -8, -10 |
   | Image too dark | Increase exposure | -2, 0 |
   | Motion blur | Decrease exposure | -6, -8 |
   | Sharp but dark | Add more lighting | Keep -4 |

4. **Balance**:
   ```
   Shorter exposure = Less blur BUT darker image
   Longer exposure = Brighter BUT more blur
   
   SOLUTION: Use shorter exposure + better lighting
   ```

### Recommended Lighting Setup

```
┌─────────────────────────────────┐
│     LED Light (White, 5000K)    │
│              ↓                  │
│         ┌─────────┐             │
│         │ Bottle  │             │
│         └─────────┘             │
│     ═══════════════════         │
│        Conveyor Belt            │
└─────────────────────────────────┘

Tips:
- Use diffused LED lighting (avoid harsh shadows)
- Position light at 45° angle
- Avoid direct sunlight (causes overexposure)
- Use white/neutral background
```

---

## AI Confidence Calibration

### Understanding Confidence Threshold

```python
CONFIDENCE_THRESHOLD = 0.5  # Default

Detection confidence: 0.0 (no confidence) to 1.0 (100% confident)

If threshold = 0.5:
- Detection with 0.6 confidence → ACCEPTED ✓
- Detection with 0.4 confidence → REJECTED ✗
```

### Tuning Strategy

1. **Start with default (0.5)**

2. **Observe false positives/negatives**:

   | Problem | Cause | Solution |
   |---------|-------|----------|
   | Too many false alarms | Threshold too low | Increase to 0.6-0.7 |
   | Missing real defects | Threshold too high | Decrease to 0.3-0.4 |
   | Inconsistent results | Poor lighting | Fix lighting first |

3. **Test with known samples**:
   ```
   Test Set:
   - 10 OK bottles (should all pass)
   - 10 NG bottles (should all be rejected)
   
   Adjust threshold until:
   - OK pass rate: >95%
   - NG rejection rate: >95%
   ```

---

## NMS Threshold Calibration

### What is NMS?

Non-Maximum Suppression removes overlapping bounding boxes.

```
Before NMS:          After NMS:
┌──────┐             ┌──────┐
│ cap  │             │ cap  │
│ 0.95 │             │ 0.95 │
└──────┘             └──────┘
┌──────┐
│ cap  │  ← Removed (overlaps with 0.95 box)
│ 0.87 │
└──────┘
```

### Tuning NMS_THRESHOLD

```python
NMS_THRESHOLD = 0.45  # Default

Range: 0.0 (strict) to 1.0 (loose)
```

| Value | Effect | Use Case |
|-------|--------|----------|
| 0.3 | Very strict (removes many overlaps) | Dense objects, many detections |
| 0.45 | Balanced (default) | General use |
| 0.6 | Loose (keeps more boxes) | Sparse objects, few detections |

**Symptoms of wrong NMS threshold**:
- Too low (0.2-0.3): Missing valid detections
- Too high (0.6-0.8): Multiple boxes on same object

---

## System Timing Verification

### Check Processing Speed

Enable debug mode:
```python
# config.py
DEBUG_MODE = True
```

Watch terminal output:
```
[AI] Prediction: OK | Reason: All OK | Time: 87.3ms
[UI] Decision sent to Arduino: OK
```

**Target times**:
- AI processing: <150ms (on Pi 5)
- Serial send: <10ms
- Total: <200ms

**If too slow**:
1. Check CPU usage: `htop`
2. Close unnecessary programs
3. Consider model optimization
4. Reduce camera resolution

---

## Circular Buffer Verification

### Check Arduino Serial Monitor

```
[Arduino] NG - Kick scheduled at 12345 (in 4500 ms) | Queue: 1
[Arduino] NG - Kick scheduled at 13456 (in 4500 ms) | Queue: 2
[Arduino] Kick executed | Queue remaining: 1
[Arduino] Kick executed | Queue remaining: 0
```

**Healthy operation**:
- Queue size stays below 10 (buffer size: 20)
- No "queue full" errors
- Kicks execute at correct times

**If queue fills up**:
1. Bottles too close together → Space them out
2. AI too slow → Optimize processing
3. Increase buffer size in Arduino

---

## Final Checklist

Before production use:

- [ ] TRAVEL_TIME measured and set correctly
- [ ] Single bottle test passed
- [ ] Multiple bottle test passed
- [ ] Camera exposure optimized (no blur)
- [ ] Lighting adequate and consistent
- [ ] AI confidence tuned (>95% accuracy)
- [ ] NMS threshold set (no overlapping boxes)
- [ ] Processing time <200ms
- [ ] Circular buffer never overflows
- [ ] Serial communication stable
- [ ] Database logging working
- [ ] UI responsive and accurate

---

## Maintenance Schedule

### Daily
- Check camera focus and cleanliness
- Verify lighting consistency
- Test with known OK/NG samples

### Weekly
- Calibrate travel time (conveyor may stretch)
- Clean IR sensor
- Check servo operation
- Review detection accuracy logs

### Monthly
- Deep clean all sensors
- Verify all electrical connections
- Update statistics analysis
- Retrain AI model if needed

---

## Troubleshooting Common Issues

### Issue: Kicks are consistently early

```
Cause: TRAVEL_TIME too short
Fix: Increase by 200-500ms
Test: Single bottle verification
```

### Issue: Kicks are consistently late

```
Cause: TRAVEL_TIME too long
Fix: Decrease by 200-500ms
Test: Single bottle verification
```

### Issue: Kicks are random/inconsistent

```
Possible causes:
1. Conveyor speed varies → Check motor/belt
2. Bottles not detected → Check IR sensor
3. Serial delay → Check baud rate (9600)
4. AI too slow → Check processing time
```

### Issue: Wrong bottles rejected

```
Possible causes:
1. TRAVEL_TIME wrong → Recalibrate
2. Multiple bottles too close → Space them out
3. Circular buffer bug → Check Arduino serial output
4. AI misclassification → Retune confidence
```

---

**Remember**: Calibration is an iterative process. Test thoroughly with various scenarios before production use!

