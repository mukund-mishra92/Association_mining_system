@echo off
REM Universal Python Command Wrapper
REM This file ensures your system uses the correct Python command

REM Try py command first (Windows Python Launcher)
py --version >nul 2>&1
if not errorlevel 1 (
    py %*
    exit /b %errorlevel%
)

REM Fallback to python command
python --version >nul 2>&1
if not errorlevel 1 (
    python %*
    exit /b %errorlevel%
)

REM Fallback to python3 command
python3 --version >nul 2>&1
if not errorlevel 1 (
    python3 %*
    exit /b %errorlevel%
)

REM If none work, show error
echo Error: Python is not installed or not in PATH
echo.
echo Please install Python from:
echo   - python.org
echo   - Microsoft Store  
echo   - Or ensure Python is added to your system PATH
echo.
pause
exit /b 1