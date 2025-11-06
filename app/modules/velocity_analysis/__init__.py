"""
Velocity Analysis Module

This module provides SKU and bin velocity analysis functionality for warehouse optimization.

Features:
- SKU velocity calculation (1, 2, 3) based on order patterns with time decay
- Bin composite velocity scoring based on SKU composition (1, 2, 4, 6 SKUs per bin)
- Weekly automated processing for bin optimization decisions
- REST API endpoints for velocity analysis
- Integration with existing association mining system

Components:
- services/velocity_service.py: Core velocity calculation algorithms
- api/velocity_endpoints.py: REST API endpoints
- ui/: Web interface components (future implementation)

Usage:
    from app.modules.velocity_analysis.services.velocity_service import VelocityAnalysisService
    
    service = VelocityAnalysisService(db_config)
    service.connect_database()
    result = service.calculate_sku_velocities()
"""

from .services.velocity_service import VelocityAnalysisService
from .api.velocity_endpoints import register_velocity_api, velocity_bp

__all__ = ['VelocityAnalysisService', 'register_velocity_api', 'velocity_bp']

__version__ = "1.0.0"
__author__ = "Association Mining System Team"