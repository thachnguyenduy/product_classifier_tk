#!/bin/bash
# ==============================================================================
# Script to run the Bottle Defect Detection System (Tkinter Version)
# Recommended for Raspberry Pi - no Qt dependencies!
# ==============================================================================

# Check if running in virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment active: $VIRTUAL_ENV"
else
    echo "⚠️  Warning: Not running in virtual environment"
    echo "   Consider activating venv first:"
    echo "   source venv/bin/activate"
    echo ""
fi

# Check if model exists
if [ ! -f "model/my_model.pt" ]; then
    echo "❌ Error: Model file not found!"
    echo "   Please place your YOLOv8 model at: model/my_model.pt"
    exit 1
fi

# Display info
echo ""
echo "=============================================="
echo "🍾 Bottle Defect Detection System"
echo "   Tkinter GUI Version"
echo "=============================================="
echo "Starting system..."
echo "Press Ctrl+C to stop"
echo "=============================================="
echo ""

# Run the Tkinter version
python3 main_continuous_flow_tkinter.py

# Cleanup on exit
echo ""
echo "=============================================="
echo "✅ System stopped"
echo "=============================================="

