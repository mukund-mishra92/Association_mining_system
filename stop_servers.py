"""
Association Mining System - Server Stopper
Stops FastAPI and Flask servers and closes their console windows
"""
import sys
import subprocess
from pathlib import Path

def kill_processes_on_port(port, port_name):
    """Kill all processes using a specific port and their entire process tree"""
    killed_count = 0
    
    try:
        # Use netstat to find all processes on the port
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True,
            text=True,
            check=False
        )
        
        pids = set()
        for line in result.stdout.split('\n'):
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.split()
                if parts and parts[-1].isdigit():
                    pids.add(parts[-1])
        
        if not pids:
            print(f"  ℹ️  No processes found on port {port}")
            return 0
        
        print(f"  Found {len(pids)} process(es) on port {port}")
        
        # Kill each process tree using taskkill /T (kills tree)
        for pid in pids:
            print(f"  Killing process tree PID {pid}...")
            result = subprocess.run(
                ['taskkill', '/F', '/T', '/PID', pid],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                print(f"  ✅ Killed process tree {pid}")
                killed_count += 1
            else:
                # Process might already be dead
                if "not found" not in result.stderr.lower():
                    print(f"  ⚠️  Could not kill PID {pid}: {result.stderr.strip()}")
        
        return killed_count
        
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
        return 0

def stop_servers():
    """Stop all running servers"""
    project_dir = Path(__file__).parent
    pid_file = project_dir / ".server_pids"
    
    print("\n" + "="*60)
    print("  Association Mining System - Server Stopper")
    print("="*60)
    print()
    
    total_killed = 0
    
    # Method 1: Stop using saved PIDs (from background start)
    if pid_file.exists():
        print("📄 Stopping saved background processes...")
        try:
            with open(pid_file, "r") as f:
                pids = [line.strip() for line in f if line.strip().isdigit()]
            
            for pid in pids:
                print(f"  Killing process tree PID {pid}...")
                result = subprocess.run(
                    ['taskkill', '/F', '/T', '/PID', pid],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0:
                    print(f"  ✅ Killed process tree {pid}")
                    total_killed += 1
            
            # Clean up PID file
            pid_file.unlink()
            print("  🗑️  Cleaned up PID file")
            print()
        except Exception as e:
            print(f"  ⚠️  Error: {e}\n")
    
    # Method 2: Kill by port (catches servers started any way)
    print("🔍 Stopping processes on server ports...")
    print()
    
    ports_to_check = [
        (8080, "FastAPI"),
        (5000, "Flask UI")
    ]
    
    for port, name in ports_to_check:
        print(f"Checking port {port} ({name})...")
        killed = kill_processes_on_port(port, name)
        total_killed += killed
        print()
    
    # Method 3: Kill console windows running our servers
    print("🔍 Closing server console windows...")
    try:
        # Find cmd.exe windows running python from our venv
        result = subprocess.run(
            ['wmic', 'process', 'where', 
             "name='cmd.exe' or name='python.exe' or name='conhost.exe'",
             'get', 'ProcessId,CommandLine'],
            capture_output=True,
            text=True,
            check=False
        )
        
        console_killed = 0
        keywords = ['uvicorn', 'app.main', 'association_mining_system']
        
        for line in result.stdout.split('\n'):
            if any(keyword in line.lower() for keyword in keywords):
                # Extract PID from the line
                parts = line.split()
                if parts and parts[-1].isdigit():
                    pid = parts[-1]
                    print(f"  Closing console window PID {pid}...")
                    subprocess.run(
                        ['taskkill', '/F', '/T', '/PID', pid],
                        capture_output=True,
                        check=False
                    )
                    console_killed += 1
        
        if console_killed > 0:
            print(f"  ✅ Closed {console_killed} console window(s)")
            total_killed += console_killed
        else:
            print("  ℹ️  No console windows found")
            
    except Exception as e:
        print(f"  ⚠️  Error checking console windows: {e}")
    
    print()
    print("="*60)
    if total_killed > 0:
        print(f"✅ Successfully stopped {total_killed} process(es)")
        print()
        print("NOTE: You may still see connections in netstat for a few")
        print("seconds. These are orphaned TCP connections in TIME_WAIT")
        print("state and will be cleaned up automatically by Windows.")
    else:
        print("ℹ️  No running server processes found")
    print("="*60)
    print()

if __name__ == "__main__":
    try:
        stop_servers()
    except KeyboardInterrupt:
        print("\n\nStopping interrupted...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error stopping servers: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    input("Press Enter to exit...")
