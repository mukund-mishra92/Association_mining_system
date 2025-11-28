@echo off
REM Stop Association Mining System Service

echo ========================================
echo Stopping Association Mining Service
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

REM Stop the service
echo Stopping service...
net stop AssociationMiningService

if %errorLevel% == 0 (
    echo.
    echo ========================================
    echo Service Stopped Successfully!
    echo ========================================
    echo.
    echo The Association Mining System has been stopped
    echo.
    echo To start again: start_service.bat
    echo.
) else (
    echo.
    echo ========================================
    echo ERROR: Failed to stop service!
    echo ========================================
    echo.
    echo Possible reasons:
    echo  1. Service not installed
    echo  2. Service already stopped
    echo  3. Insufficient permissions
    echo.
    echo Check logs\service.log for details
    echo.
)

pause
