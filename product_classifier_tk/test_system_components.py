#!/usr/bin/env python3
"""
Test script for individual system components.
Run this to verify each component works before running full system.
"""

import sys
import time
from pathlib import Path


def test_imports():
    """Test if all required packages are installed."""
    print("\n" + "="*80)
    print("TEST 1: Checking Python Dependencies")
    print("="*80)
    
    required = {
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'serial': 'pyserial',
        'ultralytics': 'ultralytics',
        'PIL': 'Pillow'
    }
    
    all_ok = True
    for module_name, package_name in required.items():
        try:
            __import__(module_name)
            print(f"✅ {package_name:20s} - OK")
        except ImportError:
            print(f"❌ {package_name:20s} - MISSING")
            print(f"   Install: pip3 install {package_name}")
            all_ok = False
    
    if all_ok:
        print("\n✅ All dependencies installed!")
    else:
        print("\n❌ Some dependencies missing. Install them first.")
        sys.exit(1)


def test_camera():
    """Test USB camera."""
    print("\n" + "="*80)
    print("TEST 2: Camera Detection")
    print("="*80)
    
    import cv2
    
    # Try camera indices 0-3
    for idx in range(4):
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                h, w = frame.shape[:2]
                print(f"✅ Camera {idx} found: {w}x{h}")
                
                # Show frame for 2 seconds
                print(f"   Displaying frame for 2 seconds...")
                cv2.imshow(f"Camera {idx} Test", frame)
                cv2.waitKey(2000)
                cv2.destroyAllWindows()
                
                cap.release()
                return True
            cap.release()
    
    print("❌ No working camera found!")
    return False


def test_serial():
    """Test Arduino serial connection."""
    print("\n" + "="*80)
    print("TEST 3: Arduino Serial Connection")
    print("="*80)
    
    import serial
    import serial.tools.list_ports
    
    # List available ports
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("❌ No serial ports found!")
        print("   Make sure Arduino is connected via USB.")
        return False
    
    print(f"Found {len(ports)} serial port(s):")
    for port in ports:
        print(f"   - {port.device}: {port.description}")
    
    # Try to connect to first Arduino-like port
    arduino_port = None
    for port in ports:
        if 'Arduino' in port.description or 'ACM' in port.device or 'USB' in port.device:
            arduino_port = port.device
            break
    
    if not arduino_port:
        # Try first port
        arduino_port = ports[0].device
    
    print(f"\n🔌 Attempting to connect to {arduino_port}...")
    
    try:
        ser = serial.Serial(arduino_port, 115200, timeout=1)
        time.sleep(2.5)  # Wait for Arduino reset
        
        # Read startup message
        print("📨 Reading Arduino startup message...")
        for _ in range(10):
            if ser.in_waiting > 0:
                line = ser.readline().decode().strip()
                print(f"   Arduino: {line}")
        
        # Send PING
        print("\n📤 Sending PING command...")
        ser.write(b"PING\n")
        time.sleep(0.5)
        
        # Read response
        if ser.in_waiting > 0:
            response = ser.readline().decode().strip()
            print(f"   Arduino: {response}")
            if response == "PONG":
                print("\n✅ Arduino connection OK!")
                ser.close()
                return True
        
        print("⚠️  No response from Arduino (but connection established)")
        print("   Make sure Arduino firmware is uploaded!")
        ser.close()
        return False
        
    except Exception as e:
        print(f"❌ Serial connection failed: {e}")
        return False


def test_model():
    """Test YOLOv8 model loading."""
    print("\n" + "="*80)
    print("TEST 4: YOLOv8 Model Loading")
    print("="*80)
    
    from ultralytics import YOLO
    import numpy as np
    
    model_path = Path("model/my_model.pt")
    
    if not model_path.exists():
        print(f"❌ Model file not found: {model_path}")
        print("   Make sure your trained YOLOv8 model is in model/ directory")
        return False
    
    print(f"📂 Found model: {model_path}")
    print(f"🧠 Loading model...")
    
    try:
        model = YOLO(str(model_path))
        print(f"✅ Model loaded successfully!")
        
        # Get model info
        print(f"\n📊 Model Information:")
        print(f"   Classes: {list(model.names.values())}")
        
        # Test inference with dummy image
        print(f"\n🧪 Testing inference with dummy image...")
        dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
        results = model(dummy_image, verbose=False)
        print(f"✅ Inference test passed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return False


def test_all():
    """Run all tests."""
    print("\n" + "="*80)
    print("🧪 SYSTEM COMPONENT TEST SUITE")
    print("="*80)
    print("This script will test each component individually.")
    print("Make sure Arduino is connected and camera is plugged in.")
    input("\nPress Enter to start tests...")
    
    results = {
        'imports': test_imports(),
        'camera': test_camera(),
        'serial': test_serial(),
        'model': test_model()
    }
    
    # Summary
    print("\n" + "="*80)
    print("📋 TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.upper():20s}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*80)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ System is ready to run.")
        print("\nNext step:")
        print("   python3 main_continuous_flow.py")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("❌ Fix the issues above before running the system.")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_all()

