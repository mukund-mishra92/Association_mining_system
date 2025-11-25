"""
Windows Service for Association Mining System
Runs FastAPI server and Scheduler in background as a Windows Service
"""

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import time
import subprocess
import logging
from pathlib import Path

# Setup logging
log_file = Path(__file__).parent / "logs" / "service.log"
log_file.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AssociationMiningService(win32serviceutil.ServiceFramework):
    """Windows Service for Association Mining System"""
    
    _svc_name_ = "AssociationMiningService"
    _svc_display_name_ = "Association Mining System Service"
    _svc_description_ = "Runs the Association Mining System FastAPI server and scheduler in background"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
        
        # Get the project directory
        self.project_dir = Path(__file__).parent
        self.python_exe = sys.executable
        
        # Process handles
        self.fastapi_process = None
        self.flask_process = None
        
    def SvcStop(self):
        """Stop the service"""
        logger.info("Service stop requested")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False
        
    def SvcDoRun(self):
        """Run the service"""
        logger.info("="*60)
        logger.info("Association Mining Service Starting")
        logger.info("="*60)
        
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        self.main()
        
    def main(self):
        """Main service logic"""
        try:
            # Start FastAPI server
            logger.info("Starting FastAPI server on port 8080...")
            self.fastapi_process = subprocess.Popen(
                [
                    self.python_exe,
                    "-m",
                    "uvicorn",
                    "app.main:app",
                    "--host", "0.0.0.0",
                    "--port", "8080",
                    "--reload"
                ],
                cwd=str(self.project_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            logger.info(f"✓ FastAPI server started (PID: {self.fastapi_process.pid})")
            
            # Wait a moment for FastAPI to start
            time.sleep(3)
            
            # Start Flask UI server
            logger.info("Starting Flask UI server on port 5000...")
            self.flask_process = subprocess.Popen(
                [
                    self.python_exe,
                    "-m",
                    "flask",
                    "--app", "app.web.main:app",
                    "run",
                    "--host", "0.0.0.0",
                    "--port", "5000"
                ],
                cwd=str(self.project_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**os.environ, "FLASK_ENV": "production"},
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            logger.info(f"✓ Flask UI server started (PID: {self.flask_process.pid})")
            
            logger.info("="*60)
            logger.info("All servers started successfully!")
            logger.info("FastAPI: http://localhost:8080")
            logger.info("Flask UI: http://localhost:5000")
            logger.info("="*60)
            
            # Keep the service running and monitor processes
            while self.running:
                # Check if processes are still running
                if self.fastapi_process.poll() is not None:
                    logger.error("FastAPI process died! Restarting...")
                    self.start_fastapi()
                    
                if self.flask_process.poll() is not None:
                    logger.error("Flask process died! Restarting...")
                    self.start_flask()
                
                # Wait for stop signal or timeout
                rc = win32event.WaitForSingleObject(self.stop_event, 5000)
                if rc == win32event.WAIT_OBJECT_0:
                    break
                    
        except Exception as e:
            logger.error(f"Service error: {e}", exc_info=True)
            servicemanager.LogErrorMsg(f"Service error: {e}")
        finally:
            self.cleanup()
            
    def start_fastapi(self):
        """Start or restart FastAPI server"""
        try:
            if self.fastapi_process and self.fastapi_process.poll() is None:
                self.fastapi_process.terminate()
                self.fastapi_process.wait(timeout=5)
                
            self.fastapi_process = subprocess.Popen(
                [
                    self.python_exe,
                    "-m",
                    "uvicorn",
                    "app.main:app",
                    "--host", "0.0.0.0",
                    "--port", "8080"
                ],
                cwd=str(self.project_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            logger.info(f"✓ FastAPI server (re)started (PID: {self.fastapi_process.pid})")
        except Exception as e:
            logger.error(f"Failed to start FastAPI: {e}")
            
    def start_flask(self):
        """Start or restart Flask server"""
        try:
            if self.flask_process and self.flask_process.poll() is None:
                self.flask_process.terminate()
                self.flask_process.wait(timeout=5)
                
            self.flask_process = subprocess.Popen(
                [
                    self.python_exe,
                    "-m",
                    "flask",
                    "--app", "app.web.main:app",
                    "run",
                    "--host", "0.0.0.0",
                    "--port", "5000"
                ],
                cwd=str(self.project_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**os.environ, "FLASK_ENV": "production"},
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            logger.info(f"✓ Flask server (re)started (PID: {self.flask_process.pid})")
        except Exception as e:
            logger.error(f"Failed to start Flask: {e}")
            
    def cleanup(self):
        """Clean up resources and stop processes"""
        logger.info("Cleaning up service resources...")
        
        # Stop FastAPI
        if self.fastapi_process:
            try:
                logger.info("Stopping FastAPI server...")
                self.fastapi_process.terminate()
                self.fastapi_process.wait(timeout=10)
                logger.info("✓ FastAPI server stopped")
            except Exception as e:
                logger.error(f"Error stopping FastAPI: {e}")
                try:
                    self.fastapi_process.kill()
                except:
                    pass
                    
        # Stop Flask
        if self.flask_process:
            try:
                logger.info("Stopping Flask server...")
                self.flask_process.terminate()
                self.flask_process.wait(timeout=10)
                logger.info("✓ Flask server stopped")
            except Exception as e:
                logger.error(f"Error stopping Flask: {e}")
                try:
                    self.flask_process.kill()
                except:
                    pass
                    
        logger.info("Service cleanup complete")


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(AssociationMiningService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(AssociationMiningService)
