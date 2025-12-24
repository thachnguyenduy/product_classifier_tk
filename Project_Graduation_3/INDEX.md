# 📚 Project Index - Continuous Coca-Cola Sorting System

Quick navigation guide to all project files and documentation.

---

## 🚀 Getting Started (Read These First)

| File | Description | Priority |
|------|-------------|----------|
| **README.md** | Complete system documentation | ⭐⭐⭐ |
| **QUICK_START.md** | 5-minute setup guide | ⭐⭐⭐ |
| **CALIBRATION_GUIDE.md** | Detailed calibration instructions | ⭐⭐ |
| **PROJECT_SUMMARY.md** | Technical overview | ⭐ |

---

## 💻 Source Code

### Main Entry Point
| File | Lines | Description |
|------|-------|-------------|
| `main.py` | 215 | Application entry point, component initialization |
| `config.py` | 82 | Configuration parameters (EDIT THIS!) |

### Core Modules (`core/`)
| File | Lines | Description |
|------|-------|-------------|
| `ai.py` | 450+ | NCNN AI engine with NMS |
| `camera.py` | 275 | Threaded camera capture |
| `hardware.py` | 318 | Serial communication with Arduino |
| `database.py` | 360 | SQLite database handler |
| `__init__.py` | 5 | Module initialization |

### User Interface (`ui/`)
| File | Lines | Description |
|------|-------|-------------|
| `main_window.py` | 520+ | Main GUI (Control First strategy) |
| `history_window.py` | 180 | Inspection history viewer |
| `__init__.py` | 5 | Module initialization |

### Arduino Code (`arduino/`)
| File | Lines | Description |
|------|-------|-------------|
| `sorting_control.ino` | 152 | Circular buffer logic, conveyor control |

---

## 📖 Documentation

### User Guides
| File | Purpose | When to Read |
|------|---------|--------------|
| **README.md** | Main documentation | Before starting |
| **QUICK_START.md** | Fast setup | First time setup |
| **CALIBRATION_GUIDE.md** | Fine-tuning | After initial setup |
| **PROJECT_SUMMARY.md** | Technical details | For understanding internals |
| **INDEX.md** | This file | For navigation |

### Legacy Documentation (From Previous Versions)
| File | Purpose | Status |
|------|---------|--------|
| `ARCHITECTURE.md` | Old architecture docs | Outdated (stop-and-go mode) |
| `FIX_GUIDE.md` | Old troubleshooting | Partially relevant |
| `SETUP_GUIDE.md` | Old setup guide | Outdated |
| `WINDOWS_SETUP.md` | Windows instructions | Partially relevant |
| `UPDATE_NOTES.md` | Change history | Reference only |

---

## 🔧 Configuration Files

| File | Purpose | Edit? |
|------|---------|-------|
| `config.py` | System parameters | ✅ YES - Edit for your setup |
| `requirements.txt` | Python dependencies | ❌ NO - Use as-is |
| `.gitignore` | Git ignore rules | ❌ NO - Use as-is |
| `run.sh` | Startup script (Linux) | ❌ NO - Use as-is |

---

## 🗂️ Data & Assets

### Model Files (`model/best_ncnn_model/`)
| File | Size | Description |
|------|------|-------------|
| `model.ncnn.param` | ~1KB | Model structure |
| `model.ncnn.bin` | ~7MB | Model weights |
| `metadata.yaml` | ~1KB | Model metadata |
| `model_ncnn.py` | ~10KB | Python wrapper |

### Database (`database/`)
| File | Description |
|------|-------------|
| `product.db` | SQLite database (auto-created) |

### Captures (`captures/`)
| Directory | Contents |
|-----------|----------|
| `ok/` | Images of passed bottles |
| `ng/` | Images of rejected bottles |
| `debug/` | Debug images (if enabled) |

---

## 🧪 Testing & Development

### Test Scripts
| File | Purpose | When to Use |
|------|---------|-------------|
| `test model.py` | NCNN model testing | Test AI without hardware |
| `test_model_live.py` | Live NCNN testing | Test with camera |
| `test_model_yolo.py` | YOLOv8 testing | If using YOLO model |
| `test_model_debug.py` | Debug NCNN output | Troubleshoot AI issues |

### Test Guides
| File | Purpose |
|------|---------|
| `TEST_MODEL_GUIDE.md` | How to test models |

---

## 📋 Quick Reference

### What to Edit for Your Setup

1. **CRITICAL - Must Edit**:
   ```python
   # config.py
   TRAVEL_TIME_MS = 4500        # Measure physically!
   ARDUINO_PORT = '/dev/ttyUSB0' # Your Arduino port
   CAMERA_ID = 0                # Your camera ID
   ```

2. **Likely Need to Edit**:
   ```python
   # config.py
   CAMERA_EXPOSURE = -4         # Adjust for lighting
   CONFIDENCE_THRESHOLD = 0.5   # Tune for accuracy
   ```

3. **Arduino - Must Match Python**:
   ```cpp
   // sorting_control.ino (line 28)
   unsigned long TRAVEL_TIME = 4500;  // Match config.py!
   ```

### Common File Locations

| What | Where |
|------|-------|
| Main program | `main.py` |
| Configuration | `config.py` |
| Arduino code | `arduino/sorting_control.ino` |
| AI model | `model/best_ncnn_model/` |
| Captured images | `captures/ok/` and `captures/ng/` |
| Database | `database/product.db` |
| Logs | Terminal output (or `system.log` if enabled) |

---

## 🎯 Workflow Guides

