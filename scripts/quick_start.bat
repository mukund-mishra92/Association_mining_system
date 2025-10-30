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

REM Check if virtual environment exists and should be used
set USE_VENV=
if exist ".venv\Scripts\python.exe" (
    echo Virtual environment found!
    set PYTHON_VENV=.venv\Scripts\python.exe
    set USE_VENV=1
    echo Using virtual environment Python
) else (
    echo No virtual environment found, using system Python
    set PYTHON_VENV=%PYTHON%
)

REM Start FastAPI on port 8080
echo [1/2] Starting FastAPI on port 8080...
start "FastAPI-8080" cmd /k "cd /d %~dp0.. && %PYTHON_VENV% -m uvicorn app.main:app --host 0.0.0.0 --port 8080"

REM Wait 3 seconds
timeout /t 3 /nobreak >nul

REM Start Flask on port 5000
echo [2/2] Starting Flask UI on port 5000...
start "Flask-5000" cmd /k "cd /d %~dp0.. && %PYTHON_VENV% -m app.web.main"

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
