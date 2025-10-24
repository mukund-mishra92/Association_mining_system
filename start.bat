@echo off
REM Association Mining System - Windows Production Startup Script

echo Starting Association Mining System...

REM Add Python to PATH for this session
set "PATH=%USERPROFILE%\AppData\Local\Programs\Python\Python314;%USERPROFILE%\AppData\Local\Programs\Python\Python314\Scripts;%PATH%"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python from python.org or Microsoft Store
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo Warning: .env file not found. Copying from .env.example
    if exist ".env.example" (
        copy .env.example .env
    ) else (
        echo Error: .env.example not found!
        pause
        exit /b 1
    )
)

REM Install dependencies (skip if already installed to speed up)
echo Checking dependencies...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt --quiet

REM Start API server in background
echo Starting FastAPI server on port 8080...
start "API Server" python -m uvicorn app.main:app --host 0.0.0.0 --port 8080

REM Wait for API to start
timeout /t 5 /nobreak >nul

REM Start Flask UI server
echo Starting Flask UI server on port 5500...
start "UI Server" python flask_ui_enhanced.py

echo.
echo ============================================================
echo Association Mining System started successfully!
echo ============================================================
echo.
echo Access the application at:
echo   UI:  http://localhost:5500
echo   API: http://localhost:8080
echo.
echo Close the command windows to stop the servers.
echo ============================================================
pause