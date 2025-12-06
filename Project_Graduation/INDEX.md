# 📚 Project Index - Coca-Cola Sorting System

Complete guide to all files and documentation in this project.

---

## 🚀 Getting Started (Read These First)

| File | Purpose | When to Read |
|------|---------|--------------|
| **README.md** | Main project documentation | Start here for overview |
| **QUICK_START.md** | 5-minute quick start guide | When you want to run it fast |
| **PROJECT_SUMMARY.md** | Complete project summary | For understanding scope |

---

## 📖 Documentation Files

### Setup & Installation

| File | Description | Target Audience |
|------|-------------|-----------------|
| **SETUP_GUIDE.md** | Complete setup guide (9 parts) | First-time installers |
| **WINDOWS_SETUP.md** | Windows-specific instructions | Windows developers |
| **QUICK_START.md** | Fast installation & run | Experienced users |

### Technical Documentation

| File | Description | Target Audience |
|------|-------------|-----------------|
| **ARCHITECTURE.md** | System architecture & design | Developers, reviewers |
| **PROJECT_SUMMARY.md** | Complete project overview | Managers, evaluators |
| **README.md** | Main documentation | Everyone |
| **INDEX.md** | This file - navigation guide | Everyone |

---

## 💻 Source Code Files

### Main Application

| File | Lines | Purpose |
|------|-------|---------|
| `main.py` | ~200 | Application entry point, initialization |

### Core Modules (`core/`)

| File | Lines | Purpose |
|------|-------|---------|
| `core/__init__.py` | ~10 | Module initialization |
| `core/ai.py` | ~400 | AI inference engine (NCNN) |
| `core/camera.py` | ~300 | Threaded camera capture |
| `core/database.py` | ~400 | SQLite database handler |
| `core/hardware.py` | ~350 | Serial communication with Arduino |

### User Interface (`ui/`)

| File | Lines | Purpose |
|------|-------|---------|
| `ui/__init__.py` | ~10 | Module initialization |
| `ui/main_window.py` | ~450 | Main control window (Tkinter) |
| `ui/history_window.py` | ~300 | History viewer window |

### Arduino Firmware (`arduino/`)

| File | Lines | Purpose |
|------|-------|---------|
| `arduino/sorting_control.ino` | ~200 | Arduino C++ control code |

---

## 🤖 AI Model Files (`model/`)

| File | Size | Purpose |
|------|------|---------|
| `model/best_ncnn_model/model.ncnn.param` | ~50KB | NCNN model structure |
| `model/best_ncnn_model/model.ncnn.bin` | ~6MB | NCNN model weights |
| `model/best_ncnn_model/metadata.yaml` | ~1KB | Class names & metadata |
| `model/best_ncnn_model/model_ncnn.py` | ~5KB | Python inference wrapper |

---

## 📁 Directory Structure

```
Project_Graduation/
│
├── 📄 Documentation (Markdown files)
│   ├── README.md                  # Main documentation
│   ├── QUICK_START.md             # Quick start guide
│   ├── SETUP_GUIDE.md             # Complete setup (9 parts)
│   ├── WINDOWS_SETUP.md           # Windows-specific guide
│   ├── ARCHITECTURE.md            # System architecture
│   ├── PROJECT_SUMMARY.md         # Project summary
│   └── INDEX.md                   # This file
│
├── 🐍 Python Source Code
│   ├── main.py                    # Entry point
│   ├── core/                      # Backend modules
│   │   ├── __init__.py
│   │   ├── ai.py                  # AI engine
│   │   ├── camera.py              # Camera handler
│   │   ├── database.py            # Database handler
│   │   └── hardware.py            # Hardware controller
│   └── ui/                        # Frontend modules
│       ├── __init__.py
│       ├── main_window.py         # Main window
│       └── history_window.py      # History window
│
├── 🔧 Arduino Firmware
│   └── arduino/
│       └── sorting_control.ino    # Arduino code
│
├── 🤖 AI Model
│   └── model/
│       └── best_ncnn_model/
│           ├── model.ncnn.param   # Model structure
│           ├── model.ncnn.bin     # Model weights
│           ├── metadata.yaml      # Metadata
│           └── model_ncnn.py      # Python wrapper
│
├── 📦 Configuration & Dependencies
│   ├── requirements.txt           # Python packages
│   ├── .gitignore                 # Git ignore rules
│   └── run.sh                     # Startup script (Linux)
│
├── 💾 Data Directories (Auto-created)
│   ├── captures/                  # Saved images
│   │   ├── ok/                    # Pass images
│   │   └── ng/                    # Reject images
│   └── database/                  # SQLite database
│       └── product.db             # (Auto-created)
│
└── 📊 Model Files (Pre-existing)
    └── model/best_ncnn_model/     # AI model files
```

---

## 📋 File Categories

### 1. Essential Files (Must Have)

```
✅ main.py                          # Entry point
✅ core/*.py                        # Backend modules (4 files)
✅ ui/*.py                          # UI modules (2 files)
✅ arduino/sorting_control.ino     # Arduino firmware
✅ model/best_ncnn_model/*         # AI model (4 files)
✅ requirements.txt                 # Dependencies
```

