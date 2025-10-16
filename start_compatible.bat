@echo off
REM Association Mining System - Windows Startup Script (Compatible Version)

echo Starting Association Mining System...

REM Check if Python is available (try py first, then python)
set PYTHON_CMD=
py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py
    echo Using Python launcher: py
) else (
    python --version >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=python
        echo Using Python command: python
    ) else (
        echo Error: Python is not installed or not in PATH
        echo Please install Python from python.org or Microsoft Store
        echo Or ensure Python is added to your system PATH
        pause
        exit /b 1
    )
)

REM Check if .env file exists
if not exist ".env" (
    echo Warning: .env file not found. Copying from .env.production
    if exist ".env.production" (
        copy .env.production .env
    ) else (
        echo Creating basic .env file...
        echo DB_HOST=localhost > .env
        echo DB_USER=root >> .env
        echo DB_PASSWORD= >> .env
        echo DB_NAME=neo >> .env
    )
)

REM Install dependencies
echo Installing/updating dependencies...
%PYTHON_CMD% -m pip install -r requirements.txt
if errorlevel 1 (
    echo Warning: Some dependencies might have failed to install
    echo Continuing with startup...
)

REM Start API server in background
echo Starting FastAPI server on port 8001...
start "Association Mining API Server" %PYTHON_CMD% -m uvicorn app.main:app --host 0.0.0.0 --port 8001

REM Wait for API to start
echo Waiting for API server to initialize...
timeout /t 8 /nobreak >nul

REM Start Flask UI server
echo Starting Flask UI server on port 5000...
start "Association Mining UI Server" %PYTHON_CMD% flask_ui_enhanced.py

REM Wait a moment for UI to start
timeout /t 3 /nobreak >nul

echo.
echo ===============================================
echo Association Mining System Started Successfully!
echo ===============================================
echo.
echo Access the application at:
echo   UI Dashboard: http://localhost:5000
echo   API Documentation: http://localhost:8001/docs
echo   API Endpoints: http://localhost:8001
echo.
echo Two windows have opened:
echo   1. API Server (FastAPI) - Port 8001
echo   2. UI Server (Flask) - Port 5000
echo.
echo To stop the system:
echo   - Close both server windows, or
echo   - Press Ctrl+C in each window
echo.
echo Enjoy your Association Mining System!
echo ===============================================
pause