"""
AI Insights Module for Order Data and Inventory Analysis
Provides intelligent analytics and recommendations for warehouse optimization
"""

from .services.ai_insights_service import AIInsightsService
from .services.inventory_optimization_service import InventoryOptimizationService
from .services.demand_forecasting_service import DemandForecastingService
from .api.endpoints import register_ai_insights_routes, AIInsightsAPI

__all__ = [
    'AIInsightsService', 
    'InventoryOptimizationService', 
    'DemandForecastingService',
    'register_ai_insights_routes',
    'AIInsightsAPI'
]