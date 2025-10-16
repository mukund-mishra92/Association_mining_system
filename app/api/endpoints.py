from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import logging
from app.database.connection import DatabaseConnection
from app.services.clean_mining_service import CleanAssociationMiningService
from app.services.task_manager import task_manager, TaskStatus

logger = logging.getLogger(__name__)
router = APIRouter()

# Request/Response models
class DatabaseConfig(BaseModel):
    host: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    order_table: Optional[str] = None
    sku_master_table: Optional[str] = None
    recommendations_table: Optional[str] = None

class MiningRequest(BaseModel):
    days_back: Optional[int] = None
    min_support: Optional[float] = None
    min_confidence: Optional[float] = None
    use_enhanced_mining: Optional[bool] = True
    time_weighting_method: Optional[str] = "exponential_decay"  # exponential_decay, linear_decay, seasonal_patterns, recency_frequency, trend_adaptive
    time_segmentation: Optional[str] = "weekly"  # weekly, monthly, daily
    db_config: Optional[DatabaseConfig] = None  # Database configuration from UI

class RecommendationResponse(BaseModel):
    recommended_item: str
    score: float
    rank: int

class ItemRecommendationsResponse(BaseModel):
    main_item: str
    recommendations: List[RecommendationResponse]

class MiningStatusResponse(BaseModel):
    status: str
    message: str
    task_id: Optional[str] = None
    recommendations_count: Optional[int] = None

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: float
    message: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[dict] = None
    result: Optional[dict] = None

# Background task for mining
def run_mining_task(task_id: str, days_back=None, use_enhanced_mining=True, time_weighting_method="exponential_decay", time_segmentation="weekly", db_config=None):
    """Background task to run mining pipeline with progress tracking"""
    try:
        # Mark task as started
        task_manager.start_task(task_id, "Initializing mining process...")
        
        # Log received configuration
        if db_config:
            logger.info(f"Mining task using custom configuration with table: {db_config.get('recommendations_table', 'NOT SET')}")
        else:
            logger.info("Mining task using default configuration")
        
        # Initialize database connection with custom config if provided
        if db_config:
            db = DatabaseConnection(custom_config=db_config)
        else:
            db = DatabaseConnection()
        
        # Use the clean mining service for all operations
        mining_service = CleanAssociationMiningService(task_id=task_id, task_manager=task_manager)
        
        # Connect to database
        task_manager.update_progress(task_id, 0.1, "Connecting to database...")
        if not db.connect():
            task_manager.fail_task(task_id, "Failed to connect to database")
            return
        
        # Fetch data
        task_manager.update_progress(task_id, 0.2, "Fetching order data...")
        df_basket = db.fetch_order_data(days_back=days_back)
        if df_basket is None or df_basket.empty:
            task_manager.fail_task(task_id, "No data found for mining")
            return
        
        # Run mining pipeline with detailed progress tracking
        logger.info(f"Starting mining pipeline for task {task_id}")
        
        # Run the clean mining pipeline
        recommendations = mining_service.run_mining_pipeline(df_basket)
        
        task_manager.update_progress(task_id, 0.8, "Processing recommendations...")
        
        if not recommendations.empty:
            # Save to database
            task_manager.update_progress(task_id, 0.9, "Saving recommendations to database...")
            success = db.save_recommendations(recommendations)
            
            # Sort recommendations by composite_score descending for UI (highest scores first)
            recommendations_sorted = recommendations.sort_values('composite_score', ascending=False).reset_index(drop=True)
            
            # Normalize scores for UI (same logic as database)
            scores = recommendations_sorted['composite_score'].astype(float)
            min_score = scores.min()
            max_score = scores.max()
            
            # Normalize to 0.001 - 0.999 range
            if max_score == min_score:
                normalized_scores = [0.5] * len(scores)  # Use middle value if all scores identical
            else:
                normalized_scores = (0.001 + (scores - min_score) / (max_score - min_score) * 0.998).tolist()
            
            # Convert recommendations to JSON-serializable format for UI with normalized scores
            rules_for_ui = []
            for idx, (_, rec) in enumerate(recommendations_sorted.head(100).iterrows()):  # Limit to first 100 for UI
                rules_for_ui.append({
                    "sku1": rec.get('main_item', ''),           # SKU ID
                    "sku2": rec.get('recommended_item', ''),    # SKU ID
                    "sku1_name": rec.get('main_item_name', ''), # SKU Name
                    "sku2_name": rec.get('recommended_item_name', ''), # SKU Name
                    "main_item": rec.get('main_item', ''),      # SKU ID (for backward compatibility)
                    "recommended_item": rec.get('recommended_item', ''), # SKU ID (for backward compatibility)
                    "main_item_name": rec.get('main_item_name', ''),     # SKU Name
                    "recommended_item_name": rec.get('recommended_item_name', ''), # SKU Name
                    "confidence": float(rec.get('confidence_score', 0)),
                    "lift": float(rec.get('lift_score', 0)),
                    "support": float(rec.get('support_score', 0)),
                    "composite_score": float(normalized_scores[idx]),  # NORMALIZED SCORE
                    "association_composite_score": float(normalized_scores[idx])  # NORMALIZED SCORE
                })
            
            # Calculate normalized score range for UI (using sorted data)
            ui_scores = [float(normalized_scores[idx]) for idx in range(min(100, len(normalized_scores)))]
            score_range = {
                "min": min(ui_scores) if ui_scores else 0.001,
                "max": max(ui_scores) if ui_scores else 0.999
            }
            
            result = {
                "recommendations_count": len(recommendations),
                "mining_method": "enhanced" if use_enhanced_mining else "standard",
                "time_weighting_method": time_weighting_method if use_enhanced_mining else None,
                "stats": {
                    "total_rules": len(rules_for_ui),
                    "top_n_skus": len(df_basket['SKU_NAME'].unique()) if not df_basket.empty else 0,
                    "total_orders": len(df_basket['ORDER_ID'].unique()) if not df_basket.empty else 0,
                    "score_range": score_range,
                    "mining_duration": "completed",
                    "database_saved": success
                },
                "rules": rules_for_ui
            }
            
            if success:
                task_manager.complete_task(
                    task_id, 
                    result=result,
                    message=f"Mining completed: {len(recommendations)} recommendations generated and saved to database"
                )
                logger.info(f"Mining completed: {len(recommendations)} recommendations generated and saved to database")
            else:
                task_manager.complete_task(
                    task_id, 
                    result=result,
                    message=f"Mining completed: {len(recommendations)} recommendations generated (database save failed)"
                )
                logger.warning(f"Mining completed: {len(recommendations)} recommendations generated but database save failed")
        else:
            task_manager.complete_task(
                task_id,
                result={"recommendations_count": 0},
                message="Mining completed but no recommendations generated"
            )
            logger.warning("No recommendations generated")
    
    except Exception as e:
        error_msg = f"Error in mining task: {str(e)}"
        task_manager.fail_task(task_id, error_msg)
        logger.error(error_msg)
    
    finally:
        if 'db' in locals():
            db.disconnect()

