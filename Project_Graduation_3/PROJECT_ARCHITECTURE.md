# 🏗️ Project Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FIFO QUEUE SORTING SYSTEM                │
└─────────────────────────────────────────────────────────────┘

INPUT (Camera)          QUEUE (Memory)        OUTPUT (IR Sensor)
     │                       │                       │
     ├─── Virtual Line       ├─── FIFO List         ├─── Physical Trigger
     │    Detection          │    Storage            │    Detection
     │                       │                       │
     ▼                       ▼                       ▼
  Classify              Add to Queue            Pop & Act
  (NCNN AI)            [(O/N), ...]           (Kick if N)
```

## Data Flow

### 1. Detection Phase (At Camera)

```python
# When bottle crosses virtual line:
frame = camera.get_frame()
result = ai.predict(frame)  # 'O' or 'N'
queue.append(result)  # Add to FIFO
save_snapshot(frame)
```

### 2. Queue Phase (In Memory)

```python
# Queue structure:
queue = [
    {'result': 'O', 'timestamp': '10:30:01', ...},
    {'result': 'N', 'timestamp': '10:30:03', ...},
    {'result': 'O', 'timestamp': '10:30:05', ...},
]
```

### 3. Trigger Phase (At IR Sensor)

```python
# When IR sensor detects:
Arduino -> Pi: 'T'
item = queue.pop(0)  # FIFO: oldest first
if item['result'] == 'N':
    Pi -> Arduino: 'K'  # Kick command
```

## NCNN Processing Pipeline

### Preprocessing
```python
frame (640x480 BGR)
    ↓ resize
resized (640x640 BGR)
    ↓ to ncnn.Mat
mat (640x640 BGR)
    ↓ normalize
normalized (mean=0, norm=1/255)
```

### Inference
```python
ex = net.create_extractor()
ex.input("in0", mat_in)
ret, mat_out = ex.extract("out0")
```

### Output Parsing
```python
# Raw output shape: (8400, 84) or (84, 8400)
# Transpose if needed
if shape[0] < shape[1]:
    out = out.T

# Each detection: [x, y, w, h, class_scores...]
for i in range(8400):
    x, y, w, h = out[i, 0:4]
    class_scores = out[i, 4:12]  # 8 classes
    class_id = argmax(class_scores)
    confidence = class_scores[class_id]
```

### NMS (Critical!)
```python
# Apply Non-Maximum Suppression
indices = cv2.dnn.NMSBoxes(
    boxes,          # List of [x, y, w, h]
    confidences,    # List of confidence scores
    0.5,            # conf_threshold
    0.45            # nms_threshold
)

# Keep only filtered detections
filtered = [detections[i] for i in indices]
```

### Sorting Logic
```python
# Check for defects (classes 0-3)
has_defects = any(d['class_id'] in [0,1,2,3] for d in detections)

# Check for required components
has_cap = any(d['class_id'] == 4 for d in detections)
has_filled = any(d['class_id'] == 6 for d in detections)
has_label = any(d['class_id'] == 7 for d in detections)

# Decision
if has_defects or not (has_cap and has_filled and has_label):
    result = 'N'  # NG
else:
    result = 'O'  # OK
```

## Threading Model

```
Main Thread (Tkinter UI)
    │
    ├─── Camera Thread
    │    └─── Continuous frame capture
    │
    ├─── Hardware Thread
    │    └─── Serial listener (waits for 'T')
    │
    └─── Detection Thread (spawned per bottle)
         └─── AI processing + Queue append
```

## Serial Protocol

### Arduino → Pi
- `'T'` - Trigger: IR sensor detected bottle

### Pi → Arduino
- `'K'` - Kick: Activate servo to reject bottle
- `'O'` - OK: Bottle passed (optional, for logging)

## Database Schema

### inspections table
```sql
CREATE TABLE inspections (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    result TEXT,              -- 'O' or 'N'
    reason TEXT,              -- Why NG
    has_cap INTEGER,
    has_filled INTEGER,
    has_label INTEGER,
    has_defects INTEGER,
    defects TEXT,             -- Comma-separated
    image_path TEXT,
    processing_time REAL
)
```

### statistics table
```sql
CREATE TABLE statistics (
    id INTEGER PRIMARY KEY,
    date TEXT,
    total_count INTEGER,
    ok_count INTEGER,
    ng_count INTEGER,
    avg_processing_time REAL
)
```

## Key Algorithms

### Virtual Line Crossing Detection
```python
# Simple blob detection
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
contours, _ = cv2.findContours(thresh, ...)

# Find largest (bottle)
largest = max(contours, key=cv2.contourArea)
cx, cy = get_center(largest)

# Check if near virtual line
if abs(cx - VIRTUAL_LINE_X) < TOLERANCE:
    detect_bottle()
```

### Cooldown Timer
```python
# Prevent double detection
current_time = time.time()
if current_time - last_detection_time < COOLDOWN:
    return  # Skip

# Process detection
last_detection_time = current_time
```

## Configuration Strategy

All settings in `config.py` for easy tuning:
- Thresholds (AI, NMS)
- Line position
- Timing (cooldown)
- Ports (Arduino, Camera)
- Debug flags

## Error Handling

### Graceful Degradation
```python
try:
    import ncnn
except ImportError:
    # Use dummy mode for UI testing
    NCNN_AVAILABLE = False
```

### Hardware Fallback
```python
if not hardware.is_connected():
    print("Warning: Arduino not connected")
    response = input("Continue anyway? (y/n): ")
```

### Thread Safety
```python
# Camera frame access
with self.lock:
    frame = self.frame.copy()
```

---

This architecture ensures:
- ✅ **Modularity**: Each component is independent
- ✅ **Reliability**: Graceful error handling
- ✅ **Performance**: Threaded processing
- ✅ **Accuracy**: NMS removes duplicate detections
- ✅ **Maintainability**: Clear separation of concerns

