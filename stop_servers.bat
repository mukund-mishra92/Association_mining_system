@echo off
REM ========================================
REM Association Mining System - Stop Servers
REM ========================================

echo.
echo Stopping Association Mining System servers...
echo.

REM Kill FastAPI (uvicorn) processes
echo [1/2] Stopping FastAPI server...
taskkill /FI "WindowTitle eq Association Mining - FastAPI*" /T /F >nul 2>&1
if %errorlevel% equ 0 (
    echo FastAPI server stopped successfully!
) else (
    echo No FastAPI server found running.
)

REM Kill Flask processes
echo [2/2] Stopping Flask UI server...
taskkill /FI "WindowTitle eq Association Mining - Flask UI*" /T /F >nul 2>&1
if %errorlevel% equ 0 (
    echo Flask UI server stopped successfully!
) else (
    echo No Flask UI server found running.
)

echo.
echo ========================================
echo All servers stopped!
echo ========================================
echo.
pause
