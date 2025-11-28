@echo off
REM Start Association Mining System Service

echo ========================================
echo Starting Association Mining Service
echo ========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges...
) else (
    echo ERROR: This script must be run as Administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

REM Start the service
echo Starting service...
net start AssociationMiningService

if %errorLevel% == 0 (
    echo.
    echo ========================================
    echo Service Started Successfully!
    echo ========================================
    echo.
    echo The Association Mining System is now running in background
    echo.
    echo  FastAPI Server:  http://localhost:8080
    echo  Flask UI:        http://localhost:5000
    echo  API Docs:        http://localhost:8080/docs
    echo.
    echo To check service status: sc query AssociationMiningService
    echo To view logs: logs\service.log
    echo.
) else (
    echo.
    echo ========================================
    echo ERROR: Failed to start service!
    echo ========================================
    echo.
    echo Possible reasons:
    echo  1. Service not installed (run install_service.bat)
    echo  2. Service already running
    echo  3. Port 8080 or 5000 already in use
    echo.
    echo Check logs\service.log for details
    echo.
)

pause
