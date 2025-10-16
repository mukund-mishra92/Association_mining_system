1. Kill all python processes (Cleanup)


taskkill /F /IM python.exe /T 2>$null; taskkill /F /IM py.exe /T 2>$null; Get-Process python* -ErrorAction SilentlyContinue | Stop-Process -Force


2. Start the Fast API Server

py -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload


3. Start the Flask UI Server

py flask_ui_enhanced.py