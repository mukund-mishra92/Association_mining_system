@echo off
REM SSH Tunnel Setup for MySQL Database Access
REM This creates a secure tunnel to forward MySQL port from remote server to localhost

echo ============================================================
echo SSH Tunnel for MySQL Database
echo ============================================================
echo.
echo This will create a tunnel from:
echo   Remote Server: 10.102.246.10 (or .9)
echo   Remote MySQL: localhost:6033 (on the server)
echo   Local Access: localhost:6033 (on your machine)
echo.
echo IMPORTANT: Keep this window open while using the application!
echo.

REM Prompt for remote server IP
set /p REMOTE_IP="Enter remote server IP (10.102.246.9 or 10.102.246.10): "

REM Prompt for SSH username
set /p SSH_USER="Enter your SSH username for %REMOTE_IP%: "

echo.
echo Starting SSH tunnel to %REMOTE_IP%...
echo You will be prompted for your SSH password.
echo.

REM Create SSH tunnel
REM This forwards local port 6033 to localhost:6033 on the remote server
ssh -L 6033:localhost:6033 %SSH_USER%@%REMOTE_IP%

echo.
echo SSH tunnel closed.
pause
