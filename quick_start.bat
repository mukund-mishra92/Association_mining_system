@echo off
REM Quick Start Script - Association Mining System

echo Starting servers...
echo.

REM Set Python path
set PYTHON=C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe

REM Start FastAPI on port 8080
echo [1/2] Starting FastAPI on port 8080...
start "FastAPI-8080" cmd /k "%PYTHON% -m uvicorn app.main:app --host 0.0.0.0 --port 8080"

REM Wait 3 seconds
timeout /t 3 /nobreak >nul

REM Start Flask on port 5000
echo [2/2] Starting Flask UI on port 5000...
start "Flask-5000" cmd /k "%PYTHON% flask_ui_enhanced.py"

echo.
echo ========================================
echo Both servers starting in new windows!
echo ========================================
echo.
echo Flask UI:  http://localhost:5000
echo FastAPI:   http://localhost:8080
echo.
echo Close those windows to stop the servers
echo ========================================
