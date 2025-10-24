@echo off
REM Complete startup script with SSH tunnel for Association Mining System

echo ============================================================
echo Association Mining System - Complete Startup
echo ============================================================
echo.

REM Step 1: Start SSH Tunnel
echo Step 1: Setting up SSH tunnel to database...
echo.
set /p SSH_USER="Enter your SSH username for 10.102.246.10 (or press Enter to skip): "

if not "%SSH_USER%"=="" (
    echo.
    echo Starting SSH tunnel in a separate window...
    echo IMPORTANT: Keep the SSH tunnel window open!
    echo.
    start "MySQL SSH Tunnel" cmd /k "echo Connecting SSH tunnel... && ssh -L 6033:localhost:6033 %SSH_USER%@10.102.246.10"
    
    echo Waiting 5 seconds for SSH tunnel to establish...
    timeout /t 5 /nobreak >nul
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
echo If you started SSH tunnel, remember to keep it open.
echo Close all windows to stop the system.
echo.
pause
