"""
Shared mining endpoints and task execution logic
Uses UnifiedMiningService -> CleanAssociationMiningService for consistent mining
"""
import logging
from typing import Dict, Any, Optional
from app.modules.association_mining.services.unified_mining_service import UnifiedMiningService

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
    
    Uses UnifiedMiningService which internally uses CleanAssociationMiningService
    for consistent, production-grade mining across all endpoints.
    """
    global task_manager
    
    try:
        if task_manager:
            task_manager.start_task(task_id=task_id)
        
        logger.info(f"🚀 Starting mining task: {task_id}")
        logger.info(f"Parameters: days_back={days_back}, min_support={min_support}, "
                   f"min_confidence={min_confidence}, min_lift={min_lift}")
        
        # Prepare mining parameters
        mining_params = {
            'days_back': days_back,
            'min_support': min_support,
            'min_confidence': min_confidence,
            'min_lift': min_lift,
            'max_recommendations': max_recommendations,
            'decay_rate': decay_rate,
            'use_enhanced_mining': use_enhanced_mining,
            'time_weighting_method': time_weighting_method,
            'time_segmentation': time_segmentation,
            'output_table': db_config.get('recommendations_table', 'sku_recommendations') if db_config else 'sku_recommendations',
            'max_items': 200
        }
        
        # Use unified mining service
        mining_service = UnifiedMiningService(db_config, mining_params)
        result = mining_service.run_mining(task_id=task_id, task_manager=task_manager)
        
        logger.info(f"========== ENDPOINT RESULT ==========")
        logger.info(f"Mining service returned: {result}")
        logger.info(f"Rules generated: {result.get('rules_generated', 0)}")
        logger.info(f"Records processed: {result.get('records_processed', 0)}")
        logger.info(f"=====================================")
        
        # Build result dictionary compatible with scheduler expectations
        response = {
            "status": "success" if result.get("success") else "error",
            "stats": result.get("stats", {}),
            "recommendations_count": result.get("rules_generated", 0),
            "database_stats": result.get("database_stats", {}),
            "records_processed": result.get("records_processed", 0)
        }
        
        if not result.get("success"):
            response["error"] = result.get("error", "Unknown error")
        
        if task_manager:
            logger.info(f"Calling task_manager.complete_task with response: {response}")
            task_manager.complete_task(task_id=task_id, result=response, message="Mining completed successfully")
        
        logger.info(f"✅ Mining task completed: {task_id}")
        return response
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Mining task failed: {task_id} - {error_msg}")
        
        if task_manager:
            task_manager.fail_task(task_id=task_id, error_msg=error_msg)
        
        return {
            "status": "error",
            "error": error_msg,
            "recommendations_count": 0,
            "stats": {},
            "records_processed": 0
        }
