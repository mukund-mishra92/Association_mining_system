@echo off
REM Start servers in background without visible windows

echo ========================================
echo  Association Mining System
echo  Background Mode
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run setup first.
    pause
    exit /b 1
)

REM Start servers in background
venv\Scripts\python.exe start_background.py

echo.
pause
