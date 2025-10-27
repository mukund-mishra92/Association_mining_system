@echo off
REM Stop Association Mining System servers

echo ========================================
echo  Stopping Association Mining System
echo ========================================
echo.

REM Kill Flask processes
echo Stopping Flask UI server (port 5000)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM Kill FastAPI processes
echo Stopping FastAPI server (port 8080)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8080 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM Also kill any Python processes running uvicorn or flask_ui_enhanced
echo Cleaning up any remaining server processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq FastAPI*" >nul 2>&1
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Flask*" >nul 2>&1

echo.
echo ========================================
echo  All servers stopped
echo ========================================
echo.
pause
