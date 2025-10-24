@echo off
REM Association Mining System - Stop Script

echo Stopping Association Mining System...

REM Kill API Server
taskkill /FI "WINDOWTITLE eq API Server*" /F >nul 2>&1
if %errorlevel% equ 0 (
    echo FastAPI server stopped.
) else (
    echo FastAPI server was not running.
)

REM Kill UI Server
taskkill /FI "WINDOWTITLE eq UI Server*" /F >nul 2>&1
if %errorlevel% equ 0 (
    echo Flask UI server stopped.
) else (
    echo Flask UI server was not running.
)

REM Alternative: Kill by process name
taskkill /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" /F >nul 2>&1
taskkill /IM python.exe /FI "WINDOWTITLE eq *flask*" /F >nul 2>&1

echo.
echo Association Mining System stopped.
pause
