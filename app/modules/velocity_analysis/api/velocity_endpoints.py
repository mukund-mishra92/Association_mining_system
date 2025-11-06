"""
Velocity Analysis API Module
Provides REST API endpoints for the bin velocity analysis system

This module handles:
- Database connection testing for velocity analysis
- SKU velocity calculation endpoints
- Bin velocity scoring endpoints  
- Weekly analysis scheduling
- Status monitoring and reporting
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, date, timedelta
import json
import logging
from typing import Dict, Any
import traceback

# Import the velocity service
from ..services.velocity_service import VelocityAnalysisService
from ..services.velocity_scheduler import create_scheduled_job_api_endpoints

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint for velocity analysis
velocity_bp = Blueprint('velocity_analysis', __name__, url_prefix='/api/velocity')

# Global service instance (will be initialized with database config)
velocity_service = None

@velocity_bp.route('/test-connection', methods=['POST'])
def test_velocity_database_connection():
    """
    Test database connection for velocity analysis using main app configuration
    
    No payload needed - uses main app's database configuration
    """
    try:
        # Import main app's database configuration and logging
        from app.web.main import USER_DB_CONFIG
        
        # Import logging system if available
        try:
            from app.utils.mining_logger import mining_logger
            LOGGING_AVAILABLE = True
        except ImportError:
            mining_logger = None
            LOGGING_AVAILABLE = False
        
        # Log the available configuration keys for debugging
        logger.info(f"Available USER_DB_CONFIG keys: {list(USER_DB_CONFIG.keys())}")
        logger.info(f"USER_DB_CONFIG content: {USER_DB_CONFIG}")
        
        # Use the main app's database configuration with proper field mapping
        db_config = {
            'host': USER_DB_CONFIG.get('host', 'localhost'),
            'user': USER_DB_CONFIG.get('user', 'root'),
            'password': USER_DB_CONFIG.get('password', ''),  # Handle missing password
            'database': USER_DB_CONFIG.get('database', 'neo'),
            'port': USER_DB_CONFIG.get('port', 3306)
        }
        
        logger.info(f"Testing velocity database connection with config: {db_config['host']}:{db_config['port']} database={db_config['database']} user={db_config['user']}")
        
        # Test connection
        test_service = VelocityAnalysisService(db_config)
        connection_success = test_service.connect_database()
        
        if connection_success:
            # Test if velocity tables exist
            tables_status = test_service._check_velocity_tables()
            test_service.disconnect_database()
            
            # Log successful velocity connection
            if mining_logger:
                mining_logger.log_velocity_analysis(
                    operation="database_connection_test",
                    parameters={"connection_type": "shared_config"},
                    results={"tables_status": tables_status},
                    success=True
                )
            
            logger.info("✅ Velocity analysis database connection successful using shared config")
            return jsonify({
                "success": True,
                "message": "Database connection successful using shared configuration",
                "tables_status": tables_status,
                "timestamp": datetime.now().isoformat(),
                "database_config": {
                    'host': db_config['host'],
                    'port': db_config['port'],
                    'database': db_config['database'],
                    'user': db_config['user']
                }
            })
        else:
            # Log failed velocity connection
            if mining_logger:
                mining_logger.log_velocity_analysis(
                    operation="database_connection_test",
                    parameters={"connection_type": "shared_config"},
                    success=False,
                    error="Database connection failed"
                )
            
            logger.error("❌ Velocity analysis database connection failed")
            return jsonify({
                "success": False,
                "message": "Database connection failed with shared configuration"
            }), 500
            
    except Exception as e:
        # Log velocity connection exception
        if mining_logger:
            mining_logger.log_velocity_analysis(
                operation="database_connection_test",
                parameters={"connection_type": "shared_config"},
                success=False,
                error=str(e)
            )
        
        logger.error(f"Database connection test failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Connection test error: {str(e)}"
        }), 500

@velocity_bp.route('/test-connection-custom', methods=['POST'])
def test_velocity_database_connection_custom():
    """
    Test database connection for velocity analysis using custom configuration
    
    Expected payload:
    {
        "host": "localhost",
        "user": "username", 
        "password": "password",
        "database": "database_name",
        "port": 3306
    }
    """
    try:
        db_config = request.get_json()
        
        if not db_config:
            return jsonify({
                "success": False,
                "message": "Database configuration required"
            }), 400
        
        # Validate required fields
        required_fields = ['host', 'user', 'database']
        missing_fields = [field for field in required_fields if field not in db_config or not db_config[field]]
        
        if missing_fields:
            return jsonify({
                "success": False,
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Set default port if not provided
        if 'port' not in db_config:
            db_config['port'] = 3306
            
        # Ensure password field exists
        if 'password' not in db_config:
            db_config['password'] = ''
            
        logger.info(f"Testing velocity database connection with custom config: {db_config['host']}:{db_config['port']} database={db_config['database']} user={db_config['user']}")
        
        # Test connection
        test_service = VelocityAnalysisService(db_config)
        connection_success = test_service.connect_database()
        
        if connection_success:
            # Test if velocity tables exist
            tables_status = test_service._check_velocity_tables()
            test_service.disconnect_database()
            
            logger.info("✅ Velocity analysis database connection successful using custom config")
            return jsonify({
                "success": True,
                "message": "Database connection successful using custom configuration",
                "tables_status": tables_status,
                "timestamp": datetime.now().isoformat(),
                "database_config": {
                    'host': db_config['host'],
                    'port': db_config['port'],
                    'database': db_config['database'],
                    'user': db_config['user']
                }
            })
        else:
            logger.error("❌ Velocity analysis database connection failed with custom config")
            return jsonify({
                "success": False,
                "message": "Database connection failed with custom configuration"
            }), 500
            
    except Exception as e:
        logger.error(f"Custom database connection test failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Connection test error: {str(e)}"
        }), 500

@velocity_bp.route('/save-config', methods=['POST'])
def save_velocity_config():
    """
    Save velocity analysis configuration for this session
    """
    try:
        config_data = request.get_json()
        
        if not config_data:
            return jsonify({
                "success": False,
                "message": "Configuration data required"
            }), 400
        
        # Store the configuration globally for this session
        # Note: This is session-based storage, not persistent
        global velocity_service
        velocity_service = VelocityAnalysisService(config_data)
        
        logger.info(f"Velocity analysis configuration saved for session: {config_data['host']}:{config_data['port']}")
        
        return jsonify({
            "success": True,
            "message": "Configuration saved successfully for this session",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to save velocity configuration: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Failed to save configuration: {str(e)}"
        }), 500

@velocity_bp.route('/initialize-database', methods=['POST'])
def initialize_velocity_database():
    """
    Initialize velocity analysis database tables
    
    Expected payload:
    {
        "host": "localhost",
        "user": "username",
        "password": "password", 
        "database": "database_name",
        "port": 3306,
        "create_tables": true
    }
    """
    try:
        config = request.get_json()
        db_config = {k: v for k, v in config.items() if k != 'create_tables'}
        
        service = VelocityAnalysisService(db_config)
        
        if not service.connect_database():
            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500
        
        # Create tables if requested
        if config.get('create_tables', False):
            result = service._create_velocity_tables()
            service.disconnect_database()
            
            return jsonify({
                "success": result["success"],
                "message": result["message"],
                "tables_created": result.get("tables_created", []),
                "timestamp": datetime.now().isoformat()
            })
        else:
            service.disconnect_database()
            return jsonify({
                "success": True,
                "message": "Database initialized (no tables created)",
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Initialization error: {str(e)}"
        }), 500

@velocity_bp.route('/calculate-sku-velocities', methods=['POST'])
def calculate_sku_velocities():
    """
    Calculate SKU velocity scores (1, 2, 3) based on order patterns
    
    Expected payload:
    {
        "db_config": {...},
        "analysis_date": "2025-11-04", // optional
        "parameters": {  // optional parameter overrides
            "analysis_period_days": 90,
            "time_decay_rate": 0.05,
            "min_orders_for_calculation": 5
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'db_config' not in data:
            return jsonify({
                "success": False,
                "message": "Database configuration required"
            }), 400
        
        # Initialize service
        service = VelocityAnalysisService(data['db_config'])
        
        if not service.connect_database():
            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500
        
        # Parse analysis date
        analysis_date = None
        if 'analysis_date' in data:
            try:
                analysis_date = datetime.strptime(data['analysis_date'], '%Y-%m-%d').date()
            except ValueError:
                service.disconnect_database()
                return jsonify({
                    "success": False,
                    "message": "Invalid date format. Use YYYY-MM-DD"
                }), 400
        
        # Override parameters if provided
        if 'parameters' in data:
            service._update_calculation_parameters(data['parameters'])
        
        # Run calculation
        result = service.calculate_sku_velocities(analysis_date)
        service.disconnect_database()
        
        return jsonify({
            **result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"SKU velocity calculation failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Calculation error: {str(e)}"
        }), 500

@velocity_bp.route('/calculate-sku-velocities-shared', methods=['POST'])
def calculate_sku_velocities_shared():
    """
    Calculate SKU velocity scores using shared database configuration
    
    Expected payload:
    {
        "analysis_date": "2025-11-04", // optional
        "parameters": {  // optional parameter overrides
            "analysis_period_days": 90,
            "time_decay_rate": 0.05,
            "min_orders_for_calculation": 5
        }
    }
    """
    try:
        # Import main app's database configuration and logging
        from app.web.main import USER_DB_CONFIG
        
        # Import logging system if available
        try:
            from app.utils.mining_logger import mining_logger
            LOGGING_AVAILABLE = True
        except ImportError:
            mining_logger = None
            LOGGING_AVAILABLE = False
        
        data = request.get_json() or {}
        
        # Use the main app's database configuration
        db_config = {
            'host': USER_DB_CONFIG.get('host', 'localhost'),
            'user': USER_DB_CONFIG.get('user', 'root'),
            'password': USER_DB_CONFIG.get('password', ''),
            'database': USER_DB_CONFIG.get('database', 'neo'),
            'port': USER_DB_CONFIG.get('port', 3306)
        }
        
        logger.info(f"Starting velocity calculation with shared config: {db_config['host']}:{db_config['port']} database={db_config['database']} user={db_config['user']}")
        
        # Initialize service
        service = VelocityAnalysisService(db_config)
        
        if not service.connect_database():
            # Log failed velocity calculation
            if mining_logger:
                mining_logger.log_velocity_analysis(
                    operation="sku_velocity_calculation",
                    parameters={"connection_type": "shared_config"},
                    success=False,
                    error="Database connection failed"
                )
            
            return jsonify({
                "success": False,
                "message": "Database connection failed with shared configuration"
            }), 500
        
        # Parse analysis date
        analysis_date = None
        if 'analysis_date' in data:
            try:
                analysis_date = datetime.strptime(data['analysis_date'], '%Y-%m-%d').date()
            except ValueError:
                service.disconnect_database()
                return jsonify({
                    "success": False,
                    "message": "Invalid date format. Use YYYY-MM-DD"
                }), 400
        
        # Override parameters if provided
        if 'parameters' in data:
            service._update_calculation_parameters(data['parameters'])
        
        # Run calculation
        result = service.calculate_sku_velocities(analysis_date)
        service.disconnect_database()
        
        # Log successful velocity calculation
        if mining_logger and result.get('success'):
            mining_logger.log_velocity_analysis(
                operation="sku_velocity_calculation",
                parameters={
                    "connection_type": "shared_config",
                    "analysis_date": str(analysis_date) if analysis_date else "today",
                    "parameters": data.get('parameters', {})
                },
                results=result.get('statistics', {}),
                success=True
            )
        elif mining_logger:
            mining_logger.log_velocity_analysis(
                operation="sku_velocity_calculation", 
                parameters={"connection_type": "shared_config"},
                success=False,
                error=result.get('message', 'Unknown error')
            )
        
        return jsonify({
            **result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        # Log velocity calculation exception
        if mining_logger:
            mining_logger.log_velocity_analysis(
                operation="sku_velocity_calculation",
                parameters={"connection_type": "shared_config"},
                success=False,
                error=str(e)
            )
        
        logger.error(f"SKU velocity calculation failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Calculation error: {str(e)}"
        }), 500

@velocity_bp.route('/calculate-bin-velocities', methods=['POST'])
def calculate_bin_velocities():
    """
    Calculate bin composite velocity scores based on SKU composition
    
    Expected payload:
    {
        "db_config": {...},
        "calculation_date": "2025-11-04" // optional
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'db_config' not in data:
            return jsonify({
                "success": False,
                "message": "Database configuration required"
            }), 400
        
        # Initialize service
        service = VelocityAnalysisService(data['db_config'])
        
        if not service.connect_database():
            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500
        
        # Parse calculation date
        calculation_date = None
        if 'calculation_date' in data:
            try:
                calculation_date = datetime.strptime(data['calculation_date'], '%Y-%m-%d').date()
            except ValueError:
                service.disconnect_database()
                return jsonify({
                    "success": False,
                    "message": "Invalid date format. Use YYYY-MM-DD"
                }), 400
        
        # Run calculation
        result = service.calculate_bin_velocities(calculation_date)
        service.disconnect_database()
        
        return jsonify({
            **result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Bin velocity calculation failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Calculation error: {str(e)}"
        }), 500

@velocity_bp.route('/calculate-bin-velocities-shared', methods=['POST'])
def calculate_bin_velocities_shared():
    """
    Calculate bin composite velocity scores using shared database configuration
    
    Expected payload:
    {
        "calculation_date": "2025-11-04" // optional
    }
    """
    try:
        # Import main app's database configuration
        from app.web.main import USER_DB_CONFIG
        
        # Import logging system if available
        try:
            from app.utils.mining_logger import mining_logger
            LOGGING_AVAILABLE = True
        except ImportError:
            mining_logger = None
            LOGGING_AVAILABLE = False
        
        data = request.get_json() or {}
        
        # Use the main app's database configuration
        db_config = {
            'host': USER_DB_CONFIG.get('host', 'localhost'),
            'user': USER_DB_CONFIG.get('user', 'root'),
            'password': USER_DB_CONFIG.get('password', ''),
            'database': USER_DB_CONFIG.get('database', 'neo'),
            'port': USER_DB_CONFIG.get('port', 3306)
        }
        
        logger.info(f"Starting bin velocity calculation with shared config: {db_config['host']}:{db_config['port']} database={db_config['database']} user={db_config['user']}")
        
        # Initialize service
        service = VelocityAnalysisService(db_config)
        
        if not service.connect_database():
            # Log failed bin velocity calculation
            if mining_logger:
                mining_logger.log_velocity_analysis(
                    operation="bin_velocity_calculation",
                    parameters={"connection_type": "shared_config"},
                    success=False,
                    error="Database connection failed"
                )
            
            return jsonify({
                "success": False,
                "message": "Database connection failed with shared configuration"
            }), 500
        
        # Parse calculation date
        calculation_date = None
        if 'calculation_date' in data:
            try:
                calculation_date = datetime.strptime(data['calculation_date'], '%Y-%m-%d').date()
            except ValueError:
                service.disconnect_database()
                return jsonify({
                    "success": False,
                    "message": "Invalid date format. Use YYYY-MM-DD"
                }), 400
        
        # Run calculation
        result = service.calculate_bin_velocities(calculation_date)
        service.disconnect_database()
        
        # Log bin velocity calculation result
        if mining_logger and result.get('success'):
            mining_logger.log_velocity_analysis(
                operation="bin_velocity_calculation",
                parameters={
                    "connection_type": "shared_config",
                    "calculation_date": str(calculation_date) if calculation_date else "today"
                },
                results=result.get('statistics', {}),
                success=True
            )
        elif mining_logger:
            mining_logger.log_velocity_analysis(
                operation="bin_velocity_calculation",
                parameters={"connection_type": "shared_config"},
                success=False,
                error=result.get('message', 'Unknown error')
            )
        
        return jsonify({
            **result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        # Log bin velocity calculation exception
        if mining_logger:
            mining_logger.log_velocity_analysis(
                operation="bin_velocity_calculation",
                parameters={"connection_type": "shared_config"},
                success=False,
                error=str(e)
            )
        
        logger.error(f"Bin velocity calculation failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Calculation error: {str(e)}"
        }), 500

@velocity_bp.route('/run-weekly-analysis', methods=['POST'])
def run_weekly_analysis():
    """
    Run complete weekly velocity analysis (SKUs + Bins)
    
    Expected payload:
    {
        "db_config": {...},
        "force_run": false // optional: run even if not scheduled day
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'db_config' not in data:
            return jsonify({
                "success": False,
                "message": "Database configuration required"
            }), 400
        
        # Initialize service
        service = VelocityAnalysisService(data['db_config'])
        
        if not service.connect_database():
            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500
        
        # Check if it's the scheduled day (unless forced)
        force_run = data.get('force_run', False)
        if not force_run:
            params = service.get_calculation_parameters()
            scheduled_day = int(params.get('weekly_calculation_day', 1))  # Monday by default
            current_day = datetime.now().weekday() + 1  # Monday = 1
            
            if current_day != scheduled_day:
                service.disconnect_database()
                return jsonify({
                    "success": False,
                    "message": f"Weekly analysis is scheduled for day {scheduled_day}, today is {current_day}. Use force_run=true to override."
                }), 400
        
        # Run weekly analysis
        result = service.run_weekly_analysis()
        service.disconnect_database()
        
        return jsonify({
            **result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Weekly analysis failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Weekly analysis error: {str(e)}"
        }), 500

@velocity_bp.route('/get-system-status', methods=['POST'])
def get_velocity_system_status():
    """
    Get current status of the velocity analysis system
    
    Expected payload:
    {
        "db_config": {...}
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'db_config' not in data:
            return jsonify({
                "success": False,
                "message": "Database configuration required"
            }), 400
        
        # Initialize service
        service = VelocityAnalysisService(data['db_config'])
        
        if not service.connect_database():
            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500
        
        # Get system status
        result = service.get_velocity_system_status()
        service.disconnect_database()
        
        return jsonify({
            **result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"System status check failed: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Status check error: {str(e)}"
        }), 500

@velocity_bp.route('/get-velocity-data', methods=['POST'])
def get_velocity_data():
    """
    Get velocity analysis data for display
    
    Expected payload:
    {
        "db_config": {...},
        "data_type": "sku_velocities" | "bin_velocities" | "both",
        "limit": 100, // optional
        "filters": {   // optional
            "velocity_score": [1, 2, 3],
            "bin_capacity": [1, 2, 4, 6],
            "date_range": ["2025-11-01", "2025-11-04"]
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'db_config' not in data:
            return jsonify({
                "success": False,
                "message": "Database configuration required"
            }), 400
        
        data_type = data.get('data_type', 'both')
        limit = data.get('limit', 100)
        filters = data.get('filters', {})
        
        # Initialize service
        service = VelocityAnalysisService(data['db_config'])
        
        if not service.connect_database():
            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500
        
        # Get velocity data
        result = service._get_velocity_data(data_type, limit, filters)
        service.disconnect_database()
        
        return jsonify({
            **result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get velocity data failed: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Data retrieval error: {str(e)}"
        }), 500

@velocity_bp.route('/export-velocity-data', methods=['POST'])
def export_velocity_data():
    """
    Export velocity analysis data as CSV
    
    Expected payload:
    {
        "db_config": {...},
        "data_type": "sku_velocities" | "bin_velocities",
        "format": "csv" | "json",
        "filters": {...} // optional
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'db_config' not in data:
            return jsonify({
                "success": False,
                "message": "Database configuration required"
            }), 400
        
        data_type = data.get('data_type', 'sku_velocities')
        export_format = data.get('format', 'csv')
        filters = data.get('filters', {})
        
        # Initialize service
        service = VelocityAnalysisService(data['db_config'])
        
        if not service.connect_database():
            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500
        
        # Export data
        result = service._export_velocity_data(data_type, export_format, filters)
        service.disconnect_database()
        
        if result["success"] and export_format == 'csv':
            # Return CSV file
            from flask import Response
            return Response(
                result["data"],
                mimetype="text/csv",
                headers={"Content-disposition": f"attachment; filename={data_type}_{datetime.now().strftime('%Y%m%d')}.csv"}
            )
        else:
            return jsonify({
                **result,
                "timestamp": datetime.now().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Export velocity data failed: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Export error: {str(e)}"
        }), 500

# Helper function to register the blueprint
def register_velocity_api(app):
    """Register the velocity analysis blueprint with the Flask app"""
    app.register_blueprint(velocity_bp)
    
    # Register scheduler endpoints
    scheduler_bp = create_scheduled_job_api_endpoints()
    app.register_blueprint(scheduler_bp)
    
    logger.info("Velocity analysis API endpoints registered")
    logger.info("Velocity scheduler API endpoints registered")

# Error handlers for the blueprint
@velocity_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "message": "Velocity analysis endpoint not found"
    }), 404

@velocity_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "message": "Internal server error in velocity analysis"
    }), 500