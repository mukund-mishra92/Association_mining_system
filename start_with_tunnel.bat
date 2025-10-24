@echo off
REM Complete startup script with SSH tunnel for Association Mining System

echo ============================================================
echo Association Mining System - Complete Startup
echo ============================================================
echo.

REM Step 1: Start SSH Tunnel
echo Step 1: Setting up SSH tunnel to remote database server...
echo.
echo Available remote servers:
echo   - 10.102.246.9
echo   - 10.102.246.10
echo.
set /p REMOTE_IP="Enter remote server IP: "
set /p SSH_USER="Enter your SSH username for %REMOTE_IP%: "

if not "%SSH_USER%"=="" (
    echo.
    echo Starting SSH tunnel in a separate window...
    echo IMPORTANT: Keep the SSH tunnel window open!
    echo.
    start "MySQL SSH Tunnel to %REMOTE_IP%" cmd /k "echo Connecting SSH tunnel to %REMOTE_IP%... && ssh -L 6033:localhost:6033 %SSH_USER%@%REMOTE_IP%"
    
    echo Waiting 8 seconds for SSH tunnel to establish...
    timeout /t 8 /nobreak >nul
)

REM Step 2: Start Application
echo.
echo Step 2: Starting Association Mining System...
echo.

call start.bat

echo.
echo ============================================================
echo Startup Complete!
echo ============================================================
echo.
echo SSH Tunnel: Active to %REMOTE_IP%
echo Application UI: http://localhost:5500
echo Application API: http://localhost:8080
echo.
echo IMPORTANT: Keep the SSH tunnel window open!
echo Close all windows to stop the system.
echo.
pause
