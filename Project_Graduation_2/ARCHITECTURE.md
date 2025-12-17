# 🏗️ System Architecture - Coca-Cola Sorting System

## 📐 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     COCA-COLA SORTING SYSTEM                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────┐         ┌──────────────────────┐
│   RASPBERRY PI 5    │◄───────►│    ARDUINO UNO       │
│   (Main Control)    │  Serial │  (Motor Control)     │
│                     │  USB    │                      │
│  ┌──────────────┐   │         │  ┌────────────────┐  │
│  │  AI Engine   │   │         │  │ Sensor Reading │  │
│  │   (NCNN)     │   │         │  │ Relay Control  │  │
│  └──────────────┘   │         │  │ Servo Control  │  │
│                     │         │  └────────────────┘  │
│  ┌──────────────┐   │         └──────────┬───────────┘
│  │   Camera     │   │                    │
│  │  (OpenCV)    │   │                    │
│  └──────────────┘   │         ┌──────────▼───────────┐
│                     │         │   PHYSICAL LAYER     │
│  ┌──────────────┐   │         │                      │
│  │   Database   │   │         │  • IR Sensor         │
│  │   (SQLite)   │   │         │  • Relay Module      │
│  └──────────────┘   │         │  • Servo Motor       │
│                     │         │  • DC Motor          │
│  ┌──────────────┐   │         └──────────────────────┘
│  │      UI      │   │
│  │   (Tkinter)  │   │
│  └──────────────┘   │
└─────────────────────┘
```

---

## 🔄 Data Flow Diagram

```
                    ┌─────────────────────────┐
                    │   START: Conveyor Run   │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   IR Sensor Detects     │
                    │       Bottle            │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Arduino: Stop Motor    │
                    │  Send 'D' to Pi         │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Pi: Capture Image      │
                    │  (640x640 RGB)          │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  AI: NCNN Inference     │
                    │  Detect 8 Classes       │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Apply Sorting Logic    │
                    │  • Check Defects        │
                    │  • Check Components     │
                    └────────────┬────────────┘
                                 │
                ┌────────────────┴────────────────┐
                │                                 │
   ┌────────────▼────────────┐     ┌─────────────▼────────────┐
   │      Result: OK         │     │      Result: NG          │
   └────────────┬────────────┘     └─────────────┬────────────┘
                │                                 │
   ┌────────────▼────────────┐     ┌─────────────▼────────────┐
   │  Pi: Send 'O'           │     │  Pi: Send 'N'            │
   │  Save to captures/ok/   │     │  Save to captures/ng/    │
   │  Log to Database        │     │  Log to Database         │
   └────────────┬────────────┘     └─────────────┬────────────┘
                │                                 │
   ┌────────────▼────────────┐     ┌─────────────▼────────────┐
   │  Arduino: Resume Motor  │     │  Arduino: Move to Servo  │
   │  Bottle Continues       │     │  Activate Servo (Kick)   │
   └────────────┬────────────┘     │  Resume Motor            │
                │                  └─────────────┬────────────┘
                │                                 │
                └────────────┬────────────────────┘
                             │
                ┌────────────▼────────────┐
                │   Return to START       │
                └─────────────────────────┘
```

---

## 🧩 Software Component Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                          main.py                               │
│                    (Application Entry)                         │
└────────────┬───────────────────────────────────────────────────┘
             │
             │ Initializes & Coordinates
             │
    ┌────────┴────────┬────────────┬────────────┬────────────┐
    │                 │            │            │            │
┌───▼───┐      ┌──────▼─────┐  ┌──▼──┐    ┌────▼────┐  ┌───▼────┐
│  UI   │      │   Camera   │  │ AI  │    │Hardware │  │Database│
│Module │      │   Module   │  │Eng. │    │ Module  │  │ Module │
└───┬───┘      └──────┬─────┘  └──┬──┘    └────┬────┘  └───┬────┘
    │                 │           │            │           │
    │  Display        │  Frames   │  Predict   │  Commands │  Log
    │  Control        │           │            │           │
    │                 │           │            │           │
    └─────────────────┴───────────┴────────────┴───────────┘
                              │
                    ┌─────────▼──────────┐
                    │   Event Loop       │
                    │   (Tkinter)        │
                    └────────────────────┘
```

