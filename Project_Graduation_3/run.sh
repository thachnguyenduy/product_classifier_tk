#!/bin/bash
# ============================================
# RUN SCRIPT - Coca-Cola Sorting System
# ============================================

echo "==========================================="
echo "  COCA-COLA SORTING SYSTEM"
echo "  FIFO Queue Mode"
echo "==========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found!"
    exit 1
fi

# Check dependencies
echo "Checking dependencies..."
python3 -c "import cv2, numpy, serial, PIL" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies!"
    echo "Run: pip3 install -r requirements.txt"
    exit 1
fi

echo "✅ Dependencies OK"
echo ""

# Check NCNN (optional)
python3 -c "import ncnn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  NCNN not found - will use dummy fallback"
    echo "   To install: sudo apt-get install python3-ncnn"
else
    echo "✅ NCNN OK"
fi

echo ""
echo "Starting system..."
echo "==========================================="
echo ""

# Run main script
python3 main.py

echo ""
echo "System stopped."

