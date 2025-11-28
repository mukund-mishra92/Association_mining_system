@echo off
REM Batch file to run both servers for Windows Service

cd /d "%~dp0"

REM Start FastAPI in background
start /B "" "%~dp0venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8080 >> logs\fastapi.log 2>&1

REM Wait a bit
timeout /t 3 /nobreak >nul

REM Start Flask in background  
start /B "" "%~dp0venv\Scripts\python.exe" -m flask --app app.web.main:app run --host 0.0.0.0 --port 5000 >> logs\flask.log 2>&1

REM Keep the batch file running
:loop
timeout /t 60 /nobreak >nul
goto loop
