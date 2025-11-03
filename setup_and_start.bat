@echo off
REM ========================================
REM Association Mining System - Full Setup
REM For NEW system installations
REM ========================================

echo.
echo ========================================
echo  Association Mining System Setup
echo  Full Installation Script
echo ========================================
echo.

REM Check Python installation
echo [1/7] Checking Python installation...
py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo Please install Python 3.10 or higher from python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

py --version
echo Python found successfully!
echo.

REM Check if virtual environment exists
echo [2/7] Checking virtual environment...
if exist "venv\Scripts\activate.bat" (
    echo Virtual environment already exists.
    choice /C YN /M "Do you want to recreate it"
    if errorlevel 2 goto SkipVenvCreation
    if errorlevel 1 (
        echo Removing old virtual environment...
        rmdir /s /q venv
    )
)

echo Creating virtual environment...
py -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo Virtual environment created successfully!

:SkipVenvCreation
echo.

REM Activate virtual environment
echo [3/7] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo Virtual environment activated!
echo.

REM Upgrade pip
echo [4/7] Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install requirements
echo [5/7] Installing dependencies...
echo This may take a few minutes...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully!
echo.

REM Check .env file
echo [6/7] Checking configuration...
if not exist ".env" (
    echo WARNING: .env file not found!
    echo.
    echo Please create a .env file with your database configuration:
    echo   - Copy .env.example to .env (if available)
    echo   - Or manually create .env with required settings
    echo.
    echo Required settings:
    echo   DB_HOST=your_database_host
    echo   DB_USER=your_database_user
    echo   DB_PASSWORD=your_database_password
    echo   DB_NAME=your_database_name
    echo   DB_PORT=3306
    echo.
    echo   MIN_SUPPORT=0.05
    echo   MIN_CONFIDENCE=0.25
    echo   MIN_LIFT=1.0
    echo   MAX_RECOMMENDATIONS=10
    echo   MAX_ITEMS=400
    echo   MIN_ITEM_FREQUENCY=5
    echo.
    pause
    exit /b 1
)
echo Configuration file found!
echo.

REM Setup database tables
echo [7/7] Setting up database tables...
echo.
choice /C YN /M "Do you want to run database table migration now"
if errorlevel 2 goto SkipMigration
if errorlevel 1 (
    echo Running migration script...
    python migrate_scheduler_tables.py
    if %errorlevel% neq 0 (
        echo WARNING: Migration failed. You may need to run it manually later.
    ) else (
        echo Migration completed successfully!
    )
)

:SkipMigration
echo.

REM Setup complete
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo Starting servers...
echo.

REM Start servers
echo [Starting] FastAPI on port 8080...
start "Association Mining - FastAPI" cmd /k "cd /d %~dp0 && call venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload"

timeout /t 3 /nobreak >nul

echo [Starting] Flask UI on port 5000...
start "Association Mining - Flask UI" cmd /k "cd /d %~dp0 && call venv\Scripts\activate.bat && python app\web\main.py"

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo  Both servers are starting!
echo ========================================
echo.
echo Flask UI:  http://localhost:5000
echo FastAPI:   http://localhost:8080
echo API Docs:  http://localhost:8080/docs
echo.
echo Two new command windows have opened.
echo Close those windows to stop the servers.
echo ========================================
echo.
echo Setup and startup complete!
echo You can close this window now.
echo.
pause
