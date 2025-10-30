@echo off
REM Association Mining System - Windows Startup Script with PyMySQL
REM Updated for generalized Python detection

echo ========================================
echo  Association Mining System - Startup
echo ========================================
echo.

REM Function to detect Python executable
set PYTHON_EXE=
REM Try py command first (Windows Python Launcher)
py --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_EXE=py
    echo Found Python using 'py' command
    goto :python_found
)

REM Try python command
python --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_EXE=python
    echo Found Python using 'python' command
    goto :python_found
)

REM Try python3 command
python3 --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_EXE=python3
    echo Found Python using 'python3' command
    goto :python_found
)

REM If no Python found
echo Error: Python not found. Please install Python or ensure it's in your PATH
echo Tried: py, python, python3
pause
exit /b 1

:python_found
echo Using Python: %PYTHON_EXE%
%PYTHON_EXE% --version
echo.

REM Check if virtual environment exists and activate it
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
    echo Virtual environment activated
    set PYTHON_EXE=python
    echo.
) else (
    echo No virtual environment found, using system Python
)

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
%PYTHON_EXE% -m pip install -r requirements.txt
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
start "Flask UI - Port 5000" %PYTHON_EXE% -m app.web.main

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