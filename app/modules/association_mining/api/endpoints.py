from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import logging
from app.shared.database.connection import DatabaseConnection
from app.modules.association_mining.services.clean_mining_service import CleanAssociationMiningService
from app.shared.utils.task_manager import task_manager, TaskStatus
from app.modules.association_mining.api.scheduler_endpoints import router as scheduler_router

logger = logging.getLogger(__name__)
router = APIRouter()

# Include scheduler endpoints
router.include_router(scheduler_router, prefix="/scheduler", tags=["scheduler"])

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
    min_lift: Optional[float] = None
    max_recommendations: Optional[int] = None
    decay_rate: Optional[float] = None
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
def run_mining_task(task_id: str, days_back=None, min_support=None, min_confidence=None, 
                   min_lift=None, max_recommendations=None, decay_rate=None,
                   use_enhanced_mining=True, time_weighting_method="exponential_decay", 
                   time_segmentation="weekly", db_config=None):
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
        
        # Prepare algorithm parameters
        algorithm_params = {}
        if min_support is not None:
            algorithm_params['min_support'] = min_support
        if min_confidence is not None:
            algorithm_params['min_confidence'] = min_confidence
        if min_lift is not None:
            algorithm_params['min_lift'] = min_lift
        if max_recommendations is not None:
            algorithm_params['max_recommendations'] = max_recommendations
        if decay_rate is not None:
            algorithm_params['decay_rate'] = decay_rate
        
        # Use the clean mining service for all operations
        mining_service = CleanAssociationMiningService(
            task_id=task_id, 
            task_manager=task_manager,
            algorithm_params=algorithm_params
        )
        
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
                    "total_rules": len(recommendations),  # Show actual total generated
                    "displayed_rules": len(rules_for_ui),  # Show how many are displayed in UI
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

