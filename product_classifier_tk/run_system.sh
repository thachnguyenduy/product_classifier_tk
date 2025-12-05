#!/bin/bash
# ==============================================================================
# Script to run the Bottle Defect Detection System
# Automatically handles Qt platform plugin issues on Raspberry Pi
# ==============================================================================

# Set Qt platform to X11 (fixes Wayland plugin error)
export QT_QPA_PLATFORM=xcb

# Disable Qt warning messages (optional)
export QT_LOGGING_RULES='*.debug=false;qt.qpa.*=false'

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
echo "=============================================="
echo "Starting with Qt platform: xcb (X11)"
echo "Press Ctrl+C to stop"
echo "=============================================="
echo ""

# Run the system
python3 main_continuous_flow.py

# Cleanup on exit
echo ""
echo "=============================================="
echo "✅ System stopped"
echo "=============================================="

