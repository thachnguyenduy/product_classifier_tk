# 🎯 Calibration Guide - Detailed Instructions

## 📐 Why Calibration Matters

The **most critical parameter** in the continuous flow system is `PHYSICAL_DELAY` - the time from capture to ejection. If this is wrong:

- ❌ **Too short**: Servo ejects before bottle arrives → Misses target
- ❌ **Too long**: Servo ejects after bottle passes → Misses target
- ✅ **Just right**: Servo ejects exactly when bottle is in position

**Goal:** Achieve ±50ms precision for 95%+ ejection success rate.

---

## 🛠️ Step-by-Step Calibration Process

### Prerequisites

✅ Hardware fully assembled  
✅ Conveyor belt running smoothly  
✅ Arduino firmware uploaded  
✅ Python dependencies installed  
✅ Camera positioned and focused  

---

## 🎬 Phase 1: Physical Measurements

### 1.1 Measure Distance

**What to measure:** Distance from camera center to servo ejection point.

**How to measure:**
1. Place a ruler or measuring tape along the conveyor belt
2. Mark the camera's center point (where lens points at belt)
3. Mark the servo's ejection point (where servo arm intersects belt)
4. Measure the distance between these two points

**Example:**
```
Camera position: 10 cm from start
Ejector position: 70 cm from start
→ Distance = 70 - 10 = 60 cm
```

**Record:** `DISTANCE = _____ cm`

### 1.2 Measure Conveyor Speed

**Method A: Manual timing**
1. Mark a bottle with tape
2. Start stopwatch when bottle passes a reference point
3. Stop when bottle passes another point (known distance apart)
4. Calculate: `Speed = Distance / Time`

**Example:**
```
Distance: 100 cm
Time: 3.5 seconds
→ Speed = 100 / 3.5 = 28.57 cm/s
```

**Method B: Use encoder/tachometer** (if available)
- Read speed directly from motor controller

**Record:** `SPEED = _____ cm/s`

### 1.3 Calculate Initial PHYSICAL_DELAY

```
PHYSICAL_DELAY = DISTANCE / SPEED
```

**Example:**
```
DISTANCE = 60 cm
SPEED = 28.57 cm/s
→ PHYSICAL_DELAY = 60 / 28.57 = 2.1 seconds
```

**Record:** `PHYSICAL_DELAY (initial) = _____ seconds`

---

## ⚙️ Phase 2: Software Configuration

### 2.1 Edit Config File

Open `main_continuous_flow.py` and find the `Config` class:

```python
class Config:
    # ... other settings ...
    
    # =============== Physical Timing (CALIBRATE!) =================
    PHYSICAL_DELAY = 2.1  # ← CHANGE THIS VALUE
```

**Enter your calculated value here.**

### 2.2 Enable Debug Mode

Ensure debug mode is ON to see detailed timing logs:

```python
class Config:
    # ... other settings ...
    
    # =================== Debug/Logging ============================
    DEBUG_MODE = True  # ← Make sure this is True
```

### 2.3 Mark Test Bottles

Prepare 10-20 test bottles:
- Mark them clearly (e.g., colored tape)
- Make them intentionally defective (if testing ejection)
- Or use known good bottles for position testing

---

## 🧪 Phase 3: Test Runs

### 3.1 Dry Run (No Ejection)

**Purpose:** Verify detection and timing calculation without actually ejecting.

**Steps:**
1. Comment out ejection command temporarily:

```python
# In EjectionScheduler._ejection_loop()
def _ejection_loop(self):
    # ...
    # self.arduino.reject_bottle()  # ← Comment this line
    print(f"[DRY RUN] Would eject at {time.time()}")  # ← Add this
```

2. Run system:
```bash
python3 main_continuous_flow.py
```

3. Observe console output:
```
🍾 BOTTLE #1 DETECTED at 2025-12-05 14:30:00
📸 Burst capturing 5 frames...
🧠 Running AI detection...
📅 Scheduled ejection for bottle #1 in 2.10s
[DRY RUN] Would eject at 1701785402.35
```

4. Manually observe when bottle reaches ejection point
5. Compare actual position with predicted time

### 3.2 First Live Test

**Warning:** Start with slow conveyor speed for safety.

1. Uncomment ejection code
2. Place ONE test bottle
3. Run system
4. Observe result:
   - ✅ **Hit**: Bottle successfully ejected
   - ❌ **Early**: Servo triggered before bottle arrived
   - ❌ **Late**: Servo triggered after bottle passed

### 3.3 Adjustment

Based on results:

| Observation | Action | Example |
|-------------|--------|---------|
| Ejection **too early** | INCREASE `PHYSICAL_DELAY` | 2.1 → 2.2 |
| Ejection **too late** | DECREASE `PHYSICAL_DELAY` | 2.1 → 2.0 |
| Ejection **just right** | Record final value! | 2.1 ✓ |

**Adjustment increments:**
- First iteration: ±0.2s
- Second iteration: ±0.1s
- Fine-tuning: ±0.05s

### 3.4 Multiple Bottle Test

