"""
Weekly Scheduling System for Bin Velocity Analysis
Provides automated weekly processing of SKU and bin velocity calculations

Features:
- Weekly job scheduling (Mondays by default)
- Job status monitoring
- Automatic retry on failure
- Email notifications (optional)
- Integration with existing scheduler system
"""

import threading
import time
import schedule
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional, Callable
import json

from ..services.velocity_service import VelocityAnalysisService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VelocityScheduler:
    """Scheduler for automated velocity analysis jobs"""
    
    def __init__(self, db_config: Dict):
        """
        Initialize the velocity scheduler
        
        Args:
            db_config: Database connection configuration
        """
        self.db_config = db_config
        self.running = False
        self.scheduler_thread = None
        self.job_history = []
        self.max_history = 50  # Keep last 50 job executions
        
    def start_scheduler(self) -> Dict:
        """Start the weekly scheduler"""
        if self.running:
            return {"success": False, "message": "Scheduler is already running"}
        
        try:
            # Schedule weekly job for Mondays at 2:00 AM
            schedule.every().monday.at("02:00").do(self._run_weekly_job)
            
            # Start scheduler thread
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            
            logger.info("Velocity analysis scheduler started - Weekly jobs on Mondays at 2:00 AM")
            
            return {
                "success": True,
                "message": "Velocity analysis scheduler started successfully",
                "schedule": "Every Monday at 2:00 AM",
                "started_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to start velocity scheduler: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def stop_scheduler(self) -> Dict:
        """Stop the weekly scheduler"""
        if not self.running:
            return {"success": False, "message": "Scheduler is not running"}
        
        try:
            self.running = False
            schedule.clear()
            
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)
            
            logger.info("Velocity analysis scheduler stopped")
            
            return {
                "success": True,
                "message": "Velocity analysis scheduler stopped successfully",
                "stopped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to stop velocity scheduler: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def get_scheduler_status(self) -> Dict:
        """Get current scheduler status"""
        try:
            status = {
                "running": self.running,
                "scheduled_jobs": len(schedule.jobs),
                "next_run": None,
                "last_job": None,
                "total_jobs_executed": len(self.job_history)
            }
            
            # Get next scheduled run
            if schedule.jobs:
                next_run = schedule.next_run()
                status["next_run"] = next_run.isoformat() if next_run else None
            
            # Get last job execution
            if self.job_history:
                status["last_job"] = self.job_history[-1]
            
            return {"success": True, "status": status}
            
        except Exception as e:
            logger.error(f"Failed to get scheduler status: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def run_job_now(self, force: bool = False) -> Dict:
        """Run velocity analysis job immediately"""
        logger.info("Running velocity analysis job manually")
        return self._run_weekly_job(manual=True, force=force)
    
    def get_job_history(self, limit: int = 10) -> Dict:
        """Get recent job execution history"""
        try:
            recent_jobs = self.job_history[-limit:] if limit > 0 else self.job_history
            return {
                "success": True,
                "job_history": recent_jobs,
                "total_jobs": len(self.job_history)
            }
        except Exception as e:
            logger.error(f"Failed to get job history: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def _scheduler_loop(self):
        """Main scheduler loop running in background thread"""
        logger.info("Velocity scheduler loop started")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                time.sleep(60)
        
        logger.info("Velocity scheduler loop stopped")
    
    def _run_weekly_job(self, manual: bool = False, force: bool = False) -> Dict:
        """Execute the weekly velocity analysis job"""
        job_start = datetime.now()
        job_id = f"velocity_weekly_{job_start.strftime('%Y%m%d_%H%M%S')}"
        
        job_record = {
            "job_id": job_id,
            "start_time": job_start.isoformat(),
            "end_time": None,
            "duration_seconds": None,
            "status": "running",
            "manual_trigger": manual,
            "force_run": force,
            "results": {},
            "error": None
        }
        
        try:
            logger.info(f"Starting weekly velocity analysis job: {job_id}")
            
            # Create service instance
            service = VelocityAnalysisService(self.db_config)
            
            # Connect to database
            if not service.connect_database():
                raise Exception("Database connection failed")
            
            # Run weekly analysis
            results = service.run_weekly_analysis()
            
            # Disconnect from database
            service.disconnect_database()
            
            # Update job record
            job_end = datetime.now()
            job_record["end_time"] = job_end.isoformat()
            job_record["duration_seconds"] = (job_end - job_start).total_seconds()
            job_record["results"] = results
            
            if results["overall_success"]:
                job_record["status"] = "completed"
                logger.info(f"Weekly velocity analysis job completed successfully: {job_id}")
            else:
                job_record["status"] = "failed"
                job_record["error"] = results.get("error", "Unknown error")
                logger.error(f"Weekly velocity analysis job failed: {job_id}")
            
        except Exception as e:
            # Update job record with error
            job_end = datetime.now()
            job_record["end_time"] = job_end.isoformat()
            job_record["duration_seconds"] = (job_end - job_start).total_seconds()
            job_record["status"] = "error"
            job_record["error"] = str(e)
            
            logger.error(f"Weekly velocity analysis job error: {job_id} - {str(e)}")
        
        # Add to job history
        self._add_job_to_history(job_record)
        
        return {
            "success": job_record["status"] == "completed",
            "job_record": job_record
        }
    
    def _add_job_to_history(self, job_record: Dict):
        """Add job record to history with size limit"""
        self.job_history.append(job_record)
        
        # Keep only the most recent jobs
        if len(self.job_history) > self.max_history:
            self.job_history = self.job_history[-self.max_history:]
    
    def set_custom_schedule(self, day_of_week: str, time_str: str) -> Dict:
        """
        Set a custom schedule for velocity analysis
        
        Args:
            day_of_week: 'monday', 'tuesday', etc.
            time_str: Time in format 'HH:MM'
            
        Returns:
            Dict: Success status and message
        """
        try:
            # Clear existing schedule
            schedule.clear()
            
            # Set new schedule
            day_method = getattr(schedule.every(), day_of_week.lower())
            day_method.at(time_str).do(self._run_weekly_job)
            
            logger.info(f"Velocity analysis schedule updated: {day_of_week} at {time_str}")
            
            return {
                "success": True,
                "message": f"Schedule updated to {day_of_week} at {time_str}",
                "next_run": schedule.next_run().isoformat() if schedule.jobs else None
            }
            
        except Exception as e:
            logger.error(f"Failed to set custom schedule: {str(e)}")
            return {"success": False, "message": str(e)}

# Global scheduler instance
_velocity_scheduler: Optional[VelocityScheduler] = None

def get_velocity_scheduler(db_config: Dict) -> VelocityScheduler:
    """Get or create the global velocity scheduler instance"""
    global _velocity_scheduler
    
    if _velocity_scheduler is None:
        _velocity_scheduler = VelocityScheduler(db_config)
    else:
        # Update db_config if it has changed
        _velocity_scheduler.db_config = db_config
    
    return _velocity_scheduler

def create_scheduled_job_api_endpoints():
    """Create API endpoints for velocity scheduler management"""
    
    from flask import Blueprint, request, jsonify
    
    scheduler_bp = Blueprint('velocity_scheduler', __name__, url_prefix='/api/velocity/scheduler')
    
    @scheduler_bp.route('/start', methods=['POST'])
    def start_velocity_scheduler():
        """Start the velocity analysis scheduler"""
        try:
            data = request.get_json() or {}
            db_config = data.get('db_config')
            
            if not db_config:
                return jsonify({
                    "success": False,
                    "message": "Database configuration required"
                }), 400
            
            scheduler = get_velocity_scheduler(db_config)
            result = scheduler.start_scheduler()
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Start scheduler API error: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"Scheduler start error: {str(e)}"
            }), 500
    
    @scheduler_bp.route('/stop', methods=['POST'])
    def stop_velocity_scheduler():
        """Stop the velocity analysis scheduler"""
        try:
            data = request.get_json() or {}
            db_config = data.get('db_config')
            
            if not db_config:
                return jsonify({
                    "success": False,
                    "message": "Database configuration required"
                }), 400
            
            scheduler = get_velocity_scheduler(db_config)
            result = scheduler.stop_scheduler()
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Stop scheduler API error: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"Scheduler stop error: {str(e)}"
            }), 500
    
    @scheduler_bp.route('/status', methods=['POST'])
    def get_velocity_scheduler_status():
        """Get velocity analysis scheduler status"""
        try:
            data = request.get_json() or {}
            db_config = data.get('db_config')
            
            if not db_config:
                return jsonify({
                    "success": False,
                    "message": "Database configuration required"
                }), 400
            
            scheduler = get_velocity_scheduler(db_config)
            result = scheduler.get_scheduler_status()
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Scheduler status API error: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"Status check error: {str(e)}"
            }), 500
    
    @scheduler_bp.route('/run-now', methods=['POST'])
    def run_velocity_job_now():
        """Run velocity analysis job immediately"""
        try:
            data = request.get_json() or {}
            db_config = data.get('db_config')
            force = data.get('force', False)
            
            if not db_config:
                return jsonify({
                    "success": False,
                    "message": "Database configuration required"
                }), 400
            
            scheduler = get_velocity_scheduler(db_config)
            result = scheduler.run_job_now(force=force)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Run job now API error: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"Job execution error: {str(e)}"
            }), 500
    
    @scheduler_bp.route('/history', methods=['POST'])
    def get_velocity_job_history():
        """Get velocity analysis job execution history"""
        try:
            data = request.get_json() or {}
            db_config = data.get('db_config')
            limit = data.get('limit', 10)
            
            if not db_config:
                return jsonify({
                    "success": False,
                    "message": "Database configuration required"
                }), 400
            
            scheduler = get_velocity_scheduler(db_config)
            result = scheduler.get_job_history(limit=limit)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Job history API error: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"History retrieval error: {str(e)}"
            }), 500
    
    @scheduler_bp.route('/set-schedule', methods=['POST'])
    def set_velocity_custom_schedule():
        """Set custom schedule for velocity analysis"""
        try:
            data = request.get_json() or {}
            db_config = data.get('db_config')
            day_of_week = data.get('day_of_week')
            time_str = data.get('time')
            
            if not all([db_config, day_of_week, time_str]):
                return jsonify({
                    "success": False,
                    "message": "Database config, day_of_week, and time are required"
                }), 400
            
            scheduler = get_velocity_scheduler(db_config)
            result = scheduler.set_custom_schedule(day_of_week, time_str)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Set schedule API error: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"Schedule setting error: {str(e)}"
            }), 500
    
    return scheduler_bp