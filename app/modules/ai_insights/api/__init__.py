"""
AI Insights API Module
Initialization for AI-powered warehouse insights API endpoints
"""

from .endpoints import register_ai_insights_routes, AIInsightsAPI

__all__ = ['register_ai_insights_routes', 'AIInsightsAPI']