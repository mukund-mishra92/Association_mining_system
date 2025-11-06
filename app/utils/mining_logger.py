"""
Enhanced Logging System for Association Mining System
Tracks all user operations, system events, and results
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import threading
from pathlib import Path

class AssociationMiningLogger:
    """Enhanced logger for tracking all operations in the system"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup different log files
        self.setup_loggers()
        
        # In-memory log storage for quick access
        self.recent_logs = []
        self.max_recent_logs = 1000
        self.lock = threading.Lock()
    
    def setup_loggers(self):
        """Setup different types of loggers"""
        
        # Main system logger
        self.system_logger = self._create_logger(
            'system', 
            self.log_dir / 'system.log',
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # User operations logger
        self.operations_logger = self._create_logger(
            'operations',
            self.log_dir / 'operations.log', 
            '%(asctime)s - %(message)s'
        )
        
        # Results logger
        self.results_logger = self._create_logger(
            'results',
            self.log_dir / 'results.log',
            '%(asctime)s - %(message)s'
        )
        
        # Error logger
        self.error_logger = self._create_logger(
            'errors',
            self.log_dir / 'errors.log',
            '%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def _create_logger(self, name: str, file_path: Path, format_str: str) -> logging.Logger:
        """Create a logger with file handler"""
        logger = logging.getLogger(f"association_mining.{name}")
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        if logger.handlers:
            logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(format_str)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def log_operation(self, operation: str, details: Dict[str, Any], user_id: str = "system"):
        """Log a user operation"""
        timestamp = datetime.now()
        
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "operation": operation,
            "user_id": user_id,
            "details": details,
            "status": details.get("status", "unknown")
        }
        
        # Log to file
        self.operations_logger.info(json.dumps(log_entry, indent=2))
        
        # Add to recent logs
        with self.lock:
            self.recent_logs.append(log_entry)
            if len(self.recent_logs) > self.max_recent_logs:
                self.recent_logs.pop(0)
        
        return log_entry
    
    def log_database_connection(self, config: Dict[str, Any], success: bool, error: str = None):
        """Log database connection attempts"""
        details = {
            "type": "database_connection",
            "config": {
                "host": config.get("host"),
                "port": config.get("port"),
                "database": config.get("database"),
                "user": config.get("user")
                # Never log passwords
            },
            "status": "success" if success else "failed",
            "error": error
        }
        return self.log_operation("Database Connection Test", details)
    
    def log_mining_operation(self, mining_type: str, parameters: Dict[str, Any], 
                           results: Dict[str, Any] = None, success: bool = True, error: str = None):
        """Log association mining operations"""
        details = {
            "type": "mining_operation",
            "mining_type": mining_type,
            "parameters": parameters,
            "results": results,
            "status": "success" if success else "failed",
            "error": error
        }
        return self.log_operation(f"Association Mining - {mining_type}", details)
    
    def log_velocity_analysis(self, operation: str, parameters: Dict[str, Any],
                            results: Dict[str, Any] = None, success: bool = True, error: str = None):
        """Log velocity analysis operations"""
        details = {
            "type": "velocity_analysis",
            "operation": operation,
            "parameters": parameters,
            "results": results,
            "status": "success" if success else "failed",
            "error": error
        }
        return self.log_operation(f"Velocity Analysis - {operation}", details)
    
    def log_config_change(self, config_type: str, old_config: Dict[str, Any], 
                         new_config: Dict[str, Any], user_id: str = "system"):
        """Log configuration changes"""
        details = {
            "type": "config_change",
            "config_type": config_type,
            "old_config": old_config,
            "new_config": new_config,
            "status": "success"
        }
        return self.log_operation(f"Configuration Change - {config_type}", details, user_id)
    
    def log_error(self, operation: str, error: str, details: Dict[str, Any] = None):
        """Log errors"""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "error": error,
            "details": details or {}
        }
        
        self.error_logger.error(json.dumps(error_entry, indent=2))
        
        # Also log as operation
        error_details = {
            "type": "error",
            "error": error,
            "details": details or {},
            "status": "error"
        }
        return self.log_operation(f"Error - {operation}", error_details)
    
    def get_recent_logs(self, limit: int = 100, operation_type: str = None) -> List[Dict[str, Any]]:
        """Get recent logs"""
        with self.lock:
            logs = self.recent_logs.copy()
        
        # Filter by operation type if specified
        if operation_type:
            logs = [log for log in logs if log.get("details", {}).get("type") == operation_type]
        
        # Return most recent logs
        return sorted(logs, key=lambda x: x["timestamp"], reverse=True)[:limit]
    
    def get_logs_by_date(self, date_str: str) -> List[Dict[str, Any]]:
        """Get logs for a specific date (YYYY-MM-DD)"""
        with self.lock:
            date_logs = [
                log for log in self.recent_logs 
                if log["timestamp"].startswith(date_str)
            ]
        return sorted(date_logs, key=lambda x: x["timestamp"], reverse=True)
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Get logging statistics"""
        with self.lock:
            total_logs = len(self.recent_logs)
            
            # Count by operation type
            type_counts = {}
            status_counts = {"success": 0, "failed": 0, "error": 0}
            
            for log in self.recent_logs:
                log_type = log.get("details", {}).get("type", "unknown")
                type_counts[log_type] = type_counts.get(log_type, 0) + 1
                
                status = log.get("status", "unknown")
                if status in status_counts:
                    status_counts[status] += 1
        
        return {
            "total_logs": total_logs,
            "type_distribution": type_counts,
            "status_distribution": status_counts,
            "last_log_time": self.recent_logs[-1]["timestamp"] if self.recent_logs else None
        }

# Global logger instance
mining_logger = AssociationMiningLogger()