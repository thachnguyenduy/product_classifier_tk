# 🪟 Windows Setup Guide

Special instructions for running the Coca-Cola Sorting System on Windows (for development/testing).

## ⚠️ Important Note

This project is **designed for Raspberry Pi 5 (Linux)**. However, you can develop and test on Windows with some modifications.

---

## 💻 Windows Prerequisites

### 1. Install Python 3.7+

Download from: https://www.python.org/downloads/

**Important**: Check "Add Python to PATH" during installation!

### 2. Install Arduino IDE

Download from: https://www.arduino.cc/en/software

### 3. Install Git (Optional)

Download from: https://git-scm.com/download/win

---

## 📦 Installation on Windows

### Step 1: Open PowerShell or Command Prompt

```powershell
# Navigate to project
cd "E:\FINAL PROJECT 222\Project_Graduation"
```

### Step 2: Create Virtual Environment (Recommended)

```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate

# Your prompt should now show (venv)
```

### Step 3: Install Dependencies

```powershell
pip install opencv-python pillow pyserial numpy
```

### Step 4: Test Installation

```powershell
python -c "import cv2, serial, PIL; print('Success!')"
```

---

## 🔌 Arduino on Windows

### Find COM Port

1. Connect Arduino via USB
2. Open **Device Manager** (Win+X → Device Manager)
3. Expand **Ports (COM & LPT)**
4. Look for "Arduino Uno (COMx)" - note the COM number

### Upload Arduino Code

1. Open Arduino IDE
2. Open `arduino/sorting_control.ino`
3. Select **Tools → Board → Arduino Uno**
4. Select **Tools → Port → COM3** (or your COM port)
5. Click **Upload** (→ button)

### Configure COM Port in Python

Edit `main.py`:

```python
'arduino_port': 'COM3',  # Change to your COM port
```

---

## 📷 Camera on Windows

### USB Camera

Most USB webcams work with OpenCV:

```python
'camera_id': 0,  # First camera (usually built-in webcam)
'camera_id': 1,  # Second camera (external USB camera)
```

### Test Camera

```powershell
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera FAIL')"
```

---

## 🚀 Running on Windows

### Method 1: Direct Run

```powershell
python main.py
```

### Method 2: Create Batch File

Create `run.bat`:

```batch
@echo off
echo ========================================
echo Coca-Cola Sorting System
echo ========================================
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\Activate.bat (
    call venv\Scripts\Activate.bat
)

REM Run application
python main.py

pause
```

Double-click `run.bat` to start.

---

## 🧪 Testing Without Hardware (Windows)

Edit `main.py`:

```python
config = {
    'camera_id': 0,
    'arduino_port': 'COM3',
    'use_dummy_camera': True,     # Enable for testing without camera
    'use_dummy_hardware': True    # Enable for testing without Arduino
}
```

This runs the full UI with simulated hardware.

---

## 🐛 Windows-Specific Issues

### Issue 1: "Python not found"

**Solution**:
1. Reinstall Python with "Add to PATH" checked
2. Or manually add to PATH:
   - Win+X → System → Advanced → Environment Variables
   - Add `C:\Python3X` and `C:\Python3X\Scripts`
   - Restart PowerShell

### Issue 2: "pip not found"

**Solution**:
```powershell
python -m ensurepip --upgrade
```

### Issue 3: Camera Opens Wrong Device

**Solution**:
```python
# Try different indices
'camera_id': 0,  # Built-in webcam
'camera_id': 1,  # External camera
'camera_id': 2,  # Another camera
```

### Issue 4: "Access Denied" on COM Port

**Solutions**:
1. Close Arduino IDE Serial Monitor
2. Unplug and replug Arduino
3. Try different USB port
4. Check Device Manager for driver issues

### Issue 5: cv2.imshow() Crashes

**Solution**:
```powershell
# Reinstall opencv-python
pip uninstall opencv-python
pip install opencv-python==4.8.0.74
```

### Issue 6: Tkinter Not Found

**Solution**:
- Tkinter is usually included with Python
- If missing, reinstall Python from python.org
- Make sure to select "tcl/tk and IDLE" during installation

### Issue 7: pyserial Error

**Solution**:
```powershell
# Uninstall conflicting packages
pip uninstall serial pyserial
# Reinstall
pip install pyserial
```

---

## 📁 Windows File Paths

### Use Forward Slashes

```python
# Good (cross-platform)
'model_path': 'model/best_ncnn_model'

# Also works
'model_path': 'model\\best_ncnn_model'  # Escaped backslash
```

### Absolute Paths

```python
'camera_id': r'E:\videos\test.mp4',  # r'' for raw string
```

---

## 🔒 Windows Security

### Antivirus Warning

Some antivirus software may flag Python scripts:
- Add project folder to exclusions
- Or click "Allow" when prompted

### Firewall

No network access needed, but if using remote camera:
- Allow Python through Windows Firewall

---

## 🎯 Development Workflow on Windows

### Recommended Setup

1. **Code on Windows** using VS Code or PyCharm
2. **Test with Dummy Modes** (no hardware needed)
3. **Deploy to Raspberry Pi** when ready:
   ```powershell
   # Use SCP or WinSCP to transfer files
   scp -r * pi@raspberrypi.local:/home/pi/Project_Graduation/
   ```

### VS Code Extensions

- Python
- Pylance
- Arduino (for .ino files)

---

## 📊 Performance on Windows

### Expected vs Raspberry Pi

| Aspect | Windows PC | Raspberry Pi 5 |
|--------|-----------|----------------|
| AI Inference | Much faster | ~100-300ms |
| Camera FPS | 30+ FPS | 30 FPS |
| UI Responsiveness | Excellent | Good |
| Real Hardware | Limited | Full support |

