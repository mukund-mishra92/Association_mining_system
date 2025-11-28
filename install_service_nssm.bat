@echo off
REM Install service using NSSM (Non-Sucking Service Manager)
REM This is a better approach for running Python scripts as Windows services

echo ========================================
echo Installing Association Mining Service using NSSM
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

REM Check if NSSM exists
if not exist "nssm.exe" (
    echo.
    echo NSSM not found. Please download NSSM from:
    echo https://nssm.cc/download
    echo.
    echo 1. Download nssm-2.24.zip
    echo 2. Extract nssm.exe from win64 folder to this directory
    echo 3. Run this script again
    echo.
    pause
    exit /b 1
)

REM Set paths
set PYTHON_EXE=%~dp0venv\Scripts\python.exe
set SERVICE_SCRIPT=%~dp0service_runner.py
set SERVICE_NAME=AssociationMiningService

REM Check if Python exists
if not exist "%PYTHON_EXE%" (
    echo ERROR: Python not found at %PYTHON_EXE%
    pause
    exit /b 1
)

REM Remove existing service if it exists
echo Removing existing service if any...
nssm stop %SERVICE_NAME% >nul 2>&1
nssm remove %SERVICE_NAME% confirm >nul 2>&1

REM Install the service
echo.
echo Installing service...
nssm install %SERVICE_NAME% "%PYTHON_EXE%" "%SERVICE_SCRIPT%"

REM Configure service
echo Configuring service...
nssm set %SERVICE_NAME% DisplayName "Association Mining System Service"
nssm set %SERVICE_NAME% Description "Runs the Association Mining System FastAPI server and Flask UI"
nssm set %SERVICE_NAME% Start SERVICE_AUTO_START
nssm set %SERVICE_NAME% AppDirectory "%~dp0"
nssm set %SERVICE_NAME% AppStdout "%~dp0logs\service_stdout.log"
nssm set %SERVICE_NAME% AppStderr "%~dp0logs\service_stderr.log"
nssm set %SERVICE_NAME% AppRotateFiles 1
nssm set %SERVICE_NAME% AppRotateBytes 1048576

if %errorLevel% == 0 (
    echo.
    echo ========================================
    echo Service Installed Successfully!
    echo ========================================
    echo.
    echo Service Name: %SERVICE_NAME%
    echo Display Name: Association Mining System Service
    echo.
    echo To start the service, run: nssm start %SERVICE_NAME%
    echo Or use: start_service.bat
    echo.
) else (
    echo.
    echo ========================================
    echo ERROR: Service installation failed!
    echo ========================================
    echo.
)

pause
