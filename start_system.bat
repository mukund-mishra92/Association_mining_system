@echo off
echo =======================================================
echo      Association Mining System - Complete Startup
echo =======================================================
echo.

REM Function to detect Python executable
set PYTHON_CMD=
REM Try py command first (Windows Python Launcher)
py --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=py
    echo Found Python using 'py' command
    goto :python_found
)

REM Try python command
python --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=python
    echo Found Python using 'python' command
    goto :python_found
)

REM Try python3 command
python3 --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=python3
    echo Found Python using 'python3' command
    goto :python_found
)

REM If no Python found
echo Error: Python not found. Please install Python or ensure it's in your PATH
echo Tried: py, python, python3
pause
exit /b 1

:python_found
%PYTHON_CMD% --version
echo.

echo [1/3] Starting Database Configuration UI...
echo     URL: http://localhost:5000
echo.
start cmd /k "cd /d %~dp0 && %PYTHON_CMD% flask_ui_enhanced.py"

echo [2/3] Waiting 3 seconds...
timeout /t 3 /nobreak >nul

echo [3/3] Starting FastAPI Backend Server...
echo     URL: http://localhost:8001
echo.
start cmd /k "cd /d %~dp0 && %PYTHON_CMD% -m uvicorn app.main:app --reload --port 8001"

echo.
echo =======================================================
echo   System Started Successfully!
echo =======================================================
echo.
echo   Database Config UI: http://localhost:5000
echo   FastAPI Backend:    http://localhost:8001
echo.
echo   1. Configure database settings at localhost:5000
echo   2. Test connection and save configuration
echo   3. Use the mining interface
echo.
echo Press any key to open the Database Config UI...
pause >nul
start http://localhost:5000