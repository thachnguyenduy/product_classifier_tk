#!/bin/bash
# Script để setup và test Raspberry Pi Camera v2

echo "=========================================="
echo "Raspberry Pi Camera v2 Setup & Test"
echo "=========================================="

# 1. Kiểm tra có phải Raspberry Pi không
if [ ! -f /proc/device-tree/model ]; then
    echo "❌ This is not a Raspberry Pi"
    exit 1
fi

echo "✅ Running on: $(cat /proc/device-tree/model)"
echo ""

# 2. Kiểm tra camera có được enable không
echo "Checking camera status..."
if ! vcgencmd get_camera | grep -q "detected=1"; then
    echo "❌ Camera not detected!"
    echo ""
    echo "Please enable camera:"
    echo "  1. Run: sudo raspi-config"
    echo "  2. Go to: Interface Options → Camera"
    echo "  3. Select: Yes"
    echo "  4. Reboot"
    exit 1
fi

echo "✅ Camera detected"
echo ""

# 3. Kiểm tra camera device
echo "Checking camera devices..."
if [ -e /dev/video0 ]; then
    echo "✅ /dev/video0 exists"
    v4l2-ctl --device=/dev/video0 --list-formats-ext 2>/dev/null || echo "  (v4l2-ctl not installed)"
else
    echo "❌ /dev/video0 not found"
fi
echo ""

# 4. Test với libcamera
echo "Testing with libcamera-hello (5 seconds)..."
if command -v libcamera-hello &> /dev/null; then
    timeout 5 libcamera-hello --timeout 5000 2>&1 | head -20
    echo "✅ libcamera test complete"
else
    echo "⚠️  libcamera-hello not found"
fi
echo ""

# 5. Test với Python OpenCV
echo "Testing with Python OpenCV..."
python3 << 'EOF'
import cv2
import sys

print("Trying cv2.VideoCapture(0, cv2.CAP_V4L2)...")
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

if not cap.isOpened():
    print("❌ Cannot open camera with V4L2")
    sys.exit(1)

ret, frame = cap.read()
cap.release()

if not ret or frame is None:
    print("❌ Cannot read frame")
    sys.exit(1)

print(f"✅ OpenCV camera test passed!")
print(f"   Frame shape: {frame.shape}")
print(f"   Frame dtype: {frame.dtype}")
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Camera setup complete!"
    echo "You can now run: python main.py"
    echo "=========================================="
else
    echo ""
    echo "=========================================="
    echo "❌ Camera test failed"
    echo ""
    echo "Troubleshooting:"
    echo "1. Enable camera in raspi-config"
    echo "2. Check cable connection"
    echo "3. Reboot Raspberry Pi"
    echo "4. Check /boot/config.txt has:"
    echo "   camera_auto_detect=1"
    echo "   dtoverlay=vc4-kms-v3d"
    echo "=========================================="
fi