@router.post("/mine-rules", response_model=MiningStatusResponse)
async def mine_association_rules(
    request: MiningRequest,
    background_tasks: BackgroundTasks
):
    """Start association rule mining process with task tracking"""
    try:
        # Create a new task
        task_id = task_manager.create_task(
            task_type="association_mining",
            metadata={
                "days_back": request.days_back,
                "use_enhanced_mining": request.use_enhanced_mining,
                "time_weighting_method": request.time_weighting_method,
                "time_segmentation": request.time_segmentation,
                "db_config": request.db_config.dict() if request.db_config else None
            }
        )
        
        # Convert db_config to dict if provided
        db_config_dict = request.db_config.dict() if request.db_config else None
        
        # Add mining task to background
        background_tasks.add_task(
            run_mining_task,
            task_id=task_id,
            days_back=request.days_back,
            use_enhanced_mining=request.use_enhanced_mining,
            time_weighting_method=request.time_weighting_method,
            time_segmentation=request.time_segmentation,
            db_config=db_config_dict
        )
        
        mining_type = "Enhanced" if request.use_enhanced_mining else "Standard"
        return MiningStatusResponse(
            status="started",
            task_id=task_id,
            message=f"{mining_type} association rule mining started in background with {request.time_weighting_method} weighting"
        )
    
    except Exception as e:
        logger.error(f"Error starting mining: {e}")
        raise HTTPException(status_code=500, detail="Failed to start mining process")

@router.get("/recommendations/{item_name}", response_model=ItemRecommendationsResponse)
async def get_item_recommendations(item_name: str, limit: int = 10):
    """Get recommendations for a specific item"""
    db = DatabaseConnection()
    
    try:
        if not db.connect():
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        recommendations = db.get_recommendations(item_name, limit=limit)
        
        return ItemRecommendationsResponse(
            main_item=item_name,
            recommendations=[
                RecommendationResponse(**rec) for rec in recommendations
            ]
        )
    
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")
    
    finally:
        db.disconnect()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Association Mining API"}

@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get status of a specific task"""
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_dict = task.to_dict()
    return TaskStatusResponse(**task_dict)

@router.get("/tasks")
async def get_all_tasks():
    """Get status of all tasks"""
    tasks = task_manager.get_all_tasks()
    return {
        "tasks": [task.to_dict() for task in tasks.values()],
        "count": len(tasks)
    }

@router.get("/tasks/running")
async def get_running_tasks():
    """Get status of currently running tasks"""
    running_tasks = task_manager.get_running_tasks()
    return {
        "running_tasks": [task.to_dict() for task in running_tasks.values()],
        "count": len(running_tasks)
    }

@router.delete("/task/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a running task"""
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Task already finished")
    
    task_manager.cancel_task(task_id)
    return {"message": f"Task {task_id} cancelled"}

@router.post("/tasks/cleanup")
async def cleanup_old_tasks(max_age_hours: int = 24):
    """Clean up old completed tasks"""
    task_manager.cleanup_old_tasks(max_age_hours)
    return {"message": f"Cleaned up tasks older than {max_age_hours} hours"}