---

## 📦 Module Breakdown

### 1. Core Modules (`core/`)

#### `ai.py` - AI Engine
```
AIEngine
├── __init__()          # Load NCNN model
├── predict(frame)      # Run inference
├── _preprocess()       # Resize to 640x640
├── _inference()        # NCNN forward pass
├── _apply_sorting_logic() # OK/NG decision
└── draw_detections()   # Visualize results
```

**Key Logic**:
- Load `model.ncnn.param` and `model.ncnn.bin`
- Input: 640×640 RGB image
- Output: List of detections (class, confidence, bbox)
- Decision: NG if defects OR missing components

#### `camera.py` - Camera Handler
```
Camera
├── __init__()          # Configure camera
├── start()             # Start capture thread
├── _update()           # Continuous frame reading
├── read()              # Get current frame
├── capture_snapshot()  # Single frame capture
├── save_image()        # Save to disk
└── stop()              # Cleanup
```

**Features**:
- Threaded capture (non-blocking)
- FPS monitoring
- Thread-safe frame access
- Auto-retry on errors

#### `database.py` - Database Handler
```
Database
├── __init__()              # Connect to SQLite
├── _init_database()        # Create tables
├── add_inspection()        # Insert record
├── get_recent_inspections() # Query history
├── get_statistics()        # Calculate stats
├── get_defect_summary()    # Defect analysis
└── clear_history()         # Delete records
```

**Schema**:
- `inspections`: Full inspection records
- `statistics`: Daily aggregates

#### `hardware.py` - Hardware Controller
```
HardwareController
├── __init__()          # Configure serial
├── connect()           # Open serial port
├── send_command()      # Send 'O', 'N', 'S', 'X'
├── read_line()         # Read from Arduino
├── start_listening()   # Start listener thread
├── _listen()           # Continuous reading
└── disconnect()        # Close serial
```

**Protocol**:
- Pi → Arduino: `'O'` (OK), `'N'` (NG)
- Arduino → Pi: `'D'` (Detection)

---

### 2. UI Modules (`ui/`)

#### `main_window.py` - Main Window
```
MainWindow
├── __init__()              # Build UI
├── _build_ui()             # Create widgets
├── _update_video()         # Video loop (30 FPS)
├── start_system()          # Start sorting
├── stop_system()           # Stop sorting
├── on_bottle_detected()    # Handle detection
├── _display_result()       # Show result
└── on_closing()            # Cleanup
```

**Layout**:
- Left: Live camera feed
- Right: Snapshot, result, details, stats, controls

#### `history_window.py` - History Viewer
```
HistoryWindow
├── __init__()              # Build UI
├── _build_ui()             # Create table
├── _load_data()            # Load from DB
├── on_row_double_click()   # Show image
├── _show_image()           # Image popup
├── clear_history()         # Delete records
└── show_defect_summary()   # Defect stats
```

**Features**:
- Sortable table
- Image viewer
- Statistics summary
- Defect analysis

---

### 3. Arduino Firmware (`arduino/`)

#### `sorting_control.ino`
```
Functions:
├── setup()                 # Initialize pins, serial
├── loop()                  # Main loop (run conveyor)
├── handleBottleDetection() # Detection workflow
├── waitForDecision()       # Wait for 'O' or 'N'
├── handleOKProduct()       # Pass bottle
├── handleNGProduct()       # Reject bottle
├── stopConveyor()          # Relay HIGH
└── startConveyor()         # Relay LOW
```

**State Machine**:
1. IDLE: Conveyor running, sensor monitoring
2. DETECTED: Stop, send 'D', wait for decision
3. OK: Resume conveyor
4. NG: Move to servo, kick, resume

---

## 🔌 Hardware Interface Layer

