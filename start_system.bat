@echo off
echo =======================================================
echo      Association Mining System - Complete Startup
echo =======================================================
echo.

echo [1/3] Starting Database Configuration UI...
echo     URL: http://localhost:5000
echo.
start cmd /k "cd /d %~dp0 && py flask_ui_enhanced.py"

echo [2/3] Waiting 3 seconds...
timeout /t 3 /nobreak >nul

echo [3/3] Starting FastAPI Backend Server...
echo     URL: http://localhost:8001
echo.
start cmd /k "cd /d %~dp0 && python -m uvicorn app.main:app --reload --port 8001"

echo.
echo =======================================================
echo   System Started Successfully!
echo =======================================================
echo.
echo   Database Config UI: http://localhost:5000
echo   FastAPI Backend:    http://localhost:8001
echo.
echo   1. Configure database settings at localhost:5000
echo   2. Test connection and save configuration
echo   3. Use the mining interface
echo.
echo Press any key to open the Database Config UI...
pause >nul
start http://localhost:5000