Once individual ejections work:

1. Place 5 bottles on conveyor (spaced apart)
2. Run system
3. Count: How many were successfully ejected?
4. Target: **≥90% success rate**

### 3.5 Varying Speeds

If your system has variable conveyor speed:

1. Test at MIN speed → Record `PHYSICAL_DELAY_MIN`
2. Test at MAX speed → Record `PHYSICAL_DELAY_MAX`
3. Test at NORMAL speed → Record `PHYSICAL_DELAY_NORMAL`

**Note:** If delay varies significantly, you may need to implement dynamic delay calculation based on current speed.

---

## 📊 Phase 4: Fine-Tuning Parameters

### 4.1 Burst Capture Timing

**DELAY_SENSOR_TO_CAPTURE**: Time from IR sensor trigger to first frame capture.

**Purpose:** Ensure bottle is in optimal camera view when capture starts.

**Default:** `0.2` seconds

**To calibrate:**
1. Run system with `DEBUG_MODE = True`
2. Check captured frames - is bottle centered?
3. Adjust:
   - Bottle **not yet visible** → INCREASE delay
   - Bottle **already passing** → DECREASE delay

```python
DELAY_SENSOR_TO_CAPTURE = 0.2  # Adjust this
```

### 4.2 Burst Interval

**BURST_INTERVAL**: Time between consecutive frame captures.

**Default:** `0.05` seconds (50ms)

**To calibrate:**
1. Check if all 5 frames show the same bottle
2. If bottle moves too fast and last frames are different bottle:
   → DECREASE interval (e.g., 0.03s)
3. If frames are too similar (not enough angles):
   → INCREASE interval (e.g., 0.08s)

```python
BURST_INTERVAL = 0.05  # Adjust this
```

### 4.3 Voting Threshold

**VOTING_THRESHOLD**: Minimum frames (out of 5) that must agree on defect.

**Default:** `3` (majority)

**Trade-offs:**

| Value | Effect | Use Case |
|-------|--------|----------|
| 2/5 | More sensitive, higher false positives | When cost of missing defect is high |
| 3/5 | Balanced (recommended) | General production use |
| 4/5 | More conservative, might miss defects | When false positives are costly |

**To calibrate:**
1. Run 100 bottles through system
2. Count:
   - True Positives (TP): Correctly detected defects
   - False Positives (FP): Good bottles marked as bad
   - False Negatives (FN): Missed defects
3. Calculate metrics:
   ```
   Precision = TP / (TP + FP)
   Recall = TP / (TP + FN)
   ```
4. Adjust threshold to meet your requirements

```python
VOTING_THRESHOLD = 3  # Adjust based on metrics
```

### 4.4 AI Confidence Threshold

**CONFIDENCE_THRESHOLD**: Minimum AI confidence to consider detection valid.

**Default:** `0.5` (50%)

**To calibrate:**
1. Run test set and log all confidences
2. Plot histogram of confidence scores
3. Find threshold that maximizes F1 score

```python
CONFIDENCE_THRESHOLD = 0.5  # Adjust this
```

---

## 📝 Phase 5: Documentation

### 5.1 Record Final Values

**Create a calibration record file:** `calibration_record.txt`

```txt
================================================================================
SYSTEM CALIBRATION RECORD
================================================================================
Date: 2025-12-05
Operator: [Your Name]
System: Coca-Cola Bottle Defect Detection

PHYSICAL MEASUREMENTS:
  Distance (camera to ejector): 60 cm
  Conveyor speed: 28.57 cm/s
  Calculated delay: 2.1 s

CALIBRATED VALUES:
  PHYSICAL_DELAY: 2.15 s
  DELAY_SENSOR_TO_CAPTURE: 0.22 s
  BURST_INTERVAL: 0.05 s
  BURST_COUNT: 5
  VOTING_THRESHOLD: 3
  CONFIDENCE_THRESHOLD: 0.5

TEST RESULTS:
  Total test bottles: 50
  Successful ejections: 48
  Success rate: 96%
  
NOTES:
  - Lighting conditions: Indoor, overhead LED
  - Bottle type: Standard 330ml Coca-Cola
  - Ambient temperature: 25°C
  
APPROVED BY: [Name]
DATE: 2025-12-05
================================================================================
```

### 5.2 Update Production Config

Create a **separate production config**:

```python
# production_config.py
class ProductionConfig:
    """Production-calibrated configuration - DO NOT CHANGE without approval"""
    
    # Calibrated on: 2025-12-05
    # Approved by: [Name]
    
    PHYSICAL_DELAY = 2.15
    DELAY_SENSOR_TO_CAPTURE = 0.22
    BURST_INTERVAL = 0.05
    VOTING_THRESHOLD = 3
    CONFIDENCE_THRESHOLD = 0.5
```

---

## 🔄 Phase 6: Periodic Re-calibration

### When to Re-calibrate?

✅ **Every 30 days** (routine maintenance)  
✅ **After conveyor speed change**  
✅ **After mechanical adjustments**  
✅ **After camera repositioning**  
✅ **If success rate drops below 90%**  

