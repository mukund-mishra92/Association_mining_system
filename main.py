#!/usr/bin/env python3
"""
Association Mining System - Main Entry Point

This is the main entry point for the Association Mining System.
It provides a unified interface to launch different modules:
- Association Rule Mining
- SKU Analysis (Fast/Slow Moving)
- Web Interface

Usage:
    python main.py [module] [options]

Modules:
    web         - Start the web interface (default)
    api         - Start the FastAPI backend
    mining      - Start association rule mining
    sku         - Start SKU analysis
    all         - Start all services

Examples:
    python main.py                 # Start web interface
    python main.py web             # Start web interface
    python main.py api             # Start FastAPI backend
    python main.py all             # Start all services
"""

import sys
import os
import argparse
import subprocess
import time
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

def get_python_executable():
    """Get the appropriate Python executable, preferring virtual environment"""
    venv_python = Path(".venv/Scripts/python.exe")
    if venv_python.exists():
        print("🐍 Using virtual environment Python")
        return str(venv_python)
    else:
        print("🐍 Using system Python")
        return sys.executable

def start_web_interface():
    """Start the Flask web interface"""
    print("🌐 Starting Web Interface...")
    print("📍 URL: http://localhost:5000")
    
    python_exe = get_python_executable()
    os.chdir(Path(__file__).parent)
    subprocess.run([python_exe, "-m", "app.web.main"])

def start_api_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting FastAPI Backend...")
    print("📍 URL: http://localhost:8001")
    print("📍 API Docs: http://localhost:8001/docs")
    
    python_exe = get_python_executable()
    os.chdir(Path(__file__).parent)
    subprocess.run([python_exe, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"])

def start_all_services():
    """Start all services"""
    print("🎯 Starting All Services...")
    print()
    
    python_exe = get_python_executable()
    
    # Start FastAPI in background
    print("🚀 Starting FastAPI Backend...")
    fastapi_process = subprocess.Popen([
        python_exe, "-m", "uvicorn", 
        "app.main:app", "--host", "0.0.0.0", "--port", "8001"
    ])
    
    # Wait a moment for FastAPI to start
    time.sleep(3)
    
    # Start Flask web interface
    print("🌐 Starting Web Interface...")
    flask_process = subprocess.Popen([
        python_exe, "-m", "app.web.main"
    ])
    
    print()
    print("=" * 50)
    print("🎉 All Services Started!")
    print("=" * 50)
    print("🌐 Web Interface:  http://localhost:5000")
    print("🚀 FastAPI Backend: http://localhost:8001") 
    print("📚 API Docs:       http://localhost:8001/docs")
    print()
    print("Press Ctrl+C to stop all services")
    print("=" * 50)
    
    try:
        # Wait for processes
        fastapi_process.wait()
        flask_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        fastapi_process.terminate()
        flask_process.terminate()
        print("✅ All services stopped")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Association Mining System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        'module',
        nargs='?',
        default='web',
        choices=['web', 'api', 'all'],
        help='Module to start (default: web)'
    )
    
    args = parser.parse_args()
    
    print("🔗 Association Mining System")
    print("=" * 40)
    
    if args.module == 'web':
        start_web_interface()
    elif args.module == 'api':
        start_api_backend()
    elif args.module == 'all':
        start_all_services()
    else:
        print(f"❌ Unknown module: {args.module}")
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()