---

## 🔄 Transferring to Raspberry Pi

### Using WinSCP (GUI)

1. Install WinSCP: https://winscp.net/
2. Connect to Pi: `raspberrypi.local` / `pi` / password
3. Drag and drop project folder

### Using Command Line

```powershell
# Install OpenSSH (Windows 10+)
# Transfer project
scp -r "E:\FINAL PROJECT 222\Project_Graduation" pi@raspberrypi.local:/home/pi/
```

### Using Git

```powershell
# On Windows
cd "E:\FINAL PROJECT 222\Project_Graduation"
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-repo-url>
git push

# On Raspberry Pi
git clone <your-repo-url> Project_Graduation
```

---

## 🎨 Windows UI Considerations

### Tkinter Scaling

If UI looks too small/large:

```python
# Add to main.py before creating window
import tkinter as tk
root = tk.Tk()
root.tk.call('tk', 'scaling', 2.0)  # Adjust scaling factor
```

### Font Rendering

Windows renders fonts differently:
- Adjust font sizes in `ui/main_window.py` if needed
- Test on target system (Raspberry Pi)

---

## 💡 Tips for Windows Development

### 1. Use Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate
```

Benefits:
- Isolated dependencies
- Easy cleanup
- Version control

### 2. Use Dummy Modes

Always test with dummy modes first:
- Faster iteration
- No hardware needed
- Safe development

### 3. Keep Arduino Connected

Test serial communication regularly:
```powershell
python -c "import serial; s=serial.Serial('COM3',9600); print('OK'); s.close()"
```

### 4. Version Control

```powershell
git init
git add .
git commit -m "Development checkpoint"
```

---

## 🔧 Debugging on Windows

### Enable Debug Logging

Add to `main.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Components Individually

```powershell
# Test camera
python -c "from core.camera import Camera; c=Camera(0); c.start(); print('OK')"

# Test AI
python -c "from core.ai import AIEngine; ai=AIEngine(); print('OK')"

# Test serial
python -c "from core.hardware import HardwareController; hw=HardwareController('COM3'); hw.connect()"
```

### Arduino Serial Monitor

- Open in Arduino IDE: **Tools → Serial Monitor**
- Set to **9600 baud**
- Watch for detection messages

---

## 📋 Pre-Deployment Checklist (Windows → Pi)

- [ ] Code tested with dummy modes
- [ ] Arduino code uploaded and verified
- [ ] Serial communication working
- [ ] Camera tested
- [ ] Dependencies documented in requirements.txt
- [ ] File paths are relative (not absolute Windows paths)
- [ ] No Windows-specific code (e.g., `os.system('cls')`)
- [ ] Git repository up to date

---

## 🎓 Learning Resources

### Python on Windows
- https://docs.python.org/3/using/windows.html

### Serial Communication
- https://pyserial.readthedocs.io/

### OpenCV
- https://docs.opencv.org/4.x/

---

## ✅ Quick Test Script for Windows

Save as `test_windows.py`:

```python
#!/usr/bin/env python3
import sys

def test_imports():
    """Test if all required packages are installed"""
    try:
        import cv2
        print("✓ OpenCV installed")
    except:
        print("✗ OpenCV missing - run: pip install opencv-python")
        return False
    
    try:
        import serial
        print("✓ PySerial installed")
    except:
        print("✗ PySerial missing - run: pip install pyserial")
        return False
    
    try:
        import PIL
        print("✓ Pillow installed")
    except:
        print("✗ Pillow missing - run: pip install pillow")
        return False
    
    try:
        import tkinter
        print("✓ Tkinter available")
    except:
        print("✗ Tkinter missing - reinstall Python with tcl/tk")
        return False
    
    return True

def test_camera():
    """Test if camera is accessible"""
    import cv2
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        print("✓ Camera accessible")
        cap.release()
        return True
    else:
        print("✗ Camera not found - check connection")
        return False

def test_arduino(com_port='COM3'):
    """Test Arduino connection"""
    import serial
    try:
        ser = serial.Serial(com_port, 9600, timeout=2)
        print(f"✓ Arduino connected on {com_port}")
        ser.close()
        return True
    except:
        print(f"✗ Arduino not found on {com_port}")
        print(f"  Check Device Manager for correct COM port")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Windows Environment Test")
    print("=" * 50)
    print()
    
    print("1. Testing Python packages...")
    imports_ok = test_imports()
    print()
    
    print("2. Testing camera...")
    camera_ok = test_camera()
    print()
    
    print("3. Testing Arduino (COM3)...")
    arduino_ok = test_arduino('COM3')
    print()
    
    print("=" * 50)
    if imports_ok and camera_ok and arduino_ok:
        print("✓ All tests passed! Ready to run.")
    elif imports_ok:
        print("⚠ Some hardware not available.")
        print("  Enable dummy modes in main.py to test UI.")
    else:
        print("✗ Installation incomplete. Install missing packages.")
    print("=" * 50)
```

Run it:
```powershell
python test_windows.py
```

---

## 🎯 Summary

**Development on Windows**:
- ✅ Full UI testing with dummy modes
- ✅ Arduino code upload and testing
- ✅ Python development and debugging
- ⚠️ Real hardware (relay, servo) needs Pi

**Best Workflow**:
1. Develop on Windows (fast iteration)
2. Test with dummy modes
3. Verify Arduino communication
4. Deploy to Raspberry Pi for final testing

---

**For production deployment, always use Raspberry Pi!**

For further help, see:
- `SETUP_GUIDE.md` - Raspberry Pi setup
- `QUICK_START.md` - Quick start guide
- `README.md` - Full documentation

