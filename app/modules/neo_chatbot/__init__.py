"""
NEO Chatbot Module - Intelligent Assistant for NEO Warehouse Management System

Features:
1. Knowledge Base Chatbot: Answer questions about NEO documentation, code, and proposals
2. SQL Assistant: Convert natural language to SQL queries and show database insights
3. Diagnostic Support: Automated issue detection and solution recommendations

Author: NEO Development Team
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "NEO Development Team"

# Import main services for easy access
from .services.llm_service import LLMService
from .services.vector_store_service import VectorStoreService
from .services.knowledge_base_service import KnowledgeBaseService
from .services.sql_assistant_service import SQLAssistantService
from .services.diagnostic_service import DiagnosticService
from .services.agentic_service import AgenticService, get_agentic_service

__all__ = [
    'LLMService',
    'VectorStoreService',
    'KnowledgeBaseService',
    'SQLAssistantService',
    'DiagnosticService',
    'AgenticService',
    'get_agentic_service'
]
