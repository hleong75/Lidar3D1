#!/bin/bash
# Quick start script for Lidar3D

echo "Lidar3D - Quick Start"
echo "===================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed"
    exit 1
fi

echo "✓ Python 3 found"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

echo "✓ Dependencies installed"

# Run tests
echo ""
echo "Running tests..."
python3 -m pytest tests/ -v

if [ $? -ne 0 ]; then
    echo "Warning: Some tests failed, but you can still try the demo"
fi

# Run demo
echo ""
echo "Running demo..."
python3 demo.py

echo ""
echo "Setup complete! Check the demo output for your 3DS file."