### 2. Documentation Files (Highly Recommended)

```
📖 README.md                        # Main docs
📖 QUICK_START.md                   # Quick guide
📖 SETUP_GUIDE.md                   # Detailed setup
📖 PROJECT_SUMMARY.md               # Summary
📖 ARCHITECTURE.md                  # Architecture
📖 WINDOWS_SETUP.md                 # Windows guide
```

### 3. Configuration Files

```
⚙️ requirements.txt                 # Python dependencies
⚙️ .gitignore                       # Git ignore rules
⚙️ run.sh                           # Startup script
```

### 4. Auto-Generated (Runtime)

```
🗂️ database/product.db              # SQLite database
🖼️ captures/ok/*.jpg                # OK product images
🖼️ captures/ng/*.jpg                # NG product images
```

---

## 🎯 Quick Navigation

### "I want to..."

| Goal | File to Read |
|------|--------------|
| **Understand the project** | `README.md` |
| **Install and run quickly** | `QUICK_START.md` |
| **Set up from scratch** | `SETUP_GUIDE.md` |
| **Run on Windows** | `WINDOWS_SETUP.md` |
| **Understand architecture** | `ARCHITECTURE.md` |
| **See project scope** | `PROJECT_SUMMARY.md` |
| **Modify AI logic** | `core/ai.py` |
| **Change UI** | `ui/main_window.py` |
| **Adjust Arduino behavior** | `arduino/sorting_control.ino` |
| **Configure system** | `main.py` (config dict) |
| **Add database features** | `core/database.py` |
| **Debug camera issues** | `core/camera.py` |
| **Fix serial communication** | `core/hardware.py` |

---

## 📊 File Statistics

### Code Files

| Language | Files | Lines | Purpose |
|----------|-------|-------|---------|
| Python | 8 | ~2,500 | Main application |
| Arduino C++ | 1 | ~200 | Motor control |
| Markdown | 7 | ~3,000 | Documentation |
| **Total** | **16** | **~5,700** | **Complete system** |

### Documentation Coverage

- **Setup Guides**: 3 files (QUICK_START, SETUP_GUIDE, WINDOWS_SETUP)
- **Technical Docs**: 2 files (ARCHITECTURE, PROJECT_SUMMARY)
- **Main Docs**: 1 file (README)
- **Navigation**: 1 file (INDEX - this file)
- **Total**: 7 comprehensive documentation files

---

## 🔍 Code Organization

### By Functionality

```
┌─────────────────────────────────────────────────────────┐
│                    FUNCTIONALITY MAP                    │
└─────────────────────────────────────────────────────────┘

Hardware Control:
├── arduino/sorting_control.ino    # Relay, servo, sensor
└── core/hardware.py               # Serial communication

Computer Vision:
├── core/camera.py                 # Image capture
└── core/ai.py                     # Object detection

Data Management:
└── core/database.py               # SQLite operations

User Interface:
├── ui/main_window.py              # Main control panel
└── ui/history_window.py           # History viewer

Application:
└── main.py                        # Initialization & coordination
```

### By Layer

```
┌─────────────────────────────────────────────────────────┐
│                      LAYER MODEL                        │
└─────────────────────────────────────────────────────────┘

Layer 4: Presentation (UI)
├── ui/main_window.py
└── ui/history_window.py

Layer 3: Business Logic
├── core/ai.py                     # Sorting logic
└── main.py                        # Coordination

Layer 2: Data Access
├── core/database.py               # Persistence
└── core/camera.py                 # Input

Layer 1: Hardware Abstraction
├── core/hardware.py               # Serial I/O
└── arduino/sorting_control.ino    # Physical control
```

---

## 📚 Documentation Reading Order

### For First-Time Users

1. **README.md** - Get overview
2. **QUICK_START.md** - Try running it
3. **SETUP_GUIDE.md** - Full installation (if needed)
4. **PROJECT_SUMMARY.md** - Understand scope

### For Developers

