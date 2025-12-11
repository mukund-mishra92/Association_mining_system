@echo off
REM ========================================
REM Association Mining System - Stop Servers
REM ========================================

echo.
echo Stopping Association Mining System servers...
echo.

REM Kill FastAPI (port 8080) - works for both windowed and background mode
echo [1/2] Stopping FastAPI server...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080.*LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)
REM Also try by window title for windowed mode
taskkill /FI "WindowTitle eq Association Mining - FastAPI*" /T /F >nul 2>&1
echo FastAPI server stopped successfully!

REM Kill Flask (port 5000) - works for both windowed and background mode
echo [2/2] Stopping Flask UI server...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000.*LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)
REM Also try by window title for windowed mode
taskkill /FI "WindowTitle eq Association Mining - Flask UI*" /T /F >nul 2>&1
echo Flask UI server stopped successfully!

echo.
echo ========================================
echo All servers stopped!
echo ========================================
echo.
pause
