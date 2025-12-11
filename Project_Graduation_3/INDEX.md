# 📚 Project Documentation Index

## Quick Navigation

### Getting Started
1. **[README.md](README.md)** - Main project overview
2. **[QUICK_START.md](QUICK_START.md)** - Fast setup guide
3. **[TEST_SYSTEM.md](TEST_SYSTEM.md)** - Testing procedures

### Architecture & Design
4. **[PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md)** - System design details

### Configuration
5. **[config.py](config.py)** - All system settings

### Source Code

#### Core Modules
- **[core/ai.py](core/ai.py)** - NCNN AI engine with NMS ⭐
- **[core/camera.py](core/camera.py)** - Threaded camera capture
- **[core/hardware.py](core/hardware.py)** - Arduino serial communication
- **[core/database.py](core/database.py)** - SQLite database handler

#### UI Modules
- **[ui/main_window.py](ui/main_window.py)** - Main interface with virtual line
- **[ui/history_window.py](ui/history_window.py)** - History viewer

#### Entry Point
- **[main.py](main.py)** - Application entry point

#### Arduino
- **[arduino/sorting_control.ino](arduino/sorting_control.ino)** - Arduino firmware

### Run Scripts
- **[run.sh](run.sh)** - Linux/Mac run script
- **[run.bat](run.bat)** - Windows run script

---

## File Structure

```
Project_Graduation_3/
├── 📄 README.md                    # Main documentation
├── 📄 QUICK_START.md               # Quick setup guide
├── 📄 TEST_SYSTEM.md               # Testing guide
├── 📄 PROJECT_ARCHITECTURE.md      # Architecture details
├── 📄 INDEX.md                     # This file
├── ⚙️  config.py                    # Configuration
├── 🚀 main.py                      # Entry point
├── 📄 requirements.txt             # Python dependencies
├── 🔧 run.sh / run.bat             # Run scripts
├── 📁 arduino/
│   └── sorting_control.ino        # Arduino code
├── 📁 captures/                   # Saved images
│   ├── ok/
│   └── ng/
├── 📁 core/                       # Backend modules
│   ├── ai.py                      # AI engine ⭐
│   ├── camera.py                  # Camera handler
│   ├── hardware.py                # Serial communication
│   └── database.py                # Database handler
├── 📁 database/                   # SQLite files
│   └── product.db
├── 📁 model/                      # NCNN model files
│   ├── best.ncnn.param
│   └── best.ncnn.bin
└── 📁 ui/                         # Frontend modules
    ├── main_window.py             # Main UI
    └── history_window.py          # History viewer
```

---

## Key Features

### 1. FIFO Queue Logic
- Virtual line detection at camera
- Queue storage in memory
- Physical trigger at IR sensor
- FIFO processing (oldest first)

### 2. NCNN AI with NMS
- Fast inference on Raspberry Pi
- Proper Non-Maximum Suppression
- 8-class detection
- Strict sorting logic

### 3. Real-time UI
- Live camera feed
- Virtual line visualization
- Queue status display
- Statistics tracking

### 4. Hardware Integration
- Arduino Uno control
- Servo actuation
- IR sensor input
- Serial protocol

### 5. Data Logging
- SQLite database
- Image snapshots
- Processing statistics
- History viewer

---

## Development Workflow

### 1. Testing Phase
```bash
# Enable dummy mode
USE_DUMMY_CAMERA = True
USE_DUMMY_HARDWARE = True

# Test UI
python3 main.py
```

### 2. Camera Integration
```bash
# Enable real camera
USE_DUMMY_CAMERA = False

# Test detection
python3 main.py
```

### 3. Hardware Integration
```bash
# Enable Arduino
USE_DUMMY_HARDWARE = False

# Test full system
python3 main.py
```

### 4. Calibration
```bash
# Adjust config.py
VIRTUAL_LINE_X = 320
DETECTION_COOLDOWN = 1.0
CONFIDENCE_THRESHOLD = 0.5

# Test and iterate
python3 main.py
```

### 5. Production
```bash
# Finalize settings
DEBUG_MODE = False
VERBOSE_LOGGING = False

# Run
./run.sh  # or run.bat on Windows
```

---

## Critical Components

### Most Important Files

1. **core/ai.py** - The AI engine
   - NCNN model loading
   - Preprocessing
   - Inference
   - **NMS (critical for accuracy)**
   - Sorting logic

2. **ui/main_window.py** - The main UI
   - Virtual line drawing
   - Crossing detection
   - Queue management
   - Hardware callbacks

3. **arduino/sorting_control.ino** - Hardware control
   - IR sensor monitoring
   - Serial protocol
   - Servo control

4. **config.py** - System configuration
   - All tunable parameters
   - Easy calibration

---

## Common Tasks

### Change Virtual Line Position
```python
# config.py
VIRTUAL_LINE_X = 400  # Move to right
```

### Adjust Detection Sensitivity
```python
# config.py
CONFIDENCE_THRESHOLD = 0.3  # More sensitive
NMS_THRESHOLD = 0.3         # Keep more boxes
```

### Change Arduino Port
```python
# config.py
ARDUINO_PORT = '/dev/ttyUSB0'  # Linux
ARDUINO_PORT = 'COM3'          # Windows
```

### View History
```
Run system → Click "View History" button
```

### Debug Issues
```python
# config.py
DEBUG_MODE = True
VERBOSE_LOGGING = True
```

---

## Support & Troubleshooting

See **[TEST_SYSTEM.md](TEST_SYSTEM.md)** for:
- Common issues
- Solutions
- Debug procedures
- Performance benchmarks

---

## Version Info

- **Version:** 1.0
- **Date:** 2024
- **Platform:** Raspberry Pi 5 + Arduino Uno
- **Framework:** NCNN + OpenCV + Tkinter

---

**Happy Sorting! 🥤✨**

