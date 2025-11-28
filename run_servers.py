
import subprocess
import os
import sys
import time
import json
from pathlib import Path

# Get project directory and python executable
PROJECT_DIR = Path(__file__).parent
PYTHON_EXE = sys.executable
PID_FILE = PROJECT_DIR / "running_service.txt"

def get_pids():
    """Reads PID file and returns a dictionary of PIDs"""
    if not PID_FILE.exists():
        return {}
    with open(PID_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_pids(pids):
    """Saves a dictionary of PIDs to the PID file"""
    with open(PID_FILE, 'w') as f:
        json.dump(pids, f)

def start_servers():
    """Starts the FastAPI and Flask servers."""
    print("="*60)
    print("Starting Association Mining System Servers...")
    print("="*60)
    
    pids = get_pids()
    
    # Start FastAPI server
    if "fastapi_pid" not in pids:
        print("Starting FastAPI server on port 8080...")
        fastapi_process = subprocess.Popen(
            [
                PYTHON_EXE, "-m", "uvicorn", "app.main:app",
                "--host", "0.0.0.0", "--port", "8080"
            ],
            cwd=str(PROJECT_DIR),
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        pids["fastapi_pid"] = fastapi_process.pid
        print(f"✓ FastAPI server started (PID: {fastapi_process.pid})")
    else:
        print("FastAPI server already running.")

    # Start Flask UI server
    if "flask_pid" not in pids:
        print("Starting Flask UI server on port 5000...")
        flask_process = subprocess.Popen(
            [
                PYTHON_EXE, "-m", "flask", "--app", "app.web.main:app",
                "run", "--host", "0.0.0.0", "--port", "5000"
            ],
            cwd=str(PROJECT_DIR),
            env={**os.environ, "FLASK_ENV": "production"},
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        pids["flask_pid"] = flask_process.pid
        print(f"✓ Flask UI server started (PID: {flask_process.pid})")
    else:
        print("Flask UI server already running.")
        
    save_pids(pids)
    print("\nAll servers are running.")
    print("FastAPI: http://localhost:8080")
    print("Flask UI: http://localhost:5000")

def stop_servers():
    """Stops the FastAPI and Flask servers."""
    print("="*60)
    print("Stopping Association Mining System Servers...")
    print("="*60)
    
    pids = get_pids()
    if not pids:
        print("No running processes found in PID file.")
        return

    for name, pid in pids.items():
        try:
            # Use taskkill on Windows to gracefully terminate
            print(f"Stopping {name} (PID: {pid})...")
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=True, capture_output=True)
            print(f"✓ {name} stopped.")
        except subprocess.CalledProcessError as e:
            if "not found" in e.stderr.decode(errors='ignore'):
                print(f"Process with PID {pid} not found. It may have already been stopped.")
            else:
                print(f"Failed to stop {name} (PID: {pid}): {e.stderr.decode(errors='ignore')}")
        except Exception as e:
            print(f"An unexpected error occurred while stopping {name}: {e}")

    # Clear the PID file
    if PID_FILE.exists():
        os.remove(PID_FILE)
    print("\nAll servers stopped.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "start":
            start_servers()
        elif command == "stop":
            stop_servers()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python run_servers.py [start|stop]")
    else:
        print("Usage: python run_servers.py [start|stop]")

