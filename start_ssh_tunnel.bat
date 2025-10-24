@echo off
REM SSH Tunnel Setup for MySQL Database Access
REM This creates a secure tunnel to forward MySQL port from remote server to localhost

echo ============================================================
echo SSH Tunnel for MySQL Database
echo ============================================================
echo.
echo This will create a tunnel from:
echo   Remote: 10.102.246.10:6033 (MySQL on server)
echo   Local:  localhost:6033 (your machine)
echo.
echo IMPORTANT: Keep this window open while using the application!
echo.

REM Prompt for SSH username if not provided
set /p SSH_USER="Enter your SSH username for 10.102.246.10: "

echo.
echo Starting SSH tunnel...
echo You will be prompted for your SSH password.
echo.

REM Create SSH tunnel
ssh -L 6033:localhost:6033 %SSH_USER%@10.102.246.10

echo.
echo SSH tunnel closed.
pause