### Quick Re-calibration Procedure

1. Run 20 test bottles
2. Count successes
3. If < 18 successful (90%):
   - Review logs for timing errors
   - Adjust `PHYSICAL_DELAY` by ±0.1s
   - Test again
4. Document changes

---

## 🎯 Success Criteria

### Minimum Requirements (Production Ready)

- ✅ **Ejection Success Rate**: ≥90%
- ✅ **Detection Accuracy**: ≥85%
- ✅ **False Positive Rate**: ≤10%
- ✅ **Timing Precision**: ±100ms
- ✅ **Uptime**: ≥4 hours continuous

### Optimal Performance

- 🌟 **Ejection Success Rate**: ≥95%
- 🌟 **Detection Accuracy**: ≥90%
- 🌟 **False Positive Rate**: ≤5%
- 🌟 **Timing Precision**: ±50ms
- 🌟 **Uptime**: ≥8 hours continuous

---

## 🐛 Troubleshooting Calibration Issues

### Issue: Inconsistent Ejection Timing

**Symptoms:** Sometimes hits, sometimes misses

**Possible Causes:**
1. Conveyor speed not constant
   - **Fix:** Check motor power supply stability
2. Bottles different sizes/weights
   - **Fix:** Test with single bottle type first
3. Threading delays
   - **Fix:** Check CPU load, reduce other processes

### Issue: All Ejections Too Early

**Symptoms:** Servo always triggers before bottle arrives

**Cause:** `PHYSICAL_DELAY` too small

**Fix:**
```python
PHYSICAL_DELAY = 2.15  # Old value
PHYSICAL_DELAY = 2.35  # Increase by 0.2s
```

### Issue: All Ejections Too Late

**Symptoms:** Servo always triggers after bottle passes

**Cause:** `PHYSICAL_DELAY` too large

**Fix:**
```python
PHYSICAL_DELAY = 2.15  # Old value
PHYSICAL_DELAY = 1.95  # Decrease by 0.2s
```

### Issue: Burst Captures Wrong Bottle

**Symptoms:** 5 frames show different bottles

**Cause:** `BURST_INTERVAL` too large or `BURST_COUNT` too high

**Fix:**
```python
BURST_COUNT = 5        # Old value
BURST_COUNT = 3        # Reduce count
BURST_INTERVAL = 0.05  # Old value
BURST_INTERVAL = 0.03  # Reduce interval
```

### Issue: Bottles Not Detected by IR Sensor

**Symptoms:** No "DETECTED" signals in console

**Possible Causes:**
1. IR sensor not connected
   - **Fix:** Check D2 wiring
2. IR sensor misaligned
   - **Fix:** Adjust sensor position to face bottles
3. IR sensor polarity wrong
   - **Fix:** Verify Active LOW wiring

**Debug:**
```bash
# Upload Arduino firmware
# Open Serial Monitor (115200 baud)
# Manually wave hand in front of IR sensor
# Should see "DETECTED" printed
```

---

## 📋 Calibration Checklist

Print this checklist for each calibration session:

```
□ Phase 1: Physical Measurements
  □ Measure distance: _____ cm
  □ Measure speed: _____ cm/s
  □ Calculate initial delay: _____ s

□ Phase 2: Software Configuration
  □ Edit PHYSICAL_DELAY in code
  □ Enable DEBUG_MODE
  □ Prepare test bottles

□ Phase 3: Test Runs
  □ Dry run (no ejection)
  □ First live test (1 bottle)
  □ Adjustment (if needed)
  □ Multi-bottle test (5 bottles)
  □ Success rate ≥90%

□ Phase 4: Fine-Tuning
  □ DELAY_SENSOR_TO_CAPTURE: _____ s
  □ BURST_INTERVAL: _____ s
  □ VOTING_THRESHOLD: _____
  □ CONFIDENCE_THRESHOLD: _____

□ Phase 5: Documentation
  □ Record final values
  □ Create calibration record
  □ Update production config

□ Phase 6: Validation
  □ 50-bottle test
  □ Success rate: _____%
  □ Meets requirements

Calibrated by: _____________
Date: _____________
Approved by: _____________
```

---

## 🎓 Tips for Perfect Calibration

1. **Start slow**: Use slowest conveyor speed for initial calibration
2. **Use markers**: Mark bottles with numbers to track individual performance
3. **Log everything**: Record all attempts, not just successes
4. **Test edge cases**: Try bottles at different positions on belt
5. **Environmental stability**: Same lighting, temperature during calibration
6. **Patience**: Perfect calibration takes 2-3 hours. Don't rush.
7. **Document**: Future you (or others) will thank you!

---

## ✅ Final Validation

Before declaring system production-ready:

1. Run **100 consecutive bottles**
2. Log all results
3. Calculate metrics:
   - Ejection success rate
   - Detection accuracy
   - Processing time per bottle
4. If all metrics meet requirements → **System ready!**
5. If not → Review this guide and re-calibrate

---

**With proper calibration, your system will achieve 95%+ accuracy! 🎯**

