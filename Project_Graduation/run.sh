#!/bin/bash
# Coca-Cola Sorting System - Startup Script (CONTINUOUS MODE)

echo "=========================================="
echo "🥤 Coca-Cola Sorting System"
echo "   CONTINUOUS MODE"
echo "=========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "   Install with: sudo apt install python3"
    exit 1
fi

# Check if required packages are installed
echo "Checking dependencies..."
python3 -c "import cv2" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ OpenCV not installed!"
    echo "   Install with: pip3 install opencv-python"
    exit 1
fi

python3 -c "import serial" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ PySerial not installed!"
    echo "   Install with: pip3 install pyserial"
    exit 1
fi

echo "✓ Dependencies OK"
echo ""

# Run the application
echo "Starting application..."
python3 main.py

echo ""
echo "Application closed."