1. **ARCHITECTURE.md** - Understand design
2. **main.py** - See initialization
3. **core/*.py** - Study modules
4. **ui/*.py** - Understand UI
5. **arduino/sorting_control.ino** - Hardware control

### For Evaluators/Reviewers

1. **PROJECT_SUMMARY.md** - Complete overview
2. **ARCHITECTURE.md** - Technical depth
3. **README.md** - Feature list
4. **Code files** - Implementation quality

### For Windows Users

1. **WINDOWS_SETUP.md** - Windows-specific setup
2. **QUICK_START.md** - Running guide
3. **README.md** - General documentation

---

## 🔧 Configuration Files

### Main Configuration

**File**: `main.py`

```python
config = {
    'camera_id': 0,
    'arduino_port': '/dev/ttyUSB0',
    'model_path': 'model/best_ncnn_model',
    'use_dummy_camera': False,
    'use_dummy_hardware': False
}
```

### Dependencies

**File**: `requirements.txt`

```
opencv-python>=4.8.0
Pillow>=10.0.0
pyserial>=3.5
numpy>=1.24.0
```

### Git Ignore

**File**: `.gitignore`

```
__pycache__/
*.pyc
venv/
*.db-journal
```

---

## 🎓 Learning Path

### Beginner Level

1. Read `README.md`
2. Run with dummy modes (no hardware)
3. Explore UI features
4. View code comments

### Intermediate Level

1. Study `ARCHITECTURE.md`
2. Understand threading model
3. Modify AI threshold
4. Customize UI

### Advanced Level

1. Implement new AI models
2. Add new sensors
3. Optimize performance
4. Extend database schema

---

## 🐛 Debugging Guide

### Issue: System won't start

**Check**:
1. `requirements.txt` - Dependencies installed?
2. `main.py` - Configuration correct?
3. Terminal output - Error messages?

### Issue: Camera not working

**Check**:
1. `core/camera.py` - Camera initialization
2. `main.py` - Camera ID correct?
3. Try dummy mode: `'use_dummy_camera': True`

### Issue: Arduino not responding

**Check**:
1. `arduino/sorting_control.ino` - Code uploaded?
2. `core/hardware.py` - Port correct?
3. Device Manager (Windows) or `ls /dev/tty*` (Linux)

### Issue: AI not detecting

**Check**:
1. `core/ai.py` - Model loaded?
2. `model/best_ncnn_model/` - Files present?
3. NCNN installed? (Falls back to dummy mode)

---

## 📞 Support Resources

### Documentation

- **README.md**: General help
- **SETUP_GUIDE.md**: Installation issues
- **WINDOWS_SETUP.md**: Windows problems
- **ARCHITECTURE.md**: Understanding design

### Code Comments

All Python files have extensive inline comments:
- Function docstrings
- Logic explanations
- Parameter descriptions

### Arduino Serial Monitor

- Open in Arduino IDE
- Set to 9600 baud
- Watch for debug messages

---

## ✅ Project Checklist

### Before Running

- [ ] All files present (see Essential Files above)
- [ ] Python dependencies installed
- [ ] Arduino code uploaded
- [ ] Hardware connected and wired
- [ ] Configuration updated in `main.py`

### For Development

- [ ] Virtual environment created
- [ ] Git repository initialized
- [ ] Dummy modes tested
- [ ] Code documented
- [ ] Changes committed

### For Deployment

- [ ] Raspberry Pi OS updated
- [ ] All dependencies installed
- [ ] Hardware calibrated
- [ ] System tested end-to-end
- [ ] Documentation reviewed

---

## 📈 Version Information

| Aspect | Details |
|--------|---------|
| **Version** | 1.0.0 |
| **Date** | December 2025 |
| **Status** | Production Ready ✅ |
| **Python** | 3.7+ |
| **Platform** | Raspberry Pi 5 (primary), Windows (dev) |
| **License** | Educational Use |

---

## 🎯 Key Files Summary

### Top 5 Most Important Files

1. **main.py** - Application entry point
2. **core/ai.py** - AI inference and sorting logic
3. **arduino/sorting_control.ino** - Hardware control
4. **ui/main_window.py** - User interface
5. **README.md** - Documentation

### Top 3 Documentation Files

1. **README.md** - Complete project guide
2. **SETUP_GUIDE.md** - Installation instructions
3. **ARCHITECTURE.md** - System design

---

## 🔗 File Dependencies

```
main.py
├── imports core.ai
├── imports core.camera
├── imports core.hardware
├── imports core.database
└── imports ui.main_window
    └── imports ui.history_window

core/ai.py
├── requires model/best_ncnn_model/*
└── uses opencv, ncnn

core/camera.py
└── uses opencv, threading

core/database.py
└── uses sqlite3

core/hardware.py
└── uses pyserial

ui/main_window.py
├── uses tkinter, PIL
└── requires all core modules

arduino/sorting_control.ino
└── uses Servo library
```

---

## 📝 Notes

### File Naming Conventions

- **UPPERCASE.md**: Documentation files
- **lowercase.py**: Python source files
- **lowercase.ino**: Arduino source files
- **lowercase/**: Directories

### Code Style

- **Python**: PEP 8 compliant
- **Arduino**: Arduino style guide
- **Documentation**: Markdown with emojis

### Comments

- All functions have docstrings
- Complex logic is explained
- TODO items marked clearly

---

## 🎉 Conclusion

This project contains **16 source files** and **7 documentation files**, totaling approximately **5,700 lines** of code and documentation.

Everything you need is organized and documented. Use this index to navigate the project efficiently!

---

**Quick Links**:
- 🚀 [Quick Start](QUICK_START.md)
- 📖 [Main Documentation](README.md)
- 🔧 [Setup Guide](SETUP_GUIDE.md)
- 🏗️ [Architecture](ARCHITECTURE.md)
- 📋 [Project Summary](PROJECT_SUMMARY.md)

**Happy Coding! 🥤🤖**

