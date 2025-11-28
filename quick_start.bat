@echo off
TITLE Association Mining System - Unified Starter

:: This script starts the Association Mining System servers using a unified Python script.

:: Get the directory of the batch file
set "CURRENT_DIR=%~dp0"
cd /d "%CURRENT_DIR%"

echo ====================================================================
echo  Starting Association Mining System...
echo ====================================================================
echo.

:: Activate virtual environment if it exists
IF EXIST "venv\Scripts\activate.bat" (
    echo Activating Python virtual environment...
    call venv\Scripts\activate.bat
    echo.
) ELSE (
    echo Virtual environment not found. Running with system Python.
    echo It is recommended to create and use a virtual environment.
    echo.
)

:: Run the unified server script
echo Starting servers via run_servers.py...
python run_servers.py start

echo.
echo ====================================================================
echo  Startup command issued. Servers are running in the background.
echo  You can close this window.
echo ====================================================================
echo.

pause

echo.
echo ========================================
echo  Servers Started Successfully!
echo ========================================
echo.
echo Flask UI:  http://localhost:5000
echo FastAPI:   http://localhost:8080
echo API Docs:  http://localhost:8080/docs
echo.
echo Two new command windows have opened.
echo Close those windows to stop the servers.
echo ========================================
echo.
echo You can close this window now.
echo.
pause
