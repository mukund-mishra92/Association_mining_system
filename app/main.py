from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.modules.association_mining.api.endpoints import router
from app.modules.neo_chatbot.api.chatbot_endpoints import router as chatbot_router
from app.shared.config.config import config
import logging
from pathlib import Path

# Create FastAPI app
app = FastAPI(
    title=config.API_TITLE,
    version=config.API_VERSION,
    description=config.API_DESCRIPTION
)

# Include routers
app.include_router(router, prefix="/api/v1")
app.include_router(chatbot_router)  # Chatbot API routes (already has /api/chatbot prefix)

@app.get("/")
async def root():
    return {"message": "Association Rule Mining API", "version": config.API_VERSION}

@app.get("/chatbot", response_class=HTMLResponse)
async def chatbot_page():
    """Serve the chatbot UI page"""
    template_path = Path(__file__).parent / "web" / "templates" / "chatbot.html"
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    """Serve the navigation dashboard page"""
    template_path = Path(__file__).parent / "web" / "templates" / "navigation_dashboard.html"
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)