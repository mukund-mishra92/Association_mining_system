from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, time
import logging
from app.modules.association_mining.services.scheduler_service import get_scheduler_service

logger = logging.getLogger(__name__)

router = APIRouter()

class ScheduleCreateRequest(BaseModel):
    job_name: str = Field(..., min_length=1, max_length=255, description="Unique name for the scheduled job")
    job_description: Optional[str] = Field("", max_length=1000, description="Description of the scheduled job")
    schedule_type: str = Field(..., pattern="^(daily|weekly)$", description="Schedule type: daily or weekly")
    schedule_time: str = Field(..., pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?$", description="Time in HH:MM or HH:MM:SS format (24-hour)")
    schedule_day_of_week: Optional[int] = Field(None, ge=0, le=6, description="Day of week for weekly schedules (0=Monday, 6=Sunday)")
    
    # Algorithm parameters
    min_support: Optional[float] = Field(0.300, ge=0.001, le=1.0, description="Minimum support threshold")
    min_confidence: Optional[float] = Field(0.300, ge=0.001, le=1.0, description="Minimum confidence threshold")
    min_lift: Optional[float] = Field(1.0, ge=0.1, le=10.0, description="Minimum lift threshold")
    max_recommendations: Optional[int] = Field(10, ge=1, le=100, description="Maximum number of recommendations")
    decay_rate: Optional[float] = Field(0.050, ge=0.001, le=1.0, description="Decay rate for temporal analysis")
    
    # Data filtering parameters
    days_back: Optional[int] = Field(365, ge=1, le=3650, description="Number of days of historical data to use")
    max_items: Optional[int] = Field(200, ge=10, le=1000, description="Maximum number of top items to analyze")
    min_item_frequency: Optional[int] = Field(5, ge=1, le=100, description="Minimum item frequency in orders")
    
    # Enhanced mining parameters
    use_enhanced_mining: Optional[bool] = Field(True, description="Use enhanced mining with time weighting")
    time_weighting_method: Optional[str] = Field("exponential_decay", description="Time weighting method: exponential_decay, linear_decay, seasonal_patterns, recency_frequency, trend_adaptive")
    time_segmentation: Optional[str] = Field("weekly", description="Time segmentation: weekly, monthly, daily")
    
    # Job configuration
    output_table: Optional[str] = Field("article_proximity_score", max_length=255, description="Output table name")
    is_active: Optional[bool] = Field(True, description="Whether the schedule is active")

class ScheduleUpdateRequest(BaseModel):
    job_name: Optional[str] = Field(None, min_length=1, max_length=255)
    job_description: Optional[str] = Field(None, max_length=1000)
    schedule_type: Optional[str] = Field(None, pattern="^(daily|weekly)$")
    schedule_time: Optional[str] = Field(None, pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?$")
    schedule_day_of_week: Optional[int] = Field(None, ge=0, le=6)
    
    # Algorithm parameters
    min_support: Optional[float] = Field(None, ge=0.001, le=1.0)
    min_confidence: Optional[float] = Field(None, ge=0.001, le=1.0)
    min_lift: Optional[float] = Field(None, ge=0.1, le=10.0)
    max_recommendations: Optional[int] = Field(None, ge=1, le=100)
    decay_rate: Optional[float] = Field(None, ge=0.001, le=1.0)
    
    # Data filtering parameters
    days_back: Optional[int] = Field(None, ge=1, le=3650)
    max_items: Optional[int] = Field(None, ge=10, le=1000)
    min_item_frequency: Optional[int] = Field(None, ge=1, le=100)
    
    # Enhanced mining parameters
    use_enhanced_mining: Optional[bool] = None
    time_weighting_method: Optional[str] = None
    time_segmentation: Optional[str] = None
    
    # Job configuration
    output_table: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None

class ScheduleResponse(BaseModel):
    id: int
    job_name: str
    job_description: str
    schedule_type: str
    schedule_time: str
    schedule_day_of_week: Optional[int] = None
    min_support: float
    min_confidence: float
    min_lift: float
    max_recommendations: int
    decay_rate: float
    output_table: str
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    created_by: str = "system"
    days_back: Optional[int] = 365
    max_items: Optional[int] = 200
    min_item_frequency: Optional[int] = 5
    use_enhanced_mining: Optional[bool] = True
    time_weighting_method: Optional[str] = "exponential_decay"
    time_segmentation: Optional[str] = "weekly"
    stats: Optional[Dict[str, Any]] = None

class JobLogResponse(BaseModel):
    id: int
    schedule_id: int
    job_name: str
    started_at: Optional[str]
    completed_at: Optional[str]
    execution_status: str
    rules_generated: int
    records_processed: int
    execution_time_seconds: int
    error_message: Optional[str]
    error_details: Optional[Dict[str, Any]]
    execution_parameters: Optional[Dict[str, Any]]

@router.post("/schedules", response_model=Dict[str, Any])
async def create_schedule(schedule_request: ScheduleCreateRequest):
    """Create a new mining schedule"""
    try:
        scheduler_service = get_scheduler_service(None)
        
        # Validate weekly schedule has day_of_week
        if schedule_request.schedule_type == "weekly" and schedule_request.schedule_day_of_week is None:
            raise HTTPException(status_code=400, detail="schedule_day_of_week is required for weekly schedules")
        
        # Convert request to dict
        schedule_data = schedule_request.model_dump()
        
        # Start scheduler if not running
        if not scheduler_service.is_running:
            scheduler_service.start()
        
        result = scheduler_service.create_schedule(schedule_data)
        
        return {
            "success": True,
            "message": f"Schedule '{schedule_request.job_name}' created successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create schedule: {str(e)}")

@router.get("/schedules", response_model=List[ScheduleResponse])
async def get_schedules():
    """Get all mining schedules"""
    try:
        scheduler_service = get_scheduler_service(None)
        schedules = scheduler_service.get_schedules()
        return schedules
        
    except Exception as e:
        logger.error(f"Failed to get schedules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get schedules: {str(e)}")

@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: int):
    """Get a specific schedule by ID"""
    try:
        scheduler_service = get_scheduler_service(None)
        schedules = scheduler_service.get_schedules()
        
        schedule = next((s for s in schedules if s['id'] == schedule_id), None)
        if not schedule:
            raise HTTPException(status_code=404, detail=f"Schedule {schedule_id} not found")
        
        return schedule
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get schedule: {str(e)}")

@router.put("/schedules/{schedule_id}", response_model=Dict[str, Any])
async def update_schedule(schedule_id: int, schedule_request: ScheduleUpdateRequest):
    """Update an existing schedule"""
    try:
        scheduler_service = get_scheduler_service(None)
        
        # Convert request to dict, excluding None values
        schedule_data = {k: v for k, v in schedule_request.dict().items() if v is not None}
        
        if not schedule_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Validate weekly schedule has day_of_week if changing to weekly
        if schedule_data.get('schedule_type') == "weekly" and 'schedule_day_of_week' not in schedule_data:
            # Check if current schedule is weekly and has day_of_week
            current_schedules = scheduler_service.get_schedules()
            current_schedule = next((s for s in current_schedules if s['id'] == schedule_id), None)
            if not current_schedule:
                raise HTTPException(status_code=404, detail=f"Schedule {schedule_id} not found")
            
            if current_schedule['schedule_day_of_week'] is None:
                raise HTTPException(status_code=400, detail="schedule_day_of_week is required for weekly schedules")
        
        result = scheduler_service.update_schedule(schedule_id, schedule_data)
        
        return {
            "success": True,
            "message": f"Schedule {schedule_id} updated successfully",
            "data": result
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update schedule: {str(e)}")

@router.delete("/schedules/{schedule_id}", response_model=Dict[str, Any])
async def delete_schedule(schedule_id: int):
    """Delete a schedule"""
    try:
        scheduler_service = get_scheduler_service(None)
        result = scheduler_service.delete_schedule(schedule_id)
        
        return {
            "success": True,
            "message": f"Schedule {schedule_id} deleted successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to delete schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete schedule: {str(e)}")

@router.delete("/schedules", response_model=Dict[str, Any])
async def delete_all_schedules():
    """Delete all schedules and related data"""
    try:
        scheduler_service = get_scheduler_service(None)
        result = scheduler_service.delete_all_schedules()
        
        return {
            "success": True,
            "message": "All schedules deleted successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to delete all schedules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete all schedules: {str(e)}")

@router.post("/schedules/{schedule_id}/toggle", response_model=Dict[str, Any])
async def toggle_schedule(schedule_id: int, db_config: Optional[Dict] = None):
    """Toggle a schedule's active status"""
    try:
        scheduler_service = get_scheduler_service(db_config)
        
        # Get current schedule
        schedules = scheduler_service.get_schedules()
        schedule = next((s for s in schedules if s['id'] == schedule_id), None)
        if not schedule:
            raise HTTPException(status_code=404, detail=f"Schedule {schedule_id} not found")
        
        # Toggle active status
        new_status = not schedule['is_active']
        result = scheduler_service.update_schedule(schedule_id, {'is_active': new_status})
        
        action = "activated" if new_status else "deactivated"
        return {
            "success": True,
            "message": f"Schedule {schedule_id} {action} successfully",
            "data": {**result, "new_status": new_status}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to toggle schedule: {str(e)}")

@router.post("/schedules/{schedule_id}/run", response_model=Dict[str, Any])
async def run_schedule_now(schedule_id: int, background_tasks: BackgroundTasks, db_config: Optional[Dict] = None):
    """Manually trigger a schedule to run now"""
    try:
        scheduler_service = get_scheduler_service(db_config)
        
        # Verify schedule exists
        schedules = scheduler_service.get_schedules()
        schedule = next((s for s in schedules if s['id'] == schedule_id), None)
        if not schedule:
            raise HTTPException(status_code=404, detail=f"Schedule {schedule_id} not found")
        
        # Run in background
        background_tasks.add_task(scheduler_service.execute_mining_job, schedule_id)
        
        return {
            "success": True,
            "message": f"Schedule '{schedule['job_name']}' execution started",
            "data": {"schedule_id": schedule_id, "status": "running"}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to run schedule: {str(e)}")

@router.get("/schedules/{schedule_id}/logs", response_model=List[JobLogResponse])
async def get_schedule_logs(schedule_id: int, limit: int = 20, db_config: Optional[Dict] = None):
    """Get execution logs for a specific schedule"""
    try:
        scheduler_service = get_scheduler_service(db_config)
        logs = scheduler_service.get_job_logs(schedule_id=schedule_id, limit=limit)
        return logs
        
    except Exception as e:
        logger.error(f"Failed to get schedule logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get schedule logs: {str(e)}")

@router.get("/logs", response_model=List[JobLogResponse])
async def get_all_logs(limit: int = 50, db_config: Optional[Dict] = None):
    """Get execution logs for all schedules"""
    try:
        scheduler_service = get_scheduler_service(db_config)
        logs = scheduler_service.get_job_logs(limit=limit)
        return logs
        
    except Exception as e:
        logger.error(f"Failed to get logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")

@router.get("/status", response_model=Dict[str, Any])
async def get_scheduler_status(db_config: Optional[Dict] = None):
    """Get scheduler service status"""
    try:
        scheduler_service = get_scheduler_service(db_config)
        
        # Check if scheduler is actually running by querying APScheduler directly
        # The scheduler.running property is more reliable than our is_running flag
        scheduler_actually_running = scheduler_service.scheduler.running
        
        # Update our flag if it's out of sync
        if scheduler_actually_running and not scheduler_service.is_running:
            scheduler_service.is_running = True
            logger.info("Synchronized is_running flag with actual scheduler state")
        
        # Get active jobs from APScheduler
        active_jobs = []
        if scheduler_actually_running:
            for job in scheduler_service.scheduler.get_jobs():
                active_jobs.append({
                    "job_id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
                })
        
        # Get schedules summary
        schedules = scheduler_service.get_schedules()
        active_schedules = [s for s in schedules if s['is_active']]
        
        return {
            "scheduler_running": scheduler_actually_running,
            "total_schedules": len(schedules),
            "active_schedules": len(active_schedules),
            "scheduled_jobs": len(active_jobs),
            "active_jobs": active_jobs
        }
        
    except Exception as e:
        logger.error(f"Failed to get scheduler status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")

@router.post("/start", response_model=Dict[str, Any])
async def start_scheduler(db_config: Optional[Dict] = None):
    """Start the scheduler service"""
    try:
        scheduler_service = get_scheduler_service(db_config)
        
        if scheduler_service.is_running:
            return {
                "success": True,
                "message": "Scheduler is already running",
                "status": "running"
            }
        
        scheduler_service.start()
        
        return {
            "success": True,
            "message": "Scheduler started successfully",
            "status": "running"
        }
        
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start scheduler: {str(e)}")

@router.post("/stop", response_model=Dict[str, Any])
async def stop_scheduler(db_config: Optional[Dict] = None):
    """Stop the scheduler service"""
    try:
        scheduler_service = get_scheduler_service(db_config)
        
        if not scheduler_service.is_running:
            return {
                "success": True,
                "message": "Scheduler is already stopped",
                "status": "stopped"
            }
        
        scheduler_service.stop()
        
        return {
            "success": True,
            "message": "Scheduler stopped successfully",
            "status": "stopped"
        }
        
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stop scheduler: {str(e)}")