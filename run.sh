#!/bin/bash
# BillBox Launcher Script for Unix/Linux/macOS

set -e

echo "🚀 Starting BillBox..."
echo "📁 Project directory: $(pwd)"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Run the Python launcher
python3 run.py "$@"