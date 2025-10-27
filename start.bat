@echo off
REM Association Mining System - Windows Startup Script with PyMySQL
REM Updated for remote MySQL (10.102.246.10:6033)

echo ========================================
echo  Association Mining System - Startup
echo ========================================
echo.

REM Set Python executable path
set PYTHON_EXE=C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe

REM Check if Python exists
if not exist "%PYTHON_EXE%" (
    echo Error: Python not found at %PYTHON_EXE%
    echo Please update the PYTHON_EXE path in this script
    pause
    exit /b 1
)

echo Using Python: %PYTHON_EXE%
%PYTHON_EXE% --version
echo.

REM Check if .env file exists
if not exist ".env" (
    echo Warning: .env file not found
    if exist ".env.example" (
        echo Copying from .env.example...
        copy .env.example .env
    ) else (
        echo Error: No .env or .env.example file found
        pause
        exit /b 1
    )
)

REM Install/update dependencies
echo Installing/updating dependencies...
echo (This includes PyMySQL and cryptography)
%PYTHON_EXE% -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo Error installing dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully
echo.

REM Start FastAPI server on port 8080
echo Starting FastAPI server on port 8080...
start "FastAPI Server - Port 8080" %PYTHON_EXE% -m uvicorn app.main:app --host 0.0.0.0 --port 8080

REM Wait for FastAPI to start
echo Waiting 5 seconds for FastAPI to initialize...
timeout /t 5 /nobreak >nul

REM Start Flask UI server on port 5000
echo Starting Flask UI server on port 5000...
start "Flask UI - Port 5000" %PYTHON_EXE% flask_ui_enhanced.py

REM Wait a bit for Flask to start
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo  Servers Started Successfully!
echo ========================================
echo.
echo  Flask UI:  http://localhost:5000
echo  FastAPI:   http://localhost:8080
echo  API Docs:  http://localhost:8080/docs
echo.
echo MySQL Server: 10.102.246.10:6033
echo Database: neo
echo.
echo Close the terminal windows to stop servers
echo Or press Ctrl+C in each window
echo ========================================
echo.
pause