@echo off
REM Uninstall Association Mining System Service

echo ========================================
echo Uninstalling Association Mining Service
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

REM Stop the service first if running
echo Stopping service if running...
net stop AssociationMiningService 2>nul

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Uninstall the service
echo.
echo Uninstalling service...
python windows_service.py remove

if %errorLevel% == 0 (
    echo.
    echo ========================================
    echo Service Uninstalled Successfully!
    echo ========================================
    echo.
    echo The Association Mining System service has been removed
    echo.
    echo To reinstall: install_service.bat
    echo.
) else (
    echo.
    echo ========================================
    echo ERROR: Service uninstallation failed!
    echo ========================================
    echo.
    echo Please check:
    echo  1. Running as Administrator
    echo  2. Service was previously installed
    echo  3. Check logs\service.log for details
    echo.
)

pause
