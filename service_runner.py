"""
Simple service runner that starts both servers
This runs the servers directly without Windows service complexity
"""
import subprocess
import time
import sys
from pathlib import Path
import logging

# Setup logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "service_runner.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Run both servers"""
    project_dir = Path(__file__).parent
    python_exe = project_dir / "venv" / "Scripts" / "python.exe"
    
    if not python_exe.exists():
        logger.error(f"Python not found at {python_exe}")
        return
    
    # Open log files
    fastapi_log = open(log_dir / "fastapi.log", "a", encoding='utf-8')
    flask_log = open(log_dir / "flask.log", "a", encoding='utf-8')
    
    try:
        logger.info("=" * 60)
        logger.info("Starting Association Mining System Servers")
        logger.info("=" * 60)
        
        # Start FastAPI
        logger.info("Starting FastAPI server on port 8080...")
        fastapi_process = subprocess.Popen(
            [str(python_exe), "-m", "uvicorn", "app.main:app", 
             "--host", "0.0.0.0", "--port", "8080"],
            cwd=str(project_dir),
            stdout=fastapi_log,
            stderr=fastapi_log
        )
        logger.info(f"FastAPI started (PID: {fastapi_process.pid})")
        
        # Wait a bit
        time.sleep(3)
        
        # Start Flask
        logger.info("Starting Flask UI server on port 5000...")
        flask_process = subprocess.Popen(
            [str(python_exe), "-m", "flask", 
             "--app", "app.web.main:app", "run",
             "--host", "0.0.0.0", "--port", "5000"],
            cwd=str(project_dir),
            stdout=flask_log,
            stderr=flask_log
        )
        logger.info(f"Flask started (PID: {flask_process.pid})")
        
        logger.info("=" * 60)
        logger.info("All servers started successfully!")
        logger.info("FastAPI: http://localhost:8080")
        logger.info("Flask UI: http://localhost:5000")
        logger.info("=" * 60)
        
        # Keep running and monitor processes
        while True:
            time.sleep(10)
            
            # Check if processes are still running
            if fastapi_process.poll() is not None:
                logger.error("FastAPI process died!")
                break
                
            if flask_process.poll() is not None:
                logger.error("Flask process died!")
                break
                
    except KeyboardInterrupt:
        logger.info("Shutdown requested...")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        # Cleanup
        logger.info("Stopping servers...")
        try:
            fastapi_process.terminate()
            flask_process.terminate()
            fastapi_process.wait(timeout=10)
            flask_process.wait(timeout=10)
        except:
            pass
        
        fastapi_log.close()
        flask_log.close()
        logger.info("Shutdown complete")

if __name__ == "__main__":
    main()
