#!/bin/bash

# BillBox OCR Service - Installation Script
# This script sets up the Python environment and builds the C++ extension

set -e  # Exit on any error

echo "BillBox OCR Service - Installation Script"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "src/python_bindings.cpp" ]; then
    echo "✗ Error: Run this script from services/ocr directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip and install build dependencies
echo "Installing build dependencies..."
pip install --upgrade pip setuptools wheel

# Install requirements
echo "Installing Python requirements..."
pip install -r requirements.txt

# Build the C++ extension
echo "Building C++ extension..."
python build.py

# Test the installation
echo "Testing installation..."
python -c "
import billbox_preprocessing as bp
print('✓ C++ module loaded successfully')
config = bp.create_invoice_config()
print(f'✓ Basic functionality works: deskewing={config.enable_deskewing}')
"

echo ""
echo "✓ Installation completed successfully!"
echo ""
echo "To use the OCR service:"
echo "  source venv/bin/activate"
echo "  python billbox_ocr.py"
echo ""
echo "To run tests:"
echo "  python test_python_bindings.py"