# 🥤 Coca-Cola Sorting System

An intelligent product sorting system using Raspberry Pi 5, Arduino Uno, and AI-powered quality inspection.

## 📋 Overview

This system automatically inspects Coca-Cola bottles on a conveyor belt using computer vision and deep learning. It follows a **Stop-and-Go** workflow:

1. **Detection**: IR sensor detects bottle → Arduino stops conveyor
2. **Inspection**: Raspberry Pi captures image → AI model analyzes quality
3. **Sorting**: Pi sends decision → Arduino activates servo for NG products or passes OK products

## 🎯 Features

- **Real-time AI Inspection**: NCNN-optimized model running on Raspberry Pi
- **Strict Quality Control**: Detects defects AND verifies component presence
- **Professional UI**: Tkinter-based interface with live video feed
- **Complete History**: SQLite database tracks all inspections
- **Statistics Dashboard**: Monitor OK/NG rates and defect types
- **Dummy Modes**: Test without physical hardware

## 🛠️ Hardware Requirements

- **Raspberry Pi 5** (main controller)
- **Arduino Uno** (conveyor and servo control)
- **USB Camera** or **Pi Camera Module**
- **IR Proximity Sensor** (detection)
- **Relay Module** (conveyor control, LOW trigger)
- **Servo Motor SG90** (rejection mechanism)
- **12V DC Motor** (conveyor belt)

## 🔌 Wiring (Arduino)

```
IR Sensor → Pin 2
Relay    → Pin 4 (LOW = Run, HIGH = Stop)
Servo    → Pin 9
```

## 📦 Installation

### 1. Clone Repository

```bash
cd /home/pi
git clone <repository-url> Project_Graduation
cd Project_Graduation
```

### 2. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Install NCNN (Optional)

If NCNN is not installed, the system will run in demo mode with random predictions.

For Raspberry Pi:
```bash
# Follow NCNN installation guide for ARM64
# https://github.com/Tencent/ncnn/wiki/how-to-build#build-for-linux
```

### 4. Upload Arduino Code

1. Open `arduino/sorting_control.ino` in Arduino IDE
2. Select **Board**: Arduino Uno
3. Select **Port**: /dev/ttyUSB0 (or COM port on Windows)
4. Click **Upload**

### 5. Configure Serial Port

Edit `main.py` if your Arduino is on a different port:

```python
'arduino_port': '/dev/ttyUSB0',  # Linux
# or
'arduino_port': 'COM3',  # Windows
```

## 🚀 Usage

### Start the System

```bash
python3 main.py
```

### Test Model Only (Without Arduino)

Want to test AI model with live camera and see bounding boxes?

```bash
python3 test_model_live.py
```

This will:
- Show live camera feed
- Run AI detection in real-time
- Draw bounding boxes with class names
- Display confidence scores
- Show FPS and performance metrics

**Controls**: Q (quit), S (screenshot), SPACE (pause)

### Testing Without Hardware

Edit `main.py` to enable dummy modes:

```python
'use_dummy_camera': True,    # Simulate camera
'use_dummy_hardware': True   # Simulate Arduino
```

### Operation Steps

1. **Launch** the application
2. Click **"START SYSTEM"**
3. Place bottles on the conveyor
4. System automatically:
   - Detects bottles
   - Captures images
   - Runs AI inspection
   - Sorts based on results
5. View **"History"** for statistics

## 🧠 AI Model Specifications

### Model Format
- **Framework**: NCNN (Tencent Neural Compute Library)
- **Input Size**: 640×640
- **Format**: `best.ncnn.param` + `best.ncnn.bin`

### Class Mapping (8 Classes)

| Index | Class Name       | Type       |
|-------|------------------|------------|
| 0     | Cap-Defect       | Defect     |
| 1     | Filling-Defect   | Defect     |
| 2     | Label-Defect     | Defect     |
| 3     | Wrong-Product    | Defect     |
| 4     | cap              | Component  |
| 5     | coca             | Component  |
| 6     | filled           | Component  |
| 7     | label            | Component  |

