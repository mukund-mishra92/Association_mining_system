"""
NEO Chatbot API Endpoints
FastAPI routes for chatbot functionality
"""

import logging
import uuid
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pathlib import Path

from ..models.schemas import (
    ChatRequest, 
    ChatResponse, 
    ChatbotType,
    SQLQueryRequest,
    SQLQueryResponse,
    SystemHealthStatus
)
from ..services.knowledge_base_service import KnowledgeBaseService
from ..services.sql_assistant_service import SQLAssistantService
from ..services.diagnostic_service import DiagnosticService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/chatbot", tags=["NEO Chatbot"])

# Initialize services
kb_service = KnowledgeBaseService()
sql_service = SQLAssistantService()
diagnostic_service = DiagnosticService()

# Session storage (in production, use Redis or database)
chat_sessions: Dict[str, list] = {}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint - routes to appropriate service based on chatbot type
    """
    try:
        logger.info(f"📨 Chat request: type={request.chatbot_type}, message={request.message[:50]}...")
        
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []
        
        # Add user message to history
        chat_sessions[session_id].append({
            "role": "user",
            "content": request.message
        })
        
        # Route to appropriate service
        if request.chatbot_type == ChatbotType.KNOWLEDGE_BASE:
            response = kb_service.process_query(request)
        elif request.chatbot_type == ChatbotType.SQL_ASSISTANT:
            response = sql_service.process_query(request)
        elif request.chatbot_type == ChatbotType.DIAGNOSTIC:
            response = diagnostic_service.process_query(request)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid chatbot type: {request.chatbot_type}")
        
        # Add assistant response to history
        chat_sessions[session_id].append({
            "role": "assistant",
            "content": response.response
        })
        
        logger.info(f"✅ Chat response generated: confidence={response.confidence_score:.2f}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sql-query", response_model=SQLQueryResponse)
async def execute_sql_query(request: SQLQueryRequest):
    """
    Generate SQL query from natural language
    Note: Does not execute query, only generates it
    """
    try:
        logger.info(f"🔍 SQL query request: {request.query[:50]}...")
        
        chat_request = ChatRequest(
            message=request.query,
            chatbot_type=ChatbotType.SQL_ASSISTANT,
            session_id=request.session_id
        )
        
        response = sql_service.process_query(chat_request)
        
        # Extract SQL from response
        sql_query = sql_service._extract_sql_query(response.response)
        
        return SQLQueryResponse(
            query=request.query,
            generated_sql=sql_query,
            explanation=response.response,
            confidence_score=response.confidence_score,
            session_id=response.session_id
        )
        
    except Exception as e:
        logger.error(f"❌ Error in SQL query endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form("general")
):
    """
    Upload a document to the knowledge base
    Supports: PDF, DOCX, TXT
    """
    try:
        logger.info(f"📤 Uploading document: {file.filename}")
        
        # Validate file type
        allowed_extensions = {".pdf", ".docx", ".txt"}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save file temporarily
        upload_dir = Path(__file__).parent.parent / "data" / "documents"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Ingest document
        result = kb_service.ingest_document(str(file_path), category)
        
        logger.info(f"✅ Document uploaded and indexed: {file.filename}")
        return {
            "filename": file.filename,
            "category": category,
            "size_bytes": len(content),
            "status": "success",
            "message": f"Document uploaded and indexed successfully. {result.get('chunks', 0)} chunks created."
        }
        
    except Exception as e:
        logger.error(f"❌ Error uploading document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-health", response_model=SystemHealthStatus)
async def get_system_health():
    """
    Get current system health status
    """
    try:
        logger.info("🏥 Checking system health...")
        health_status = diagnostic_service.check_system_health()
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Error checking system health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics():
    """
    Get chatbot statistics and metrics
    """
    try:
        kb_stats = kb_service.get_statistics()
        sql_stats = sql_service.get_statistics()
        diag_stats = diagnostic_service.get_statistics()
        
        return {
            "knowledge_base": kb_stats,
            "sql_assistant": sql_stats,
            "diagnostic": diag_stats,
            "total_sessions": len(chat_sessions)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """
    Clear a chat session history
    """
    try:
        if session_id in chat_sessions:
            del chat_sessions[session_id]
            logger.info(f"🗑️ Cleared session: {session_id}")
            return {"status": "success", "message": f"Session {session_id} cleared"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error clearing session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/history")
async def get_session_history(session_id: str):
    """
    Get chat history for a session
    """
    try:
        if session_id in chat_sessions:
            return {
                "session_id": session_id,
                "messages": chat_sessions[session_id]
            }
        else:
            return {
                "session_id": session_id,
                "messages": []
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting session history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Simple health check endpoint
    """
    return {
        "status": "healthy",
        "service": "NEO Chatbot API",
        "version": "1.0.0"
    }
