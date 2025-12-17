"""
Association Mining System - Quick Start Script
Starts FastAPI and Flask servers with visible terminal windows
"""
import subprocess
import sys
import time
from pathlib import Path

def check_setup():
    """Check if system is properly set up"""
    project_dir = Path(__file__).parent
    
    # Check virtual environment
    venv_python = project_dir / "venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        print("❌ ERROR: Virtual environment not found!")
        print("\nThis appears to be a new installation.")
        print("Please set up the virtual environment first:")
        print("  1. python -m venv venv")
        print("  2. venv\\Scripts\\activate")
        print("  3. pip install -r requirements.txt")
        return False
    
    # Check .env file
    env_file = project_dir / ".env"
    if not env_file.exists():
        print("❌ ERROR: Configuration file (.env) not found!")
        print("\nPlease create .env file with your database configuration.")
        print("See .env.example for required settings.")
        return False
    
    return True

def start_servers():
    """Start FastAPI and Flask servers"""
    project_dir = Path(__file__).parent
    python_exe = project_dir / "venv" / "Scripts" / "python.exe"
    
    print("\n" + "="*60)
    print("  Association Mining System - Quick Start")
    print("="*60)
    print()
    
    if not check_setup():
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    print("Starting servers...\n")
    
    # Start FastAPI server in new window
    print("[1/2] Starting FastAPI server on port 8080...")
    fastapi_cmd = [
        str(python_exe), "-m", "uvicorn", 
        "app.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8080",
        "--reload"
    ]
    
    subprocess.Popen(
        fastapi_cmd,
        cwd=str(project_dir),
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
    )
    
    time.sleep(3)
    
    # Start Flask UI server in new window
    print("[2/2] Starting Flask UI server on port 5000...")
    flask_cmd = [str(python_exe), str(project_dir / "app" / "web" / "main.py")]
    
    subprocess.Popen(
        flask_cmd,
        cwd=str(project_dir),
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
    )
    
    time.sleep(2)
    
    print("\n" + "="*60)
    print("✅ Servers started successfully!")
    print("="*60)
    print("\nAccess points:")
    print("  🌐 Flask UI:  http://localhost:5000")
    print("  🚀 FastAPI:   http://localhost:8080")
    print("  📚 API Docs:  http://localhost:8080/docs")
    print("\nServers are running in separate windows.")
    print("Close the terminal windows to stop the servers.")
    print("="*60)
    print()
    input("Press Enter to exit this launcher...")

if __name__ == "__main__":
    try:
        start_servers()
    except KeyboardInterrupt:
        print("\n\nShutdown requested...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting servers: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)
