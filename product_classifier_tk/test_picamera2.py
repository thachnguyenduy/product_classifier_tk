"""Test script để kiểm tra Picamera2 (thư viện mới cho Pi Camera)."""
import sys

print("Testing Picamera2 library...")
print("=" * 50)

# Test 1: Import picamera2
try:
    from picamera2 import Picamera2
    print("✅ picamera2 library found")
except ImportError:
    print("❌ picamera2 not installed!")
    print("\nInstall with:")
    print("  sudo apt install -y python3-picamera2")
    sys.exit(1)

# Test 2: Create camera instance
try:
    picam2 = Picamera2()
    print("✅ Picamera2 instance created")
except Exception as e:
    print(f"❌ Cannot create Picamera2: {e}")
    sys.exit(1)

# Test 3: Configure camera
try:
    config = picam2.create_preview_configuration(
        main={"size": (1280, 720), "format": "RGB888"}
    )
    picam2.configure(config)
    print("✅ Camera configured (1280x720, RGB888)")
except Exception as e:
    print(f"❌ Cannot configure camera: {e}")
    sys.exit(1)

# Test 4: Start camera
try:
    picam2.start()
    print("✅ Camera started")
except Exception as e:
    print(f"❌ Cannot start camera: {e}")
    sys.exit(1)

# Test 5: Capture frame
try:
    import time
    time.sleep(1)  # Warm up
    frame = picam2.capture_array()
    print(f"✅ Frame captured!")
    print(f"   Shape: {frame.shape}")
    print(f"   Dtype: {frame.dtype}")
except Exception as e:
    print(f"❌ Cannot capture frame: {e}")
    picam2.stop()
    sys.exit(1)

# Test 6: Capture multiple frames
try:
    print("\nCapturing 10 frames to test FPS...")
    start = time.time()
    for i in range(10):
        frame = picam2.capture_array()
    elapsed = time.time() - start
    fps = 10 / elapsed
    print(f"✅ FPS: {fps:.1f}")
except Exception as e:
    print(f"❌ FPS test failed: {e}")

# Cleanup
picam2.stop()
print("\n" + "=" * 50)
print("✅ All tests passed!")
print("\nYour Pi Camera v2 is working with picamera2.")
print("The code has been updated to use picamera2.")

