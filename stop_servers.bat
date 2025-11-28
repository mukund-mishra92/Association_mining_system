@echo off
TITLE Association Mining System - Server Stopper

:: This script stops the Association Mining System servers using the unified Python script.

:: Get the directory of the batch file
set "CURRENT_DIR=%~dp0"
cd /d "%CURRENT_DIR%"

echo ====================================================================
echo  Stopping Association Mining System...
echo ====================================================================
echo.

:: Activate virtual environment if it exists
IF EXIST "venv\Scripts\activate.bat" (
    echo Activating Python virtual environment...
    call venv\Scripts\activate.bat
    echo.
) ELSE (
    echo Virtual environment not found. Assuming system Python was used.
    echo.
)

:: Run the unified server script to stop servers
echo Stopping servers via run_servers.py...
python run_servers.py stop

echo.
echo ====================================================================
echo  Shutdown command issued.
echo ====================================================================
echo.

pause
