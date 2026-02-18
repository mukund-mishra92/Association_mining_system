from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.modules.association_mining.api.scheduler_endpoints import router as scheduler_router
from app.modules.association_mining.services.scheduler_service import get_scheduler_service
from app.shared.config.config import config
import logging
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=config.API_TITLE,
    version=config.API_VERSION,
    description=config.API_DESCRIPTION
)

@app.on_event("startup")
async def startup_event():
    """Initialize and start the scheduler when the application starts"""
    try:
        logger.info("🚀 Starting application startup sequence...")
        
        # Get or create the scheduler service
        scheduler = get_scheduler_service()
        
        # Check if scheduler is already running
        if scheduler.is_running and scheduler.scheduler.running:
            logger.info("ℹ️ Scheduler service already running")
            return
        
        # Start the scheduler
        try:
            logger.info("📋 Initializing scheduler service...")
            scheduler.start()
            logger.info("✅ Scheduler service started successfully")
        except Exception as start_error:
            logger.error(f"❌ Error starting scheduler: {start_error}", exc_info=True)
            logger.warning("⚠️ Application will continue without scheduler - schedules can be managed via API")
            
    except Exception as e:
        logger.error(f"❌ Failed in startup_event: {e}", exc_info=True)
        logger.warning("⚠️ Application will continue with limited functionality")
        
@app.on_event("shutdown")
async def shutdown_event():
    """Stop the scheduler when the application shuts down"""
    try:
        logger.info("🛑 Starting application shutdown sequence...")
        
        scheduler = get_scheduler_service()
        if scheduler.is_running:
            scheduler.stop()
            logger.info("✅ Scheduler service stopped successfully")
            
    except Exception as e:
        logger.error(f"❌ Error during scheduler shutdown: {e}")

# Include routers
app.include_router(scheduler_router, prefix="/api/v1/scheduler", tags=["Scheduler"])

@app.get("/")
async def root():
    return {"message": "Association Rule Mining API", "version": config.API_VERSION}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    """Serve the navigation dashboard page"""
    template_path = Path(__file__).parent / "web" / "templates" / "navigation_dashboard.html"
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)