### First Time Setup
```
1. Read: QUICK_START.md
2. Edit: config.py (TRAVEL_TIME, ports)
3. Edit: arduino/sorting_control.ino (TRAVEL_TIME)
4. Upload: Arduino code
5. Run: python3 main.py
6. Follow: CALIBRATION_GUIDE.md
```

### Daily Operation
```
1. Check: Camera, lighting, sensors
2. Run: python3 main.py
3. Click: "START SYSTEM"
4. Monitor: Statistics and results
5. Click: "STOP SYSTEM" when done
```

### Troubleshooting
```
1. Enable: DEBUG_MODE in config.py
2. Check: Terminal output
3. Check: Arduino Serial Monitor
4. Review: CALIBRATION_GUIDE.md
5. Check: captures/debug/ folder
```

### Maintenance
```
Daily:
- Check camera focus
- Verify lighting
- Test with known samples

Weekly:
- Recalibrate TRAVEL_TIME
- Clean sensors
- Review statistics

Monthly:
- Deep clean hardware
- Analyze defect trends
- Update model if needed
```

---

## 🔍 Finding Specific Information

### "How do I..."

| Task | File to Read | Section |
|------|--------------|---------|
| Install the system | QUICK_START.md | Installation |
| Calibrate travel time | CALIBRATION_GUIDE.md | Travel Time Calibration |
| Adjust camera exposure | CALIBRATION_GUIDE.md | Camera Exposure |
| Tune AI confidence | CALIBRATION_GUIDE.md | AI Confidence |
| Fix overlapping boxes | config.py | NMS_THRESHOLD |
| Change Arduino port | config.py | ARDUINO_PORT |
| View inspection history | UI | "VIEW HISTORY" button |
| Understand the workflow | README.md | How It Works |
| Troubleshoot issues | CALIBRATION_GUIDE.md | Troubleshooting |

### "What does this do..."

| Component | File | Description |
|-----------|------|-------------|
| Circular buffer | arduino/sorting_control.ino | Lines 40-60 |
| NMS algorithm | core/ai.py | `_apply_nms()` method |
| Control First strategy | ui/main_window.py | `_process_bottle()` method |
| Camera threading | core/camera.py | `_capture_loop()` method |
| Serial communication | core/hardware.py | `_listen_loop()` method |
| Sorting logic | core/ai.py | `_apply_sorting_logic()` method |

---

## 📊 Project Statistics

### Code Metrics
- **Total Files**: 45+
- **Source Code**: ~2,500 lines
  - Python: ~2,200 lines (88%)
  - C++ (Arduino): ~150 lines (6%)
  - Config: ~150 lines (6%)
- **Documentation**: ~1,500 lines
- **Languages**: Python, C++, Markdown

### File Breakdown
| Category | Files | Lines |
|----------|-------|-------|
| Core Logic | 5 | ~1,400 |
| UI | 2 | ~700 |
| Arduino | 1 | ~150 |
| Config | 1 | ~80 |
| Main | 1 | ~215 |
| Documentation | 8+ | ~1,500 |
| Tests | 4 | ~500 |

---

## 🎓 Learning Path

### For Students/Beginners

**Week 1**: Understanding
1. Read README.md
2. Read PROJECT_SUMMARY.md
3. Study workflow diagram
4. Review Arduino code

**Week 2**: Setup
1. Follow QUICK_START.md
2. Install dependencies
3. Upload Arduino code
4. Test with dummy mode

**Week 3**: Calibration
1. Follow CALIBRATION_GUIDE.md
2. Measure travel time
3. Adjust camera exposure
4. Tune AI confidence

**Week 4**: Operation
1. Run with real hardware
2. Test with known samples
3. Monitor statistics
4. Optimize performance

### For Developers

**Phase 1**: Code Review
- Study `core/ai.py` (AI logic)
- Study `arduino/sorting_control.ino` (circular buffer)
- Study `ui/main_window.py` (Control First strategy)

**Phase 2**: Customization
- Modify sorting logic
- Add new features
- Optimize performance
- Extend UI

**Phase 3**: Advanced
- Integrate new sensors
- Add network features
- Implement analytics
- Deploy to production

---

## 🆘 Quick Help

### System Won't Start
→ Check `QUICK_START.md` → Troubleshooting section

### Wrong Bottles Rejected
→ Check `CALIBRATION_GUIDE.md` → Travel Time section

### Poor Detection Accuracy
→ Check `CALIBRATION_GUIDE.md` → AI Confidence section

### Motion Blur in Images
→ Check `CALIBRATION_GUIDE.md` → Camera Exposure section

### Need Technical Details
→ Check `PROJECT_SUMMARY.md` → Technical Highlights

---

## 📞 Support Resources

1. **Documentation**: Read guides in order (README → QUICK_START → CALIBRATION)
2. **Debug Mode**: Enable in `config.py` for detailed logs
3. **Arduino Monitor**: Open Serial Monitor (9600 baud) for hardware status
4. **Test Scripts**: Use test files to isolate issues
5. **Debug Images**: Check `captures/debug/` folder

---

## 🗺️ Project Roadmap

### Current Version: 2.0.0 (Continuous Mode)
✅ Circular buffer queue  
✅ Control First strategy  
✅ NCNN with NMS  
✅ Manual exposure control  
✅ Complete documentation  

### Future Enhancements
- [ ] Multi-camera support
- [ ] Web dashboard
- [ ] Cloud integration
- [ ] Advanced analytics
- [ ] Automatic calibration

---

**Last Updated**: December 2025  
**Project Status**: ✅ Complete and Production-Ready

**Quick Links**:
- [Main Documentation](README.md)
- [Quick Start](QUICK_START.md)
- [Calibration Guide](CALIBRATION_GUIDE.md)
- [Project Summary](PROJECT_SUMMARY.md)