```
┌─────────────────────────────────────────────────────────┐
│                  RASPBERRY PI 5                         │
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│  │  Camera  │    │   USB    │    │  GPIO    │         │
│  │  Module  │    │  Serial  │    │ (Future) │         │
│  └────┬─────┘    └────┬─────┘    └──────────┘         │
└───────┼───────────────┼──────────────────────────────────┘
        │               │
        │ CSI/USB       │ USB
        │               │
┌───────▼───────┐ ┌─────▼──────────────────────────────────┐
│   Camera      │ │         ARDUINO UNO                    │
│   (USB/Pi)    │ │                                        │
└───────────────┘ │  Pin 2 ──► IR Sensor                  │
                  │  Pin 4 ──► Relay IN                   │
                  │  Pin 9 ──► Servo Signal               │
                  │  5V    ──► Sensors/Servo VCC          │
                  │  GND   ──► Common Ground              │
                  └─────┬──────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼─────┐  ┌──────▼──────┐  ┌────▼────┐
│  IR Sensor  │  │    Relay    │  │  Servo  │
│   (FC-51)   │  │   Module    │  │  SG90   │
└─────────────┘  └──────┬──────┘  └─────────┘
                        │
                 ┌──────▼──────┐
                 │ Motor Driver│
                 │   (L298N)   │
                 └──────┬──────┘
                        │
                 ┌──────▼──────┐
                 │  DC Motor   │
                 │ (Conveyor)  │
                 └─────────────┘
```

---

## 🎯 Sorting Logic Flowchart

```
                    ┌─────────────────┐
                    │  AI Detections  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Parse Results   │
                    │ (8 Classes)     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────────────┐
                    │ Check for Defects       │
                    │ (Class 0, 1, 2, 3)      │
                    └────────┬────────────────┘
                             │
                   ┌─────────┴─────────┐
                   │                   │
              YES  │                   │  NO
        ┌──────────▼────────┐          │
        │   Return NG       │          │
        │   (Defect Found)  │          │
        └───────────────────┘          │
                                       │
                          ┌────────────▼────────────┐
                          │ Check Components        │
                          │ • Class 4 (cap)         │
                          │ • Class 6 (filled)      │
                          │ • Class 7 (label)       │
                          └────────────┬────────────┘
                                       │
                          ┌────────────┴────────────┐
                          │                         │
                     YES  │                         │  NO
               ┌──────────▼────────┐    ┌──────────▼────────┐
               │   Return OK       │    │   Return NG       │
               │ (All Present)     │    │ (Missing Parts)   │
               └───────────────────┘    └───────────────────┘
```

---

## 🧵 Threading Model

```
┌─────────────────────────────────────────────────────────────┐
│                      MAIN THREAD                            │
│                   (Tkinter Event Loop)                      │
│                                                             │
│  • UI Updates                                               │
│  • User Input Handling                                      │
│  • Window Management                                        │
└────────────┬────────────────────────────────────────────────┘
             │
             │ Spawns
             │
    ┌────────┴─────────┬──────────────┬─────────────┐
    │                  │              │             │
┌───▼────────┐  ┌──────▼──────┐  ┌───▼────┐  ┌─────▼─────┐
│  Camera    │  │  Hardware   │  │   AI   │  │ Database  │
│  Thread    │  │  Listener   │  │ Thread │  │  Thread   │
│            │  │  Thread     │  │(Async) │  │  (Async)  │
└────────────┘  └─────────────┘  └────────┘  └───────────┘
     │                 │
     │ Continuous      │ Continuous
     │ Capture         │ Serial Read
     │                 │
     │                 │ Callback on 'D'
     │                 └──────────────────┐
     │                                    │
     │                         ┌──────────▼──────────┐
     │                         │  Inspection Task    │
     │◄────────────────────────┤  • Capture          │
     │  Get Frame              │  • AI Predict       │
     │                         │  • Save Image       │
     │                         │  • Log to DB        │
     │                         │  • Send Result      │
     │                         └─────────────────────┘
     │
     └─► Shared Frame Buffer (Thread-Safe Lock)
```

---

## 💾 Database Schema

