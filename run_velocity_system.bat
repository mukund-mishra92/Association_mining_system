@echo off
REM 🚀 Velocity Analysis System - Windows Batch Launcher
REM This script activates the virtual environment and runs the velocity analysis

echo ============================================================
echo 🚀 VELOCITY ANALYSIS SYSTEM - QUICK START
echo ============================================================

REM Change to project directory
cd /d "C:\Users\Balmukund.Mishra\Desktop\NEO\association_mining_system"

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ❌ Virtual environment not found at: venv\Scripts\activate.bat
    echo Please ensure the virtual environment is set up correctly.
    pause
    exit /b 1
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if activation was successful
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

echo ✅ Virtual environment activated

REM Run the velocity analysis
echo 🔄 Starting velocity analysis system...
python run_velocity_analysis.py

REM Check the result
if errorlevel 1 (
    echo ❌ Velocity analysis failed
) else (
    echo ✅ Velocity analysis completed successfully
)

echo.
echo Press any key to exit...
pause