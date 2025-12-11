"""
Start servers in background without visible command windows
"""
import subprocess
import sys
import time
from pathlib import Path

def start_background():
    """Start FastAPI and Flask servers in background"""
    project_dir = Path(__file__).parent
    python_exe = project_dir / "venv" / "Scripts" / "python.exe"
    logs_dir = project_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Open log files
    fastapi_log = open(logs_dir / "fastapi_background.log", "w", encoding="utf-8")
    flask_log = open(logs_dir / "flask_background.log", "w", encoding="utf-8")
    
    # Start FastAPI server in background
    print("Starting FastAPI server in background...")
    fastapi_proc = subprocess.Popen(
        [str(python_exe), "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"],
        cwd=str(project_dir),
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
        stdout=fastapi_log,
        stderr=subprocess.STDOUT
    )
    
    # Wait a moment for FastAPI to start
    time.sleep(2)
    
    # Start Flask UI server in background
    print("Starting Flask UI server in background...")
    flask_proc = subprocess.Popen(
        [str(python_exe), str(project_dir / "test_flask.py")],
        cwd=str(project_dir),
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
        stdout=flask_log,
        stderr=subprocess.STDOUT
    )
    
    print("\n" + "="*50)
    print("Servers started in background!")
    print("="*50)
    print("\nAccess points:")
    print("  Flask UI:  http://localhost:5000")
    print("  FastAPI:   http://localhost:8080")
    print("  API Docs:  http://localhost:8080/docs")
    print("\nServers are running in background (no visible windows)")
    print("To stop: run stop_servers.bat")
    print("="*50)

if __name__ == "__main__":
    start_background()
