#!/bin/bash
echo ""
echo " ============================================"
echo "  CanonCache - KV-Cache Research Tool"
echo " ============================================"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo " [ERROR] python3 not found. Please install Python 3.10+"
    exit 1
fi

echo " Python: $(python3 --version)"

# Install dependencies
echo ""
echo " Checking dependencies..."
pip3 install -r requirements.txt --quiet

# Check tkinter
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo ""
    echo " [ERROR] tkinter not found."
    echo " On Ubuntu/Debian: sudo apt install python3-tk"
    echo " On Fedora:        sudo dnf install python3-tkinter"
    echo " On macOS:         brew install python-tk"
    exit 1
fi

echo ""
echo " Launching CanonCache..."
echo ""
python3 main.py
