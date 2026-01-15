"""
Association Mining System - Background Server Launcher
Starts FastAPI and Flask servers in background without visible windows
"""
import subprocess
import sys
import time
from pathlib import Path

def check_setup():
    """Check if system is properly set up"""
    project_dir = Path(__file__).parent
    
    # Check for venv or .venv
    venv_dirs = ["venv", ".venv"]
    venv_python = None
    for venv_name in venv_dirs:
        candidate = project_dir / venv_name / "Scripts" / "python.exe"
        if candidate.exists():
            venv_python = candidate
            break
    if not venv_python:
        print("❌ ERROR: Virtual environment not found!")
        print("\nPlease set up the virtual environment first:")
        print("  1. python -m venv venv   OR   python -m venv .venv")
        print("  2. venv\\Scripts\\activate   OR   .venv\\Scripts\\activate")
        print("  3. pip install -r requirements.txt")
        return False
    
    # Check .env file
    env_file = project_dir / ".env"
    if not env_file.exists():
        print("❌ ERROR: Configuration file (.env) not found!")
        print("\nPlease create .env file. See .env.example for required settings.")
        return False
    
    return True

def start_background():
    """Start FastAPI and Flask servers in background"""
    project_dir = Path(__file__).parent
    # Find python.exe in venv or .venv
    venv_dirs = ["venv", ".venv"]
    python_exe = None
    for venv_name in venv_dirs:
        candidate = project_dir / venv_name / "Scripts" / "python.exe"
        if candidate.exists():
            python_exe = candidate
            break
    if not python_exe:
        print("❌ ERROR: Virtual environment not found!")
        sys.exit(1)
    logs_dir = project_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    print("\n" + "="*60)
    print("  Association Mining System - Background Start")
    print("="*60)
    print()
    
    if not check_setup():
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # Open log files
    fastapi_log = open(logs_dir / "fastapi_background.log", "w", encoding="utf-8")
    flask_log = open(logs_dir / "flask_background.log", "w", encoding="utf-8")
    
    # Start FastAPI server in background
    print("🚀 Starting FastAPI server in background...")
    fastapi_proc = subprocess.Popen(
        [str(python_exe), "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"],
        cwd=str(project_dir),
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
        stdout=fastapi_log,
        stderr=subprocess.STDOUT
    )
    
    # Wait for FastAPI to start
    time.sleep(3)
    
    # Start Flask UI server in background
    print("🌐 Starting Flask UI server in background...")
    flask_proc = subprocess.Popen(
        [str(python_exe), str(project_dir / "app" / "web" / "main.py")],
        cwd=str(project_dir),
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
        stdout=flask_log,
        stderr=subprocess.STDOUT
    )
    
    time.sleep(2)
    
    print("\n" + "="*60)
    print("✅ Servers started in background!")
    print("="*60)
    print("\nAccess points:")
    print("  🌐 Flask UI:  http://localhost:5000")
    print("  🚀 FastAPI:   http://localhost:8080")
    print("  📚 API Docs:  http://localhost:8080/docs")
    print("\n📝 Log files:")
    print(f"  FastAPI: logs\\fastapi_background.log")
    print(f"  Flask:   logs\\flask_background.log")
    print("\nServers are running in background (no visible windows)")
    print("="*60)
    
    # Save PIDs for later cleanup
    pid_file = project_dir / ".server_pids"
    with open(pid_file, "w") as f:
        f.write(f"{fastapi_proc.pid}\n{flask_proc.pid}")
    
    print(f"\nPIDs saved to: .server_pids")
    print("To stop servers: Use Task Manager or kill processes")
    print()
    input("Press Enter to exit this launcher...")

if __name__ == "__main__":
    try:
        start_background()
    except KeyboardInterrupt:
        print("\n\nShutdown requested...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting servers: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)
