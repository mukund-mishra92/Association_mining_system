@echo off
REM Quick Start Script - Association Mining System

echo Starting servers...
echo.

REM Function to detect Python executable
set PYTHON=
REM Try py command first (Windows Python Launcher)
py --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON=py
    echo Found Python using 'py' command
    goto :python_found
)

REM Try python command
python --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON=python
    echo Found Python using 'python' command
    goto :python_found
)

REM Try python3 command
python3 --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON=python3
    echo Found Python using 'python3' command
    goto :python_found
)

REM If no Python found
echo Error: Python not found. Please install Python or ensure it's in your PATH
echo Tried: py, python, python3
pause
exit /b 1

:python_found
echo Using Python: %PYTHON%
%PYTHON% --version
echo.

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
