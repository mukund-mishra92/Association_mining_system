@echo off
REM ========================================
REM Association Mining System - Quick Start
REM For systems already set up
REM ========================================

echo.
echo ========================================
echo  Association Mining System
echo  Quick Start
echo ========================================
echo.

REM Check if virtual environment exists
if not exist venv\Scripts\activate.bat (
    echo ERROR: Virtual environment not found!
    echo.
    echo This appears to be a new installation.
    echo Please run setup_and_start.bat instead for first-time setup.
    echo.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo ERROR: Configuration file ^(.env^) not found!
    echo.
    echo Please create .env file with your database configuration.
    echo See setup_and_start.bat for required settings.
    echo.
    pause
    exit /b 1
)

echo Starting servers...
echo.

REM Start FastAPI
echo [1/2] Starting FastAPI on port 8080...
start "Association Mining - FastAPI" cmd /k "cd /d %~dp0 && call venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload"

timeout /t 3 /nobreak >nul

REM Start Flask UI
echo [2/2] Starting Flask UI on port 5000...
start "Association Mining - Flask UI" cmd /k "cd /d %~dp0 && call venv\Scripts\activate.bat && python app\web\main.py"

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo  Servers Started Successfully!
echo ========================================
echo.
echo Flask UI:  http://localhost:5000
echo FastAPI:   http://localhost:8080
echo API Docs:  http://localhost:8080/docs
echo.
echo Two new command windows have opened.
echo Close those windows to stop the servers.
echo ========================================
echo.
echo You can close this window now.
echo.
pause