```sql
-- Inspections Table
CREATE TABLE inspections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,           -- ISO format
    result TEXT NOT NULL,              -- 'OK' or 'NG'
    reason TEXT,                       -- Explanation
    has_cap INTEGER,                   -- Boolean (0/1)
    has_filled INTEGER,                -- Boolean (0/1)
    has_label INTEGER,                 -- Boolean (0/1)
    defects TEXT,                      -- Comma-separated
    image_path TEXT,                   -- Path to saved image
    processing_time REAL               -- Seconds
);

-- Statistics Table
CREATE TABLE statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,         -- YYYY-MM-DD
    total_count INTEGER DEFAULT 0,
    ok_count INTEGER DEFAULT 0,
    ng_count INTEGER DEFAULT 0
);

-- Indexes
CREATE INDEX idx_timestamp ON inspections(timestamp);
CREATE INDEX idx_result ON inspections(result);
```

---

## 📡 Communication Protocol

### Serial Protocol (Pi ↔ Arduino)

```
┌─────────────────────────────────────────────────────────┐
│                  SERIAL COMMUNICATION                   │
│                    (9600 baud, 8N1)                     │
└─────────────────────────────────────────────────────────┘

Pi → Arduino:
┌─────────┬──────────────────────────────────────────────┐
│ Command │ Meaning                                      │
├─────────┼──────────────────────────────────────────────┤
│   'O'   │ OK result - Pass bottle                     │
│   'N'   │ NG result - Reject bottle                   │
│   'S'   │ Start system (reserved)                     │
│   'X'   │ Stop system (reserved)                      │
└─────────┴──────────────────────────────────────────────┘

Arduino → Pi:
┌─────────┬──────────────────────────────────────────────┐
│ Command │ Meaning                                      │
├─────────┼──────────────────────────────────────────────┤
│   'D'   │ Bottle detected - Trigger inspection        │
│  Text   │ Debug messages (ignored by Pi)              │
└─────────┴──────────────────────────────────────────────┘

Timing:
┌─────────────────────────────────────────────────────────┐
│ Event                    │ Time                         │
├──────────────────────────┼──────────────────────────────┤
│ Detection to 'D' sent    │ ~500ms (stabilization)       │
│ 'D' to inspection start  │ <50ms                        │
│ Inspection duration      │ 100-300ms                    │
│ Result to Arduino        │ <50ms                        │
│ Arduino timeout          │ 10 seconds                   │
└──────────────────────────┴──────────────────────────────┘
```

---

## 🎨 UI Component Tree

```
Root Window (1280x720)
│
├── Main Frame
│   │
│   ├── Top Bar
│   │   ├── Title Label: "🥤 COCA-COLA SORTING SYSTEM"
│   │   └── Status Label: "● RUNNING" / "● STOPPED"
│   │
│   ├── Left Panel (Live Video)
│   │   ├── Video Label (640x480)
│   │   └── FPS Label
│   │
│   └── Right Panel (Results & Controls)
│       │
│       ├── Snapshot Frame
│       │   └── Snapshot Label (350x260)
│       │
│       ├── Result Frame
│       │   ├── Result Label: "✓ OK" / "✗ NG"
│       │   └── Reason Label
│       │
│       ├── Details Frame
│       │   └── Text Widget (Components, Defects)
│       │
│       ├── Statistics Frame
│       │   └── Stats Label (Total, OK, NG)
│       │
│       └── Control Frame
│           ├── Start Button
│           ├── Stop Button
│           ├── History Button
│           └── Exit Button
│
└── History Window (Popup)
    ├── Statistics Summary
    ├── Inspection Table (Treeview)
    └── Control Buttons
```

---

## 🔐 Error Handling Strategy

```
┌─────────────────────────────────────────────────────────┐
│                  ERROR HANDLING LAYERS                  │
└─────────────────────────────────────────────────────────┘

Layer 1: Hardware Failures
├── Camera not found → Switch to Dummy Camera
├── Arduino not connected → Switch to Dummy Hardware
└── Serial timeout → Log error, continue

Layer 2: Software Errors
├── NCNN not available → Use dummy predictions
├── Model load failure → Fallback to demo mode
└── Database error → Log to console, continue

Layer 3: Runtime Exceptions
├── Frame capture failed → Use previous frame
├── Inference error → Return default OK
└── UI error → Log and refresh

Layer 4: User Errors
├── Invalid input → Show message box
├── System busy → Ignore duplicate commands
└── Destructive action → Confirmation dialog

Recovery Strategy:
├── Graceful degradation (dummy modes)
├── Automatic retry (transient errors)
├── User notification (critical errors)
└── Complete logging (debugging)
```

