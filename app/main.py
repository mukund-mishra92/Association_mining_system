from fastapi import FastAPI
from app.api.endpoints import router
from app.utils.config import config
from app.utils.logger_config import setup_detailed_logging
import logging

# Setup detailed logging
log_files = setup_detailed_logging()

# Create FastAPI app
app = FastAPI(
    title=config.API_TITLE,
    version=config.API_VERSION,
    description=config.API_DESCRIPTION
)

# Include routers
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Association Rule Mining API", "version": config.API_VERSION}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)