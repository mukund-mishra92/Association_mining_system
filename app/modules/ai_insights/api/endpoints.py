"""
AI Insights API Endpoints
Flask REST API for AI-powered warehouse insights
"""

from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List
import traceback

# Import AI services
from ..services.ai_insights_service import AIInsightsService
from ..services.inventory_optimization_service import InventoryOptimizationService
from ..services.demand_forecasting_service import DemandForecastingService


class AIInsightsAPI:
    def __init__(self, app: Flask, db_config: Dict[str, Any]):
        """Initialize AI Insights API with Flask app and database config"""
        self.app = app
        self.db_config = db_config
        
        # Initialize services
        self.ai_insights_service = AIInsightsService(db_config)
        self.inventory_service = InventoryOptimizationService(db_config)
        self.forecasting_service = DemandForecastingService(db_config)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register all API routes"""
        
        @self.app.route('/api/ai-insights/order-patterns', methods=['GET'])
        def get_ai_order_patterns():
            """Get comprehensive order pattern analysis"""
            try:
                # Get parameters
                days_back = request.args.get('days', 30, type=int)
                start_date = request.args.get('start_date')
                end_date = request.args.get('end_date')
                
                # Validate parameters
                if not start_date and not end_date:
                    if days_back < 7 or days_back > 365:
                        return jsonify({
                            'error': 'days parameter must be between 7 and 365',
                            'status': 'error'
                        }), 400
                
                # Get order pattern analysis
                if start_date and end_date:
                    result = self.ai_insights_service.analyze_order_patterns(
                        start_date=start_date, end_date=end_date
                    )
                else:
                    result = self.ai_insights_service.analyze_order_patterns(
                        days_back=days_back
                    )
                
                if 'error' in result:
                    return jsonify({
                        'error': result['error'],
                        'status': 'error'
                    }), 500
                
                return jsonify({
                    'data': result,
                    'status': 'success',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Error in order patterns endpoint: {str(e)}")
                return jsonify({
                    'error': 'Internal server error',
                    'details': str(e),
                    'status': 'error'
                }), 500

        @self.app.route('/api/ai-insights/inventory-optimization', methods=['GET'])
        def get_ai_inventory_optimization():
            """Get comprehensive inventory optimization analysis"""
            try:
                # Get parameters
                analysis_days = request.args.get('analysis_days', 90, type=int)
                start_date = request.args.get('start_date')
                end_date = request.args.get('end_date')
                include_recommendations = request.args.get('recommendations', 'true').lower() == 'true'
                min_turnover_threshold = request.args.get('min_turnover', 2.0, type=float)
                
                # Validate parameters
                if not start_date and not end_date:
                    if analysis_days < 30 or analysis_days > 365:
                        return jsonify({
                            'error': 'analysis_days must be between 30 and 365',
                            'status': 'error'
                        }), 400
                
                # Get inventory optimization analysis
                if start_date and end_date:
                    result = self.inventory_service.comprehensive_inventory_analysis(
                        start_date=start_date, end_date=end_date
                    )
                else:
                    result = self.inventory_service.comprehensive_inventory_analysis(
                        days_back=analysis_days
                    )
                
                if 'error' in result:
                    return jsonify({
                        'error': result['error'],
                        'status': 'error'
                    }), 500
                
                return jsonify({
                    'data': result,
                    'status': 'success',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Error in inventory optimization endpoint: {str(e)}")
                return jsonify({
                    'error': 'Internal server error',
                    'details': str(e),
                    'status': 'error'
                }), 500

        @self.app.route('/api/ai-insights/demand-forecast', methods=['GET'])
        def get_ai_demand_forecast():
            """Get comprehensive demand forecasting analysis"""
            try:
                # Get parameters
                forecast_days = request.args.get('forecast_days', 30, type=int)
                analysis_days = request.args.get('analysis_days', 90, type=int)
                
                # Validate parameters
                if forecast_days < 7 or forecast_days > 90:
                    return jsonify({
                        'error': 'forecast_days must be between 7 and 90',
                        'status': 'error'
                    }), 400
                
                if analysis_days < 30 or analysis_days > 365:
                    return jsonify({
                        'error': 'analysis_days must be between 30 and 365',
                        'status': 'error'
                    }), 400
                
                # Get demand forecasting analysis
                result = self.forecasting_service.comprehensive_demand_forecast(
                    forecast_days=forecast_days,
                    analysis_days=analysis_days
                )
                
                if 'error' in result:
                    return jsonify({
                        'error': result['error'],
                        'status': 'error'
                    }), 500
                
                return jsonify({
                    'data': result,
                    'status': 'success',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Error in demand forecast endpoint: {str(e)}")
                return jsonify({
                    'error': 'Internal server error',
                    'details': str(e),
                    'status': 'error'
                }), 500

        @self.app.route('/api/ai-insights/sku-performance', methods=['GET'])
        def get_ai_sku_performance():
            """Get SKU performance analysis"""
            try:
                # Get parameters
                days_back = request.args.get('days', 30, type=int)
                top_n = request.args.get('top_n', 20, type=int)
                
                # Validate parameters
                if days_back < 7 or days_back > 365:
                    return jsonify({
                        'error': 'days parameter must be between 7 and 365',
                        'status': 'error'
                    }), 400
                
                if top_n < 5 or top_n > 100:
                    return jsonify({
                        'error': 'top_n must be between 5 and 100',
                        'status': 'error'
                    }), 400
                
                # Get SKU performance from order patterns analysis
                full_analysis = self.ai_insights_service.analyze_order_patterns(
                    days_back=days_back
                )
                
                if 'error' in full_analysis:
                    return jsonify({
                        'error': full_analysis['error'],
                        'status': 'error'
                    }), 500
                
                # Extract SKU performance data
                sku_performance = full_analysis.get('sku_performance', {})
                
                # Limit to top N SKUs
                if 'top_skus' in sku_performance:
                    sku_performance['top_skus'] = sku_performance['top_skus'][:top_n]
                
                return jsonify({
                    'data': {
                        'sku_performance': sku_performance,
                        'analysis_period': full_analysis.get('analysis_period'),
                        'summary_stats': full_analysis.get('summary_stats')
                    },
                    'status': 'success',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Error in SKU performance endpoint: {str(e)}")
                return jsonify({
                    'error': 'Internal server error',
                    'details': str(e),
                    'status': 'error'
                }), 500

        @self.app.route('/api/ai-insights/abc-analysis', methods=['GET'])
        def get_ai_abc_analysis():
            """Get ABC classification analysis"""
            try:
                # Get parameters
                analysis_days = request.args.get('analysis_days', 90, type=int)
                
                # Validate parameters
                if analysis_days < 30 or analysis_days > 365:
                    return jsonify({
                        'error': 'analysis_days must be between 30 and 365',
                        'status': 'error'
                    }), 400
                
                # Get inventory analysis
                full_analysis = self.inventory_service.comprehensive_inventory_analysis(
                    days_back=analysis_days
                )
                
                if 'error' in full_analysis:
                    return jsonify({
                        'error': full_analysis['error'],
                        'status': 'error'
                    }), 500
                
                # Extract ABC analysis data
                abc_data = {
                    'abc_analysis': full_analysis.get('abc_analysis', {}),
                    'analysis_period': full_analysis.get('analysis_period', {}),
                    'summary_stats': full_analysis.get('summary_statistics', {})
                }
                
                return jsonify({
                    'data': abc_data,
                    'status': 'success',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Error in ABC analysis endpoint: {str(e)}")
                return jsonify({
                    'error': 'Internal server error',
                    'details': str(e),
                    'status': 'error'
                }), 500

        @self.app.route('/api/ai-insights/seasonal-analysis', methods=['GET'])
        def get_ai_seasonal_analysis():
            """Get seasonal pattern analysis"""
            try:
                # Get parameters
                forecast_days = request.args.get('forecast_days', 30, type=int)
                analysis_days = request.args.get('analysis_days', 90, type=int)
                start_date = request.args.get('start_date')
                end_date = request.args.get('end_date')
                
                # Get demand forecasting analysis
                if start_date and end_date:
                    full_analysis = self.forecasting_service.comprehensive_demand_forecast(
                        forecast_days=forecast_days,
                        start_date=start_date,
                        end_date=end_date
                    )
                else:
                    full_analysis = self.forecasting_service.comprehensive_demand_forecast(
                        forecast_days=forecast_days,
                        analysis_days=analysis_days
                    )
                
                if 'error' in full_analysis:
                    return jsonify({
                        'error': full_analysis['error'],
                        'status': 'error'
                    }), 500
                
                # Extract seasonal analysis data
                seasonal_data = {
                    'seasonal_analysis': full_analysis.get('seasonal_analysis', {}),
                    'forecast_period': full_analysis.get('forecast_period', {}),
                    'overall_forecast': full_analysis.get('overall_forecast', {})
                }
                
                return jsonify({
                    'data': seasonal_data,
                    'status': 'success',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Error in seasonal analysis endpoint: {str(e)}")
                return jsonify({
                    'error': 'Internal server error',
                    'details': str(e),
                    'status': 'error'
                }), 500

        @self.app.route('/api/ai-insights/recommendations', methods=['GET'])
        def get_ai_recommendations():
            """Get AI-powered recommendations"""
            try:
                # Get parameters
                analysis_days = request.args.get('analysis_days', 90, type=int)
                forecast_days = request.args.get('forecast_days', 30, type=int)
                
                # Get comprehensive analysis from all services
                order_analysis = self.ai_insights_service.analyze_order_patterns(days_back=analysis_days)
                inventory_analysis = self.inventory_service.comprehensive_inventory_analysis(days_back=analysis_days)
                forecast_analysis = self.forecasting_service.comprehensive_demand_forecast(
                    forecast_days=forecast_days, analysis_days=analysis_days
                )
                
                # Compile recommendations
                recommendations = {
                    'order_insights': order_analysis.get('recommendations', []),
                    'inventory_optimization': inventory_analysis.get('recommendations', []),
                    'demand_forecasting': forecast_analysis.get('recommendations', []),
                    'risk_analysis': forecast_analysis.get('risk_analysis', {}),
                    'priority_actions': self._generate_priority_actions(
                        order_analysis, inventory_analysis, forecast_analysis
                    )
                }
                
                return jsonify({
                    'data': recommendations,
                    'status': 'success',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Error in recommendations endpoint: {str(e)}")
                return jsonify({
                    'error': 'Internal server error',
                    'details': str(e),
                    'status': 'error'
                }), 500

        @self.app.route('/api/ai-insights/dashboard-summary', methods=['GET'])
        def get_ai_dashboard_summary():
            """Get comprehensive dashboard summary"""
            try:
                # Get parameters with defaults for dashboard
                analysis_days = request.args.get('analysis_days', 30, type=int)
                forecast_days = request.args.get('forecast_days', 14, type=int)
                start_date = request.args.get('start_date')
                end_date = request.args.get('end_date')
                
                # If custom date range is provided, use it instead of analysis_days
                date_params = {}
                if start_date and end_date:
                    date_params = {'start_date': start_date, 'end_date': end_date}
                else:
                    date_params = {'days_back': analysis_days}
                
                # Get quick analysis from all services (reduced scope for dashboard)
                if 'start_date' in date_params:
                    order_patterns = self.ai_insights_service.analyze_order_patterns(
                        start_date=date_params['start_date'], 
                        end_date=date_params['end_date']
                    )
                    inventory_analysis = self.inventory_service.comprehensive_inventory_analysis(
                        start_date=date_params['start_date'], 
                        end_date=date_params['end_date']
                    )
                    forecast_analysis = self.forecasting_service.comprehensive_demand_forecast(
                        forecast_days=forecast_days, 
                        start_date=date_params['start_date'], 
                        end_date=date_params['end_date']
                    )
                else:
                    order_patterns = self.ai_insights_service.analyze_order_patterns(
                        days_back=date_params['days_back']
                    )
                    inventory_analysis = self.inventory_service.comprehensive_inventory_analysis(
                        days_back=date_params['days_back']
                    )
                    forecast_analysis = self.forecasting_service.comprehensive_demand_forecast(
                        forecast_days=forecast_days, 
                        analysis_days=date_params['days_back']
                    )
                
                # Create dashboard summary
                analysis_period = order_patterns.get('analysis_period', {})
                daily_stats = order_patterns.get('daily_patterns', {}).get('daily_statistics', {})
                
                # Calculate average daily orders
                total_orders = analysis_period.get('total_orders', 0)
                total_days = analysis_period.get('total_days', 1)
                avg_daily_orders = total_orders / total_days if total_days > 0 else 0
                
                summary = {
                    'key_metrics': {
                        'total_orders': total_orders,
                        'total_skus': analysis_period.get('unique_skus', 0),
                        'avg_daily_orders': round(avg_daily_orders, 2),
                        'forecast_accuracy': forecast_analysis.get('accuracy_metrics', {}).get('overall_accuracy', {}).get('accuracy_grade', 'Unknown')
                    },
                    'trends': {
                        'order_trend': order_patterns.get('daily_patterns', {}).get('trend_analysis', {}),
                        'demand_forecast': forecast_analysis.get('overall_forecast', {}),
                        'seasonal_strength': forecast_analysis.get('seasonal_analysis', {}).get('seasonality_strength', {})
                    },
                    'alerts': self._generate_dashboard_alerts(order_patterns, inventory_analysis, forecast_analysis),
                    'top_performers': {
                        'top_skus': order_patterns.get('sku_analysis', {}).get('top_performing_skus', [])[:5],
                        'abc_summary': inventory_analysis.get('abc_analysis', {}).get('category_summary', {})
                    },
                    'risk_indicators': {
                        'overall_risk': forecast_analysis.get('risk_analysis', {}).get('overall_risk_level', 'Low'),
                        'high_risk_skus': len([f for f in forecast_analysis.get('sku_forecasts', []) if f.get('risk_level') == 'High'])
                    }
                }
                
                return jsonify({
                    'data': summary,
                    'status': 'success',
                    'timestamp': datetime.now().isoformat(),
                    'refresh_interval': 300  # 5 minutes
                })
                
            except Exception as e:
                self.logger.error(f"Error in dashboard summary endpoint: {str(e)}")
                return jsonify({
                    'error': 'Internal server error',
                    'details': str(e),
                    'status': 'error'
                }), 500

        @self.app.route('/api/ai-insights/health', methods=['GET'])
        def ai_insights_health_check():
            """Health check endpoint for AI insights services"""
            try:
                # Test database connections
                services_status = {
                    'ai_insights_service': self._test_service_health(self.ai_insights_service),
                    'inventory_service': self._test_service_health(self.inventory_service),
                    'forecasting_service': self._test_service_health(self.forecasting_service)
                }
                
                all_healthy = all(services_status.values())
                
                return jsonify({
                    'status': 'healthy' if all_healthy else 'degraded',
                    'services': services_status,
                    'timestamp': datetime.now().isoformat()
                }), 200 if all_healthy else 503
                
            except Exception as e:
                return jsonify({
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

    def _generate_priority_actions(self, order_analysis: Dict, inventory_analysis: Dict, forecast_analysis: Dict) -> List[Dict]:
        """Generate prioritized action items from all analyses"""
        actions = []
        
        # High priority actions based on risk analysis
        risk_analysis = forecast_analysis.get('risk_analysis', {})
        if risk_analysis.get('overall_risk_level') == 'High':
            actions.append({
                'priority': 'High',
                'category': 'Risk Management',
                'action': 'Review high-risk SKU forecasts and adjust safety stock levels',
                'impact': 'Prevent stockouts and excess inventory'
            })
        
        # Inventory optimization actions
        slow_moving = inventory_analysis.get('slow_moving_analysis', {})
        if slow_moving.get('slow_moving_skus'):
            actions.append({
                'priority': 'Medium',
                'category': 'Inventory Optimization',
                'action': f'Review {len(slow_moving["slow_moving_skus"])} slow-moving SKUs for liquidation or reorder reduction',
                'impact': 'Reduce carrying costs and free up warehouse space'
            })
        
        # Order pattern actions
        seasonal_insights = forecast_analysis.get('seasonal_analysis', {}).get('seasonal_insights', [])
        if seasonal_insights:
            actions.append({
                'priority': 'Medium',
                'category': 'Seasonal Planning',
                'action': 'Adjust staffing and inventory levels based on seasonal patterns',
                'impact': 'Optimize resource allocation and improve service levels'
            })
        
        return sorted(actions, key=lambda x: {'High': 3, 'Medium': 2, 'Low': 1}[x['priority']], reverse=True)

    def _generate_dashboard_alerts(self, order_analysis: Dict, inventory_analysis: Dict, forecast_analysis: Dict) -> List[Dict]:
        """Generate alerts for dashboard display"""
        alerts = []
        
        # Risk-based alerts
        risk_level = forecast_analysis.get('risk_analysis', {}).get('overall_risk_level')
        if risk_level == 'High':
            alerts.append({
                'type': 'warning',
                'title': 'High Forecasting Risk',
                'message': 'Multiple SKUs show high demand variability',
                'action': 'Review forecast parameters'
            })
        
        # Inventory alerts
        slow_moving_count = len(inventory_analysis.get('slow_moving_analysis', {}).get('slow_moving_skus', []))
        if slow_moving_count > 5:
            alerts.append({
                'type': 'info',
                'title': 'Inventory Optimization Opportunity',
                'message': f'{slow_moving_count} slow-moving SKUs identified',
                'action': 'Review for liquidation'
            })
        
        # Trending alerts
        trending_skus = len([f for f in forecast_analysis.get('sku_forecasts', []) if abs(f.get('forecast_trend', 0)) > 0.1])
        if trending_skus > 3:
            alerts.append({
                'type': 'info',
                'title': 'Demand Trends Detected',
                'message': f'{trending_skus} SKUs show significant demand trends',
                'action': 'Monitor closely'
            })
        
        return alerts

    def _test_service_health(self, service) -> bool:
        """Test if a service can connect to database"""
        try:
            connection = service.get_connection()
            connection.close()
            return True
        except Exception as e:
            self.logger.error(f"Service health check failed: {str(e)}")
            return False


def register_ai_insights_routes(app: Flask, db_config: Dict[str, Any]):
    """Register AI insights routes with Flask app"""
    ai_api = AIInsightsAPI(app, db_config)
    return ai_api