### Sorting Logic

#### ❌ NG (Rejection) if:
1. **Any defect detected** (Class 0-3) with confidence > 0.5
2. **Missing critical components**:
   - Missing `cap` (Class 4), OR
   - Missing `filled` (Class 6), OR
   - Missing `label` (Class 7)

#### ✅ OK (Pass) only if:
- **No defects** detected (Class 0-3)
- **AND all components present**: cap, filled, label

## 📁 Project Structure

```
Project_Graduation/
├── arduino/
│   └── sorting_control.ino    # Arduino control code
├── captures/                   # Saved inspection images
│   ├── ok/                    # Pass images
│   └── ng/                    # Reject images
├── core/                       # Backend modules
│   ├── __init__.py
│   ├── ai.py                  # NCNN inference + sorting logic
│   ├── camera.py              # Threaded camera handler
│   ├── database.py            # SQLite database
│   └── hardware.py            # Serial communication
├── database/
│   └── product.db             # SQLite database (auto-created)
├── model/                      # AI model files
│   └── best_ncnn_model/
│       ├── model.ncnn.param
│       └── model.ncnn.bin
├── ui/                         # User interface
│   ├── __init__.py
│   ├── main_window.py         # Main control window
│   └── history_window.py      # History viewer
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🔧 Configuration

### Camera Settings

Edit `main.py`:

```python
'camera_id': 0,              # Use 0 for USB camera
# or
'camera_id': '/path/to/video.mp4',  # Use video file
```

### Model Path

If model is in a different location:

```python
'model_path': 'model/best_ncnn_model',
```

## 📊 Database Schema

### Inspections Table
- `id`: Primary key
- `timestamp`: Inspection time
- `result`: 'OK' or 'NG'
- `reason`: Explanation
- `has_cap`, `has_filled`, `has_label`: Boolean flags
- `defects`: Comma-separated defect list
- `image_path`: Path to saved image
- `processing_time`: Inference time (seconds)

### Statistics Table
- `date`: Date
- `total_count`, `ok_count`, `ng_count`: Daily counts

## 🐛 Troubleshooting

### Camera Not Opening
```bash
# List available cameras
ls /dev/video*

# Test camera
python3 -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"
```

### Arduino Not Connecting
```bash
# Check USB connection
ls /dev/ttyUSB*  # Linux
# or
ls /dev/ttyACM*

# Check permissions
sudo usermod -a -G dialout $USER
# Then logout and login
```

### NCNN Not Available
The system will automatically fall back to dummy mode for testing. To install NCNN, follow the official build guide.

## 📝 Communication Protocol

### Pi → Arduino
- `'O'`: OK result (pass bottle)
- `'N'`: NG result (reject bottle)
- `'S'`: Start system (unused in current version)
- `'X'`: Stop system (unused in current version)

### Arduino → Pi
- `'D'`: Bottle detected (trigger inspection)

## 🎥 Demo Mode

For testing without hardware:

```python
# In main.py
config = {
    'use_dummy_camera': True,
    'use_dummy_hardware': True
}
```

- **Dummy Camera**: Shows animated test pattern
- **Dummy Hardware**: Simulates detections every 5 seconds
- **Dummy AI**: Random OK/NG predictions (if NCNN unavailable)

## 📈 Performance

- **Inference Time**: ~100-300ms per image (Pi 5)
- **FPS**: 30 FPS video feed
- **Detection Latency**: <500ms
- **Sorting Accuracy**: Depends on model quality

## 🔐 Safety Features

- Graceful fallbacks for missing hardware
- Exception handling throughout
- Confirmation dialogs for destructive actions
- Thread-safe database operations

## 👥 Authors

Developed for Final Year Project - Embedded Systems & AI

## 📄 License

For educational purposes only.

---

**System Status**: ✅ Ready for Production

For issues or questions, check the logs or contact support.

