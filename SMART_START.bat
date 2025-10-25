@echo off
REM Association Mining System - Ultimate Startup Script
REM Automatically detects and uses the correct Python command

echo ================================================================
echo        Association Mining System - Smart Startup
echo ================================================================
echo.

REM Detect available Python command
set PYTHON_CMD=
echo [1/5] Detecting Python installation...

py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py
    echo     ✓ Found Python Launcher: py
    py --version
    goto :python_found
)

python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
    echo     ✓ Found Python: python
    python --version
    goto :python_found
)

python3 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python3
    echo     ✓ Found Python3: python3
    python3 --version
    goto :python_found
)

echo     ✗ Python not found!
echo.
echo ERROR: No Python installation detected
echo.
echo Please install Python from:
echo   • https://python.org
echo   • Microsoft Store (Windows)
echo   • Or ensure Python is in your system PATH
echo.
pause
exit /b 1

:python_found
echo.

REM Check if .env file exists
echo [2/5] Checking environment configuration...
if not exist ".env" (
    echo     ⚠ .env file not found
    if exist ".env.production" (
        echo     ➤ Copying from .env.production
        copy .env.production .env >nul
        echo     ✓ Created .env file
    ) else (
        echo     ➤ Creating basic .env file
        echo DB_HOST=localhost > .env
        echo DB_USER=root >> .env
        echo DB_PASSWORD= >> .env
        echo DB_NAME=neo >> .env
        echo ORDER_TABLE=wms_to_wcs_order_line_request_data >> .env
        echo SKU_MASTER_TABLE=sku_master >> .env
        echo RECOMMENDATIONS_TABLE=sku_recommendations >> .env
        echo     ✓ Created basic .env file
    )
) else (
    echo     ✓ .env file found
)
echo.

REM Install dependencies
echo [3/5] Installing/updating dependencies...
%PYTHON_CMD% -m pip install --upgrade pip >nul 2>&1
%PYTHON_CMD% -m pip install -r requirements.txt
if errorlevel 1 (
    echo     ⚠ Some dependencies may have failed to install
    echo     ➤ Continuing with startup...
) else (
    echo     ✓ All dependencies installed successfully
)
echo.

REM Start API Server
echo [4/5] Starting FastAPI Backend Server...
echo     ➤ API will be available at: http://localhost:8001
echo     ➤ API Documentation at: http://localhost:8001/docs
start "Association Mining API Server" cmd /k "title Association Mining API && echo Starting API Server... && %PYTHON_CMD% -m uvicorn app.main:app --host 0.0.0.0 --port 8001"

REM Wait for API to start
echo     ➤ Waiting for API server to initialize...
timeout /t 5 /nobreak >nul

REM Start UI Server
echo [5/5] Starting Flask UI Server...
echo     ➤ Dashboard will be available at: http://localhost:5000
start "Association Mining UI Server" cmd /k "title Association Mining Dashboard && echo Starting UI Server... && %PYTHON_CMD% flask_ui_enhanced.py"

REM Wait for UI to start
timeout /t 3 /nobreak >nul

echo.
echo ================================================================
echo              🚀 SYSTEM STARTED SUCCESSFULLY! 🚀
echo ================================================================
echo.
echo 📊 Main Dashboard:       http://localhost:5000
echo 🔧 API Documentation:    http://localhost:8001/docs
echo 📈 API Endpoints:        http://localhost:8001
echo.
echo 🖥️  Two console windows have been opened:
echo     1. Association Mining API (FastAPI) - Port 8001
echo     2. Association Mining Dashboard (Flask) - Port 5000
echo.
echo 🛑 To stop the system:
echo     • Close both console windows, or
echo     • Press Ctrl+C in each console window
echo.
echo 📋 Next Steps:
echo     1. Open http://localhost:5000 in your browser
echo     2. Configure your database connection
echo     3. Test the connection
echo     4. Start mining!
echo.
echo 🎉 Happy Mining!
echo ================================================================
echo.
echo Press any key to open the dashboard in your default browser...
pause >nul

REM Open dashboard in browser
start http://localhost:5000

echo.
echo Dashboard opened! You can close this window now.
timeout /t 3 >nul