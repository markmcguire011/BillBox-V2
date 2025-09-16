@echo off
REM BillBox Launcher Script for Windows

echo 🚀 Starting BillBox...
echo 📁 Project directory: %CD%

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is required but not installed
    pause
    exit /b 1
)

REM Run the Python launcher
python run.py %*

pause