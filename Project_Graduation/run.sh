#!/bin/bash
# Coca-Cola Sorting System - Startup Script

echo "=========================================="
echo "🥤 Coca-Cola Sorting System"
echo "=========================================="
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 is not installed"
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Python version: $python_version"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✓ Activating virtual environment..."
    source venv/bin/activate
fi

# Run the application
echo ""
echo "Starting application..."
echo ""

python3 main.py

echo ""
echo "Application closed."

