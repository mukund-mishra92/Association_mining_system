"""
Shared mining endpoints and task execution logic
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Global task manager for tracking progress
task_manager = None


def run_mining_task(
    task_id: str,
    days_back: int,
    min_support: float,
    min_confidence: float,
    min_lift: float,
    max_recommendations: int,
    decay_rate: float,
    use_enhanced_mining: bool = True,
    time_weighting_method: str = "exponential_decay",
    time_segmentation: str = "weekly",
    db_config: Dict[str, Any] = None,
    skip_logging: bool = False
) -> Dict[str, Any]:
    """
    Execute a mining task with the given parameters.
    
    This function wraps the mining logic from web.main to provide
    a consistent interface for both API and scheduler usage.
    """
    global task_manager
    
    try:
        if task_manager:
            task_manager.start_task(task_id=task_id)
        
        logger.info(f"🚀 Starting mining task: {task_id}")
        logger.info(f"Parameters: days_back={days_back}, min_support={min_support}, "
                   f"min_confidence={min_confidence}, min_lift={min_lift}")
        
        # Import the actual mining function from web module
        from app.web.main import generate_rules_top_skus
        
        # Prepare user config from db_config
        user_config = db_config if db_config else {}
        
        # Call the mining function
        stats, rules = generate_rules_top_skus(
            user_config=user_config,
            top_n=200,  # Use a reasonable default
            days_back=days_back,
            min_support=min_support,
            min_confidence=min_confidence,
            min_lift=min_lift,
            max_recommendations=max_recommendations,
            decay_rate=decay_rate
        )
        
        # Build result dictionary
        result = {
            "status": "success",
            "stats": stats,
            "recommendations_count": stats.get("total_rules", 0) if isinstance(stats, dict) else 0,
            "database_stats": stats.get("database_stats", {}) if isinstance(stats, dict) else {}
        }
        
        if task_manager:
            task_manager.complete_task(task_id=task_id, result=result, message="Mining completed successfully")
        
        logger.info(f"✅ Mining task completed: {task_id}")
        return result
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Mining task failed: {task_id} - {error_msg}")
        
        if task_manager:
            task_manager.fail_task(task_id=task_id, error_msg=error_msg)
        
        return {
            "status": "error",
            "error": error_msg,
            "recommendations_count": 0,
            "stats": {}
        }
