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
        self.run_script = self.project_dir / "run_servers.py"
        
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
            # Use the unified server script to start servers
            logger.info(f"Executing: {self.python_exe} {self.run_script} start")
            subprocess.Popen(
                [self.python_exe, str(self.run_script), "start"],
                cwd=str(self.project_dir),
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            logger.info("✓ Server start command issued.")
            
            # Keep the service alive
            while self.running:
                rc = win32event.WaitForSingleObject(self.stop_event, 5000)
                if rc == win32event.WAIT_OBJECT_0:
                    break
                    
        except Exception as e:
            logger.error(f"Service error: {e}", exc_info=True)
            servicemanager.LogErrorMsg(f"Service error: {e}")
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Clean up resources and stop processes"""
        logger.info("Cleaning up service resources...")
        try:
            # Use the unified server script to stop servers
            logger.info(f"Executing: {self.python_exe} {self.run_script} stop")
            subprocess.run(
                [self.python_exe, str(self.run_script), "stop"],
                cwd=str(self.project_dir),
                check=True,
                capture_output=True
            )
            logger.info("✓ Server stop command issued and completed.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stop servers: {e.stderr.decode(errors='ignore')}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during cleanup: {e}")
            
        logger.info("Service cleanup complete")


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(AssociationMiningService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(AssociationMiningService)