def run_fast_mining_task(task_id: str, days_back=None, db_config=None):
    """
    FAST mining background task - optimized for speed and top 100 SKUs.
    - Uses 15% support (configured in .env)
    - Fetches top 100 most frequent SKUs only
    - Skips complex temporal analysis
    - Writes directly to database
    - Estimated completion: 2-5 minutes
    """
    try:
        import pandas as pd
        from mlxtend.frequent_patterns import fpgrowth, association_rules
        from mlxtend.preprocessing import TransactionEncoder
        
        # Mark task as started
        task_manager.start_task(task_id, "Initializing FAST mining...")
        logger.info(f"Starting FAST mining for top 100 SKUs - task {task_id}")
        
        # Initialize database connection
        if db_config:
            db = DatabaseConnection(custom_config=db_config)
        else:
            db = DatabaseConnection()
        
        # Connect to database
        task_manager.update_progress(task_id, 0.1, "Connecting to database...")
        if not db.connect():
            task_manager.fail_task(task_id, "Failed to connect to database")
            return
        
        # Fetch data with filtering for top 100 SKUs
        task_manager.update_progress(task_id, 0.2, "Fetching top 100 most frequent SKUs...")
        df_basket = db.fetch_order_data(days_back=days_back, max_items=100, min_item_frequency=10)
        
        if df_basket is None or df_basket.empty:
            task_manager.fail_task(task_id, "No data found for mining")
            return
        
        unique_skus = len(df_basket['SKU_NAME'].unique())
        unique_orders = len(df_basket['ORDER_ID'].unique())
        logger.info(f"FAST mode: Processing {unique_skus} SKUs from {unique_orders} orders")
        
        # Create simple transactions (no time weighting for speed)
        task_manager.update_progress(task_id, 0.3, f"Creating transactions from {unique_orders} orders...")
        transactions = df_basket.groupby('ORDER_ID')['SKU_NAME'].apply(list).tolist()
        logger.info(f"Created {len(transactions)} transactions")
        
        # Create transaction matrix
        task_manager.update_progress(task_id, 0.4, "Building transaction matrix...")
        te = TransactionEncoder()
        onehot = te.fit(transactions).transform(transactions)
        basket_matrix = pd.DataFrame(onehot, columns=te.columns_)
        
        num_items = basket_matrix.shape[0]
        num_transactions = basket_matrix.shape[1]
        density = (basket_matrix.sum().sum() / (num_items * num_transactions) * 100)
        logger.info(f"Transaction matrix: ({num_items}, {num_transactions}), Density: {density:.2f}%")
        
        # Run FP-Growth with 15% support
        from app.shared.config.config import config
        support = config.MIN_SUPPORT  # Should be 0.15 from .env
        
        task_manager.update_progress(task_id, 0.5, f"Mining patterns (support={support*100:.0f}%)...")
        logger.info(f"Starting FP-Growth with {support*100:.0f}% support...")
        
        freq_itemsets = fpgrowth(basket_matrix, min_support=support, use_colnames=True)
        logger.info(f"Found {len(freq_itemsets)} frequent itemsets")
        
        if freq_itemsets.empty:
            task_manager.fail_task(task_id, f"No frequent itemsets found with {support*100:.0f}% support")
            return
        
        # Generate association rules
        task_manager.update_progress(task_id, 0.6, "Generating association rules...")
        rules = association_rules(
            freq_itemsets, 
            metric="lift", 
            min_threshold=config.MIN_LIFT
        )
        
        rules = rules[rules['confidence'] >= config.MIN_CONFIDENCE]
        logger.info(f"Generated {len(rules)} rules (confidence >= {config.MIN_CONFIDENCE*100:.0f}%)")
        
        if rules.empty:
            task_manager.fail_task(task_id, "No rules met confidence threshold")
            return
        
        # Create recommendations from rules
        task_manager.update_progress(task_id, 0.7, "Creating recommendations...")
        recommendations_list = []
        
        for _, rule in rules.iterrows():
            antecedents = list(rule['antecedents'])
            consequents = list(rule['consequents'])
            
            # Create recommendation for each antecedent-consequent pair
            for ant in antecedents:
                for cons in consequents:
                    recommendations_list.append({
                        'main_item_id': ant,
                        'recommended_item_id': cons,
                        'support': rule['support'],
                        'confidence': rule['confidence'],
                        'lift': rule['lift'],
                        'composite_score': rule['confidence'] * rule['lift']
                    })
        
        recommendations = pd.DataFrame(recommendations_list)
        
        # Filter to top 100 SKUs recommendations only
        top_skus = df_basket['SKU_NAME'].value_counts().head(100).index.tolist()
        recommendations = recommendations[recommendations['main_item_id'].isin(top_skus)]
        
        # Keep top 10 recommendations per SKU
        recommendations = recommendations.sort_values(['main_item_id', 'composite_score'], ascending=[True, False])
        recommendations = recommendations.groupby('main_item_id').head(config.MAX_RECOMMENDATIONS)
        
        logger.info(f"Created {len(recommendations)} recommendations for top {len(top_skus)} SKUs")
        
        # Save directly to database
        task_manager.update_progress(task_id, 0.8, "Writing to database...")
        success = db.save_recommendations(recommendations)
        
        # Complete task
        result = {
            "recommendations_count": len(recommendations),
            "target_skus": len(top_skus),
            "rules_generated": len(rules),
            "database_saved": success,
            "stats": {
                "total_skus_processed": unique_skus,
                "total_orders": unique_orders,
                "support_used": f"{support*100:.0f}%",
                "mode": "FAST"
            }
        }
        
        if success:
            task_manager.complete_task(
                task_id,
                result=result,
                message=f"FAST mining completed: {len(recommendations)} recommendations for top {len(top_skus)} SKUs saved to database"
            )
            logger.info(f"FAST mining SUCCESS: {len(recommendations)} recommendations saved")
        else:
            task_manager.fail_task(task_id, "Database save failed")
            
    except Exception as e:
        error_msg = f"Error in FAST mining: {str(e)}"
        task_manager.fail_task(task_id, error_msg)
        logger.error(error_msg, exc_info=True)
    
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
                "min_support": request.min_support,
                "min_confidence": request.min_confidence,
                "min_lift": request.min_lift,
                "max_recommendations": request.max_recommendations,
                "decay_rate": request.decay_rate,
                "use_enhanced_mining": request.use_enhanced_mining,
                "time_weighting_method": request.time_weighting_method,
                "time_segmentation": request.time_segmentation,
                "db_config": request.db_config.model_dump() if request.db_config else None
            }
        )
        
        # Convert db_config to dict if provided
        db_config_dict = request.db_config.model_dump() if request.db_config else None
        
        # Add mining task to background
        background_tasks.add_task(
            run_mining_task,
            task_id=task_id,
            days_back=request.days_back,
            min_support=request.min_support,
            min_confidence=request.min_confidence,
            min_lift=request.min_lift,
            max_recommendations=request.max_recommendations,
            decay_rate=request.decay_rate,
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

@router.post("/mine-rules-fast", response_model=MiningStatusResponse)
async def mine_rules_fast(
    request: MiningRequest,
    background_tasks: BackgroundTasks
):
    """
    FAST mining mode - optimized for top 100 SKUs with direct database write.
    Uses higher support (15%), fewer items, and skips complex temporal analysis.
    Completes in 2-5 minutes instead of 90+ minutes.
    """
    try:
        # Create a new task
        task_id = task_manager.create_task(
            task_type="fast_mining",
            metadata={
                "days_back": request.days_back,
                "mode": "fast",
                "target_skus": 100,
                "db_config": request.db_config.dict() if request.db_config else None
            }
        )
        
        # Convert db_config to dict if provided
        db_config_dict = request.db_config.dict() if request.db_config else None
        
        # Add FAST mining task to background
        background_tasks.add_task(
            run_fast_mining_task,
            task_id=task_id,
            days_back=request.days_back,
            db_config=db_config_dict
        )
        
        return MiningStatusResponse(
            status="started",
            task_id=task_id,
            message="FAST mining started - targeting top 100 SKUs with direct database write (estimated 2-5 minutes)"
        )
    
    except Exception as e:
        logger.error(f"Error starting fast mining: {e}")
        raise HTTPException(status_code=500, detail="Failed to start fast mining process")

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