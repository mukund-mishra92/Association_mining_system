@echo off
echo ================================================================
echo   Starting Flask Server for Testing
echo ================================================================
echo.
echo This will start the server. Keep this window open.
echo Open a NEW terminal window and run: test_services_validation.py
echo.
echo Press Ctrl+C to stop the server when done testing.
echo ================================================================
echo.

cd /d "%~dp0"
.\.venv\Scripts\python.exe quick_start.py

pause
