@echo off
REM Association Mining System - Windows Production Startup Script

echo Starting Association Mining System...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo Warning: .env file not found. Copying from .env.production
    copy .env.production .env
)

REM Install dependencies
echo Installing/updating dependencies...
pip install -r requirements.txt

REM Start API server in background
echo Starting FastAPI server on port 8001...
start "API Server" python -m uvicorn app.main:app --host 0.0.0.0 --port 8001

REM Wait for API to start
timeout /t 5 /nobreak >nul

REM Start Flask UI server
echo Starting Flask UI server on port 5000...
start "UI Server" python flask_ui_enhanced.py

echo.
echo Association Mining System started successfully!
echo.
echo Access the application at:
echo   UI: http://localhost:5000
echo   API: http://localhost:8001
echo.
echo Close the command windows to stop the servers.
pause