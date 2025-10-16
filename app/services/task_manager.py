"""
Task Manager for tracking background job status
"""
import uuid
import time
from enum import Enum
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import threading
import logging

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TaskInfo:
    task_id: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    message: str = ""
    error: Optional[str] = None
    result: Optional[Any] = None
    metadata: Dict[str, Any] = None

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        for key in ['created_at', 'started_at', 'completed_at']:
            if data[key]:
                data[key] = data[key].isoformat()
        # Convert enum to string
        data['status'] = data['status'].value
        return data

class TaskManager:
    """
    Singleton task manager for tracking background tasks
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(TaskManager, cls).__new__(cls)
                    cls._instance._tasks: Dict[str, TaskInfo] = {}
                    cls._instance._lock = threading.Lock()
        return cls._instance
    
    def create_task(self, task_type: str = "mining", metadata: Dict[str, Any] = None) -> str:
        """Create a new task and return task ID"""
        task_id = str(uuid.uuid4())
        
        with self._lock:
            self._tasks[task_id] = TaskInfo(
                task_id=task_id,
                status=TaskStatus.PENDING,
                created_at=datetime.now(),
                message=f"{task_type} task created",
                metadata=metadata or {}
            )
        
        logger.info(f"Task created: {task_id} ({task_type})")
        return task_id
    
    def start_task(self, task_id: str, message: str = "Task started"):
        """Mark task as started"""
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].status = TaskStatus.RUNNING
                self._tasks[task_id].started_at = datetime.now()
                self._tasks[task_id].message = message
                logger.info(f"Task started: {task_id}")
    
    def update_progress(self, task_id: str, progress: float, message: str = ""):
        """Update task progress (0.0 to 1.0)"""
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].progress = max(0.0, min(1.0, progress))
                if message:
                    self._tasks[task_id].message = message
                logger.debug(f"Task progress: {task_id} - {progress:.1%}")
    
    def complete_task(self, task_id: str, result: Any = None, message: str = "Task completed"):
        """Mark task as completed"""
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].status = TaskStatus.COMPLETED
                self._tasks[task_id].completed_at = datetime.now()
                self._tasks[task_id].progress = 1.0
                self._tasks[task_id].message = message
                self._tasks[task_id].result = result
                logger.info(f"Task completed: {task_id}")
    
    def fail_task(self, task_id: str, error: str, message: str = "Task failed"):
        """Mark task as failed"""
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].status = TaskStatus.FAILED
                self._tasks[task_id].completed_at = datetime.now()
                self._tasks[task_id].error = error
                self._tasks[task_id].message = message
                logger.error(f"Task failed: {task_id} - {error}")
    
    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """Get task information"""
        with self._lock:
            return self._tasks.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, TaskInfo]:
        """Get all tasks"""
        with self._lock:
            return self._tasks.copy()
    
    def get_running_tasks(self) -> Dict[str, TaskInfo]:
        """Get only running tasks"""
        with self._lock:
            return {
                task_id: task 
                for task_id, task in self._tasks.items() 
                if task.status == TaskStatus.RUNNING
            }
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Remove tasks older than specified hours"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        with self._lock:
            to_remove = []
            for task_id, task in self._tasks.items():
                if task.created_at.timestamp() < cutoff_time:
                    to_remove.append(task_id)
            
            for task_id in to_remove:
                del self._tasks[task_id]
                logger.info(f"Cleaned up old task: {task_id}")
    
    def cancel_task(self, task_id: str):
        """Cancel a task"""
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].status = TaskStatus.CANCELLED
                self._tasks[task_id].completed_at = datetime.now()
                self._tasks[task_id].message = "Task cancelled"
                logger.info(f"Task cancelled: {task_id}")

# Global task manager instance
task_manager = TaskManager()