---

## 📊 Performance Characteristics

```
┌─────────────────────────────────────────────────────────┐
│                  PERFORMANCE METRICS                    │
└─────────────────────────────────────────────────────────┘

Raspberry Pi 5:
├── CPU: Quad-core ARM Cortex-A76 @ 2.4GHz
├── RAM: 4GB/8GB LPDDR4X
├── AI Inference: 100-300ms (NCNN optimized)
├── Camera FPS: 30 FPS (640x480)
└── UI Refresh: 30 FPS

Arduino Uno:
├── CPU: ATmega328P @ 16MHz
├── Loop Time: <1ms
├── Serial: 9600 baud (960 bytes/sec)
└── GPIO Response: <1µs

System Throughput:
├── Detection Latency: <500ms
├── Inspection Time: 100-300ms
├── Sorting Decision: <50ms
├── Total Cycle: 2-3 seconds
└── Max Throughput: 20-30 bottles/minute

Resource Usage:
├── Python Memory: ~200MB
├── CPU Usage: 30-50% (during inference)
├── Disk I/O: Minimal (SQLite + images)
└── Network: None (standalone system)
```

---

## 🔄 State Diagram

```
                    ┌──────────┐
                    │  INIT    │
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │ STOPPED  │◄────────────┐
                    └────┬─────┘             │
                         │ Start             │ Stop
                    ┌────▼─────┐             │
                    │  IDLE    │─────────────┘
                    └────┬─────┘
                         │ Detection
                    ┌────▼─────┐
                    │DETECTING │
                    └────┬─────┘
                         │ 'D' Sent
                    ┌────▼─────┐
                    │CAPTURING │
                    └────┬─────┘
                         │ Image Ready
                    ┌────▼─────┐
                    │PROCESSING│
                    └────┬─────┘
                         │ Result Ready
                    ┌────▼─────┐
                    │ SORTING  │
                    └────┬─────┘
                         │ Complete
                    ┌────▼─────┐
                    │  IDLE    │
                    └──────────┘
```

---

## 🎯 Design Patterns Used

### 1. **Singleton Pattern**
- `Database`: Single connection instance
- `AIEngine`: Single model instance

### 2. **Observer Pattern**
- Hardware listener → Callback on detection
- Camera thread → Frame buffer updates

### 3. **Strategy Pattern**
- Real vs Dummy Camera
- Real vs Dummy Hardware

### 4. **Factory Pattern**
- Camera creation (USB vs Pi vs Dummy)
- Hardware creation (Serial vs Dummy)

### 5. **MVC Pattern**
- Model: Core modules (AI, Camera, Hardware, Database)
- View: UI modules (MainWindow, HistoryWindow)
- Controller: main.py (coordinates components)

---

## 📝 Configuration Management

```python
# main.py - Central Configuration
config = {
    # Hardware
    'camera_id': 0,
    'camera_width': 640,
    'camera_height': 480,
    'arduino_port': '/dev/ttyUSB0',
    'arduino_baudrate': 9600,
    
    # AI
    'model_path': 'model/best_ncnn_model',
    'confidence_threshold': 0.5,
    
    # Testing
    'use_dummy_camera': False,
    'use_dummy_hardware': False,
    
    # Paths
    'db_path': 'database/product.db',
    'captures_ok': 'captures/ok',
    'captures_ng': 'captures/ng'
}
```

---

## 🎓 Architecture Principles

### 1. **Modularity**
- Each component is independent
- Clear interfaces between modules
- Easy to test and maintain

### 2. **Scalability**
- Add new AI models easily
- Support multiple cameras
- Extend database schema

### 3. **Reliability**
- Graceful degradation
- Comprehensive error handling
- Automatic recovery

### 4. **Maintainability**
- Clean code structure
- Extensive documentation
- Consistent naming conventions

### 5. **Testability**
- Dummy modes for unit testing
- Modular components
- Clear separation of concerns

---

**This architecture ensures a robust, maintainable, and scalable sorting system.**

