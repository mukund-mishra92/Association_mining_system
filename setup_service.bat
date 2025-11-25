@echo off
REM Quick Setup Script for Windows Service

echo ========================================
echo Association Mining System
echo Windows Service Quick Setup
echo ========================================
echo.

echo This script will guide you through the service setup process.
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  ERROR: This script must be run as Administrator!
    echo.
    echo Please:
    echo  1. Right-click this file
    echo  2. Select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo ✓ Running with administrator privileges
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8+ from https://www.python.org
    echo.
    pause
    exit /b 1
)

echo ✓ Python is installed
python --version
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo ⚠️  Virtual environment not found. Creating...
    python -m venv venv
    if %errorLevel% neq 0 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install/update requirements
echo Installing required packages...
pip install --upgrade pip
pip install -r requirements.txt
if %errorLevel% neq 0 (
    echo ❌ Failed to install requirements
    pause
    exit /b 1
)
echo ✓ All packages installed
echo.

REM Install pywin32 specifically
echo Installing Windows service support (pywin32)...
pip install pywin32
python -m pywin32_postinstall -install
echo ✓ Windows service support installed
echo.

REM Setup database
echo ========================================
echo Database Setup
echo ========================================
echo.
echo Would you like to setup the database tables now? (Y/N)
set /p DB_SETUP="Enter choice: "

if /i "%DB_SETUP%"=="Y" (
    echo.
    echo Running database setup...
    python utils\setup\database_setup_checker.py
    echo.
)

REM Install service
echo ========================================
echo Service Installation
echo ========================================
echo.
echo Installing Windows service...
python windows_service.py install

if %errorLevel% neq 0 (
    echo ❌ Service installation failed
    echo Please check the error messages above
    pause
    exit /b 1
)

echo ✓ Service installed successfully
echo.

REM Ask to configure auto-start
echo Would you like the service to start automatically with Windows? (Y/N)
set /p AUTO_START="Enter choice: "

if /i "%AUTO_START%"=="Y" (
    sc config AssociationMiningService start= auto
    echo ✓ Service configured for automatic startup
    echo.
)

REM Ask to start service now
echo Would you like to start the service now? (Y/N)
set /p START_NOW="Enter choice: "

if /i "%START_NOW%"=="Y" (
    echo.
    echo Starting service...
    net start AssociationMiningService
    echo.
    
    if %errorLevel% == 0 (
        echo ========================================
        echo 🎉 Setup Complete!
        echo ========================================
        echo.
        echo The Association Mining System is now running as a service
        echo.
        echo Access Points:
        echo  • Flask UI:  http://localhost:5000
        echo  • FastAPI:   http://localhost:8080
        echo  • API Docs:  http://localhost:8080/docs
        echo.
        echo Service Management:
        echo  • Check Status:  check_service.bat
        echo  • Stop Service:  stop_service.bat (run as admin)
        echo  • Start Service: start_service.bat (run as admin)
        echo  • View Logs:     logs\service.log
        echo.
        echo For full documentation, see: SERVICE_SETUP.md
        echo.
    ) else (
        echo ⚠️  Service installed but failed to start
        echo Check logs\service.log for error details
        echo.
    )
) else (
    echo.
    echo ========================================
    echo Installation Complete (Service Not Started)
    echo ========================================
    echo.
    echo Service installed but not started.
    echo To start: run start_service.bat as administrator
    echo.
    echo For full documentation, see: SERVICE_SETUP.md
    echo.
)

echo Press any key to finish...
pause >nul
