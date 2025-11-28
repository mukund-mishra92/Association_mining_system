@echo off
REM Install Association Mining System as Windows Service

echo ========================================
echo Installing Association Mining Service
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

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found at venv\
    echo Make sure you have Python and required packages installed
)

REM Install pywin32 if not already installed
echo.
echo Checking for pywin32 package...
python -c "import win32serviceutil" 2>nul
if %errorLevel% neq 0 (
    echo Installing pywin32...
    pip install pywin32
    python -m win32api install
) else (
    echo pywin32 is already installed
)

REM Install the service
echo.
echo Installing service...
python windows_service.py install

if %errorLevel% == 0 (
    echo.
    echo ========================================
    echo Service Installed Successfully!
    echo ========================================
    echo.
    echo Service Name: AssociationMiningService
    echo Display Name: Association Mining System Service
    echo.
    echo To start the service, run: start_service.bat
    echo To configure startup: services.msc
    echo.
) else (
    echo.
    echo ========================================
    echo ERROR: Service installation failed!
    echo ========================================
    echo.
    echo Please check:
    echo  1. Running as Administrator
    echo  2. Python and pywin32 are installed
    echo  3. Check logs\service.log for details
    echo.
)

pause
