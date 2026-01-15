from flask import Flask, render_template, request, jsonify, send_file
import requests
import pandas as pd
import numpy as np
import pymysql
from datetime import datetime
import json
import os
import time
import logging
from mlxtend.frequent_patterns import apriori, association_rules
from app.shared.database.connection import DatabaseConnection
import warnings
warnings.filterwarnings('ignore')

# Store reference to original print before overriding
_original_print = print

# Safe print function that won't crash if stdout is unavailable
def safe_print(*args, **kwargs):
    """Print wrapper that handles OSError when stdout is not available"""
    try:
        _original_print(*args, **kwargs)
    except (OSError, IOError):
        pass  # Silently ignore if console is not available

# Replace built-in print with safe version
print = safe_print

# Add the parent directory to Python path for imports
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import enhanced logging system
try:
    from app.utils.mining_logger import mining_logger
    LOGGING_AVAILABLE = True
    print("[OK] Enhanced logging system loaded")
except ImportError as e:
    LOGGING_AVAILABLE = False
    print(f"[WARN] Enhanced logging system not available: {e}")
    # Fallback to basic logging
    mining_logger = None

# Import history tracking and performance monitoring
try:
    from app.services.history_service import HistoryService
    from app.utils.performance_monitor import JobPerformanceTracker
    HISTORY_TRACKING_AVAILABLE = True
    print("[OK] History tracking and performance monitoring loaded")
except ImportError as e:
    HISTORY_TRACKING_AVAILABLE = False
    print(f"[WARN] History tracking not available: {e}")
    HistoryService = None
    JobPerformanceTracker = None

# Import velocity analysis module
try:
    from app.modules.velocity_analysis.api.velocity_endpoints import register_velocity_api
    VELOCITY_ANALYSIS_AVAILABLE = True
    print("[OK] Velocity Analysis module loaded successfully")
except ImportError as e:
    VELOCITY_ANALYSIS_AVAILABLE = False
    print(f"[WARN] Velocity Analysis module not available: {e}")
except Exception as e:
    VELOCITY_ANALYSIS_AVAILABLE = False
    print(f"[WARN] Velocity Analysis module error: {e}")

# Import AI insights module
try:
    from app.modules.ai_insights.api.endpoints import register_ai_insights_routes
    AI_INSIGHTS_AVAILABLE = True
    print("[OK] AI Insights module loaded successfully")
except ImportError as e:
    AI_INSIGHTS_AVAILABLE = False
    print(f"[WARN] AI Insights module not available: {e}")
except Exception as e:
    AI_INSIGHTS_AVAILABLE = False
    print(f"[WARN] AI Insights module error: {e}")

app = Flask(__name__)

# Register velocity analysis API if available
if VELOCITY_ANALYSIS_AVAILABLE:
    register_velocity_api(app)
    print("[OK] Velocity Analysis API endpoints registered")



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('association_mining.log'),
        logging.StreamHandler()
    ]
)

# Create logger instance
logger = logging.getLogger(__name__)

# Configuration - Updated for port 8080
BASE_URL = "http://127.0.0.1:8080"
API_BASE = f"{BASE_URL}/api/v1"

# Load configuration from shared config
try:
    from app.shared.config.config import config
    
    # Global variable to store user-defined database configuration - loaded from .env
    USER_DB_CONFIG = {
        'host': config.DB_HOST,
        'port': config.DB_PORT,
        'user': config.DB_USER,
        'password': config.DB_PASSWORD,
        'database': config.DB_NAME,
        'order_table': config.ORDER_TABLE,
        'sku_master_table': config.SKU_MASTER_TABLE,
        'recommendations_table': config.RECOMMENDATIONS_TABLE
    }
    print(f"[OK] Loaded database configuration from .env file")
    print(f"   Database: {config.DB_NAME} on {config.DB_HOST}:{config.DB_PORT}")
    print(f"   Order Table: {config.ORDER_TABLE}")
    print(f"   SKU Table: {config.SKU_MASTER_TABLE}")
except Exception as e:
    print(f"[WARN] Could not load configuration from .env, using defaults: {e}")
    # Fallback to hardcoded configuration
    USER_DB_CONFIG = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'root',
        'database': 'neo',
        'order_table': 'wms_to_wcs_order_line_request_data',
        'sku_master_table': 'sku_master',
        'recommendations_table': 'sku_recommendations'
    }

# Register AI insights API if available (after USER_DB_CONFIG is defined)
if AI_INSIGHTS_AVAILABLE:
    try:
        register_ai_insights_routes(app, USER_DB_CONFIG)
        print("[OK] AI Insights API endpoints registered")
    except Exception as e:
        print(f"[WARN] Failed to register AI Insights API: {e}")

def load_config():
    """Load database configuration"""
    try:
        import sys
        sys.path.append('.')
        from app.shared.config.config import config
        return config
    except Exception as e:
        print(f"Could not load configuration: {e}")
        return None

def test_server_connection():
    """Test if the server is running"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except Exception as e:
        return False, str(e)

def save_rules_to_database(user_config, rules_df, sku_name_to_id):
    """Save association rules to database using production-ready upsert/decay logic.

    Args:
        user_config: Database configuration
        rules_df: DataFrame with columns sku1 (name), sku2 (name), association_composite_score
        sku_name_to_id: Dictionary mapping SKU_NAME to SKU_ID
    """
    logger = logging.getLogger(__name__)
    try:
        logger.info(
            f"Saving {len(rules_df)} recommendations to table: {user_config['recommendations_table']} "
            f"using DatabaseConnection.save_recommendations"
        )

        # Build recommendations DataFrame compatible with DatabaseConnection.save_recommendations
        records = []
        for _, rule in rules_df.iterrows():
            parent_id = sku_name_to_id.get(rule['sku1'], rule['sku1'])  # Fallback to name if not found
            child_id = sku_name_to_id.get(rule['sku2'], rule['sku2'])   # Fallback to name if not found

            records.append({
                "main_item": parent_id,
                "recommended_item": child_id,
                "main_item_name": rule['sku1'],
                "recommended_item_name": rule['sku2'],
                "confidence_score": float(rule.get('confidence', rule.get('confidence_score', 0.0))),
                "lift_score": float(rule.get('lift', rule.get('lift_score', 0.0))),
                "support_score": float(rule.get('support', rule.get('support_score', 0.0))),
                # Use UI composite score as base; symmetric and normalized handling
                # is applied inside DatabaseConnection.save_recommendations
                "composite_score": float(rule['association_composite_score']),
                "temporal_stability": 0.5,
                "temporal_trend": 0.0,
                "temporal_composite_score": float(rule['association_composite_score']),
                "recommendation_rank": 1,
            })

        if not records:
            logger.warning("No rules to save to database")
            return False

        recommendations_df = pd.DataFrame(records)

        # Prepare custom DB configuration for DatabaseConnection
        db_config = {
            "host": user_config['host'],
            "port": user_config.get('port', 3306),
            "user": user_config['user'],
            "password": user_config['password'],
            "database": user_config['database'],
            "order_table": user_config.get('order_table'),
            "sku_master_table": user_config.get('sku_master_table'),
            "recommendations_table": user_config['recommendations_table'],
        }

        db = DatabaseConnection(custom_config=db_config)

        if not db.connect():
            logger.error("DatabaseConnection.connect() failed while saving rules from UI pipeline")
            return False

        try:
            summary = db.save_recommendations(recommendations_df)
        finally:
            db.disconnect()

        if not summary:
            logger.error("save_recommendations returned False/empty summary")
            return None

        logger.info(
            "Successfully saved recommendations using production-ready logic: "
            f"{summary.get('total_written', 0)} written, "
            f"{summary.get('new_inserts', 0)} inserts, "
            f"{summary.get('updated_existing', 0)} updates, "
            f"{summary.get('decayed_not_in_current', 0)} decayed."
        )
        return summary

    except Exception as e:
        logger.error(f"Database save error: {e}")
        return False

def generate_rules_top_skus(user_config=None, top_n=20, days_back=60, 
                           min_support=0.30, min_confidence=0.30, min_lift=1.0, 
                           max_recommendations=10, decay_rate=0.05):
    """
    Ultra-conservative: Top N SKUs only with high support threshold
    Uses user-defined database configuration
    """
    try:
        start_time = time.time()
        
        # Use user config or fall back to default
        if user_config is None:
            user_config = USER_DB_CONFIG
            
        # Connect to database using user configuration
        conn = pymysql.connect(
            host=user_config['host'],
            port=user_config.get('port', 3306),
            user=user_config['user'],
            password=user_config['password'],
            database=user_config['database'],
            charset='utf8mb4'
        )
        
        # Get top N most popular SKUs
        popularity_query = f"""
        SELECT 
            s.SKU_NAME,
            COUNT(DISTINCT o.ORDER_ID) as order_count
        FROM {user_config['order_table']} o
        JOIN {user_config['sku_master_table']} s ON o.ARTICLE_ID = s.SKU_ID
        WHERE o.INSERTED_TIMESTAMP >= DATE_SUB(CURDATE(), INTERVAL {days_back} DAY)
        AND s.SKU_NAME IS NOT NULL
        GROUP BY s.SKU_NAME
        HAVING order_count >= 10
        ORDER BY order_count DESC
        LIMIT {top_n}
        """
        
        popular_skus_df = pd.read_sql(popularity_query, conn)
        popular_sku_list = popular_skus_df['SKU_NAME'].tolist()
        
        if not popular_sku_list:
            conn.close()
            return {"error": "No popular SKUs found"}, None
        
        # Load data for these SKUs using parameterized query
        # IMPORTANT: Also fetch SKU_ID for database saving
        placeholders = ','.join(['%s'] * len(popular_sku_list))
        main_query = f"""
        SELECT 
            o.ORDER_ID,
            s.SKU_NAME,
            s.SKU_ID,
            DATEDIFF(CURDATE(), DATE(o.INSERTED_TIMESTAMP)) as days_ago
        FROM {user_config['order_table']} o
        JOIN {user_config['sku_master_table']} s ON o.ARTICLE_ID = s.SKU_ID
        WHERE o.INSERTED_TIMESTAMP >= DATE_SUB(CURDATE(), INTERVAL {days_back} DAY)
        AND s.SKU_NAME IN ({placeholders})
        """
        
        df = pd.read_sql(main_query, conn, params=popular_sku_list)
        
        # Create SKU_NAME to SKU_ID mapping for later use
        sku_name_to_id = dict(zip(df['SKU_NAME'], df['SKU_ID']))
        
        conn.close()
        
        if df.empty:
            return {"error": "No order data found"}, None
        
        # Apply time weighting with configurable decay rate
        df['weight'] = np.exp(-df['days_ago'] / (30 / decay_rate))
        
        # Create market basket (simple binary)
        basket = df.groupby(['ORDER_ID', 'SKU_NAME'])['weight'].sum().reset_index()
        basket_matrix = basket.pivot_table(
            index='ORDER_ID', 
            columns='SKU_NAME', 
            values='weight', 
            fill_value=0
        )
        basket_binary = (basket_matrix > 0).astype(int)
        
        # Mine with user-defined support threshold
        frequent_itemsets = apriori(basket_binary, min_support=min_support, use_colnames=True, max_len=2)
        
        if len(frequent_itemsets) == 0:
            # Try with lower threshold (half of user's setting)
            fallback_support = max(min_support / 2, 0.01)
            frequent_itemsets = apriori(basket_binary, min_support=fallback_support, use_colnames=True, max_len=2)
        
        if len(frequent_itemsets) > 0:
            # Generate rules with user-defined confidence
            rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
            
            # Apply lift filter
            if len(rules) > 0:
                rules = rules[rules['lift'] >= min_lift]
            
            if len(rules) > 0:
                # Create final output
                rules['sku1'] = rules['antecedents'].apply(lambda x: list(x)[0])
                rules['sku2'] = rules['consequents'].apply(lambda x: list(x)[0])
                rules['association_composite_score'] = (
                    rules['confidence'] * 0.6 + 
                    rules['lift'] / rules['lift'].max() * 0.4
                )
                
                final_rules = rules[['sku1', 'sku2', 'association_composite_score', 'confidence', 'lift', 'support']].copy()
                final_rules = final_rules.sort_values('association_composite_score', ascending=False)
                
                # Limit to max_recommendations per SKU (antecedent)
                limited_rules = []
                for sku in final_rules['sku1'].unique():
                    sku_rules = final_rules[final_rules['sku1'] == sku].head(max_recommendations)
                    limited_rules.append(sku_rules)
                
                if limited_rules:
                    final_rules = pd.concat(limited_rules, ignore_index=True)
                    final_rules = final_rules.sort_values('association_composite_score', ascending=False)
                
                # Save to database
                database_saved = False
                db_summary = None
                try:
                    db_summary = save_rules_to_database(user_config, final_rules, sku_name_to_id)
                    database_saved = bool(db_summary)
                except Exception as db_error:
                    print(f"Database save failed: {db_error}")
                
                # Save to CSV
                csv_filename = f"association_rules_ui_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                export_df = final_rules[['sku1', 'sku2', 'association_composite_score']].copy()
                export_df.to_csv(csv_filename, index=False)
                
                end_time = time.time()
                mining_duration = f"{end_time - start_time:.2f}s"
                
                stats = {
                    "total_rules": len(final_rules),
                    "top_n_skus": len(popular_sku_list),
                    "total_orders": df['ORDER_ID'].nunique(),
                    "csv_filename": csv_filename,
                    "database_saved": database_saved,
                    "mining_duration": mining_duration,
                    "score_range": {
                        "min": float(final_rules['association_composite_score'].min()),
                        "max": float(final_rules['association_composite_score'].max())
                    }
                }
                
                # Add database statistics if available
                if db_summary:
                    stats["database_stats"] = {
                        "total_generated": db_summary.get('total_generated', len(final_rules)),
                        "valid_after_filtering": db_summary.get('valid_after_filtering', 0),
                        "total_written": db_summary.get('total_written', 0),
                        "new_inserts": db_summary.get('new_inserts', 0),
                        "updated_existing": db_summary.get('updated_existing', 0),
                        "output_table": db_summary.get('target_table', user_config.get('recommendations_table', 'unknown'))
                    }
                
                return stats, final_rules.to_dict('records')
        
        return {"error": "No association rules could be generated"}, None
        
    except Exception as e:
        return {"error": str(e)}, None

def direct_mining(user_config=None, days_back=30):
    """Direct mining without API - updated to use user configuration"""
    return generate_rules_top_skus(user_config, top_n=20, days_back=days_back)

@app.route('/')
def index():
    """Main navigation dashboard"""
    print("[ROUTE LOG] Main navigation dashboard route called")
    logger.info("Main navigation dashboard route accessed")
    return render_template('navigation_dashboard.html')

@app.route('/association-mining')
def association_mining():
    """SKU Association Mining page"""
    print("[ROUTE LOG] Association mining route called")
    logger.info("Association mining page accessed")
    return render_template('association_mining.html')

@app.route('/velocity-analysis')
def velocity_analysis():
    """Bin Velocity Analysis page - Enhanced Version"""
    print("[ROUTE LOG] Velocity analysis route called")
    logger.info("Velocity analysis page accessed")
    
    try:
        # Log velocity analysis page access (if logging available)
        if LOGGING_AVAILABLE and mining_logger:
            mining_logger.log_operation(
                operation="velocity_analysis_page_access",
                details={"page": "velocity_analysis_enhanced", "status": "success"},
                user_id="system"
            )
        
        print("[OK] [VELOCITY LOG] Rendering enhanced velocity analysis template")
        logger.info("Rendering enhanced velocity analysis template")
        
        # Render the enhanced velocity analysis template
        return render_template('velocity_analysis_enhanced.html')
        
    except Exception as e:
        print(f"[ERROR] [VELOCITY LOG] Error loading velocity analysis: {e}")
        logger.error(f"Error loading velocity analysis: {e}")
        
        # Log the error (if logging available)
        if LOGGING_AVAILABLE and mining_logger:
            mining_logger.log_operation(
                operation="velocity_analysis_page_error",
                details={"page": "velocity_analysis_enhanced", "status": "error", "error": str(e)},
                user_id="system"
            )
        
        return render_template('error.html', 
                             error_message=f"Could not load velocity analysis: {str(e)}")

@app.route('/ai-insights')
def ai_insights_dashboard():
    """AI Insights Dashboard page"""
    print("[ROUTE LOG] AI Insights dashboard route called")
    logger.info("AI Insights dashboard page accessed")
    
    try:
        # Log AI insights page access (if logging available)
        if LOGGING_AVAILABLE and mining_logger:
            mining_logger.log_operation(
                operation="ai_insights_page_access",
                details={"page": "ai_insights_dashboard", "status": "success"},
                user_id="system"
            )
        
        print("[OK] [AI INSIGHTS LOG] Rendering AI insights dashboard template")
        logger.info("Rendering AI insights dashboard template")
        
        # Check if AI insights module is available
        if AI_INSIGHTS_AVAILABLE:
            print("[OK] [AI INSIGHTS LOG] AI Insights module is available")
        else:
            print("[WARN] [AI INSIGHTS LOG] AI Insights module is not available")
        
        # Render the AI insights dashboard template
        return render_template('ai_insights_dashboard.html')
        
    except Exception as e:
        print(f"[ERROR] [AI INSIGHTS LOG] Error loading AI insights dashboard: {e}")
        logger.error(f"Error loading AI insights dashboard: {e}")
        
        # Log the error (if logging available)
        if LOGGING_AVAILABLE and mining_logger:
            mining_logger.log_operation(
                operation="ai_insights_page_error",
                details={"page": "ai_insights_dashboard", "status": "error", "error": str(e)},
                user_id="system"
            )
        
        return render_template('error.html', 
                             error_message=f"Could not load AI insights dashboard: {str(e)}")

@app.route('/velocity-analysis-legacy')
def velocity_analysis_legacy():
    """Bin Velocity Analysis page - Legacy Version"""
    print("[ROUTE LOG] Legacy velocity analysis route called")
    logger.info("Legacy velocity analysis page accessed")
    
    # Import velocity analysis UI if available
    velocity_content = ""
    if VELOCITY_ANALYSIS_AVAILABLE:
        try:
            from app.modules.velocity_analysis.ui.velocity_ui import get_velocity_analysis_section
            velocity_content = get_velocity_analysis_section()
            print(f"[OK] [VELOCITY LOG] Velocity HTML loaded: {len(velocity_content)} characters")
            logger.info(f"Velocity HTML content loaded successfully: {len(velocity_content)} characters")
        except ImportError as e:
            print(f"[ERROR] [VELOCITY LOG] Failed to import velocity UI: {e}")
            logger.error(f"Failed to import velocity UI: {e}")
            velocity_content = ""
        except Exception as e:
            print(f"[ERROR] [VELOCITY LOG] Error loading velocity UI: {e}")
            logger.error(f"Error loading velocity UI: {e}")
            velocity_content = ""
    else:
        print("[ERROR] [VELOCITY LOG] Velocity Analysis not available")
        logger.warning("Velocity Analysis module not available")
    
    print(f"[VELOCITY LOG] Rendering legacy velocity analysis template with content length: {len(velocity_content)}")
    return render_template('velocity_analysis.html', velocity_analysis_content=velocity_content)

@app.route('/legacy-dashboard')
def legacy_dashboard():
    """Legacy combined dashboard - kept for compatibility"""
    # Import velocity analysis UI if available
    velocity_html = ""
    if VELOCITY_ANALYSIS_AVAILABLE:
        try:
            from app.modules.velocity_analysis.ui.velocity_ui import get_velocity_analysis_section
            velocity_html = get_velocity_analysis_section()
            print(f"[OK] Velocity HTML loaded: {len(velocity_html)} characters")
        except ImportError as e:
            print(f"[ERROR] Failed to import velocity UI: {e}")
            velocity_html = ""
        except Exception as e:
            print(f"[ERROR] Error loading velocity UI: {e}")
            velocity_html = ""
    else:
        print("[ERROR] Velocity Analysis not available")
    
    print(f"[VELOCITY LOG] Rendering template with velocity_html length: {len(velocity_html)}")
    return render_template('complete_dashboard_enhanced.html', velocity_analysis_section=velocity_html)

@app.route('/db-config')
def db_config_page():
    """Database configuration page"""
    return render_template('test_db_config.html')

@app.route('/api/db-config', methods=['GET'])
def get_db_config():
    """Get current database configuration"""
    return jsonify({
        "success": True,
        "config": USER_DB_CONFIG
    })

@app.route('/api/algorithm-params', methods=['GET'])
def get_algorithm_params():
    """Get current algorithm parameters from configuration"""
    try:
        from app.shared.config.config import config
        
        algorithm_params = {
            "min_support": float(config.MIN_SUPPORT),
            "min_confidence": float(config.MIN_CONFIDENCE),
            "min_lift": float(config.MIN_LIFT),
            "max_recommendations": int(config.MAX_RECOMMENDATIONS),
            "decay_rate": float(config.DECAY_RATE)
        }
        
        return jsonify({
            "success": True,
            "params": algorithm_params
        })
    except Exception as e:
        # Fallback to defaults if config loading fails
        return jsonify({
            "success": True,
            "params": {
                "min_support": 0.30,
                "min_confidence": 0.30,
                "min_lift": 1.0,
                "max_recommendations": 10,
                "decay_rate": 0.05
            }
        })

@app.route('/api/db-config', methods=['GET', 'POST'])
def handle_db_config():
    """Handle database configuration - GET to retrieve, POST to update"""
    logger = logging.getLogger(__name__)
    
    if request.method == 'GET':
        return jsonify({
            "success": True,
            "config": USER_DB_CONFIG
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Handle both 'rules_table' and 'recommendations_table' for backward compatibility
            recommendations_table = data.get('recommendations_table') or data.get('rules_table', 'sku_recommendations')
            
            # Update global configuration
            USER_DB_CONFIG.update({
                'host': data.get('host', 'localhost'),
                'port': int(data.get('port', 3306)),
                'user': data.get('user', 'root'),
                'password': data.get('password', ''),
                'database': data.get('database', 'neo'),
                'order_table': data.get('order_table', 'wms_to_wcs_order_line_request_data'),
                'sku_master_table': data.get('sku_master_table', 'sku_master'),
                'recommendations_table': recommendations_table
            })
            
            logger.info(f"Database configuration updated - recommendations table: {USER_DB_CONFIG['recommendations_table']}")
            
            return jsonify({
                "success": True,
                "message": "Database configuration updated successfully",
                "config": USER_DB_CONFIG
            })
        except Exception as e:
            logger.error(f"Database configuration update failed: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            })

@app.route('/api/test-db-connection', methods=['POST'])
def test_db_connection():
    """Test database connection with user-provided configuration"""
    logger = logging.getLogger(__name__)
    
    try:
        # Safely get JSON data with fallback
        try:
            data = request.get_json(silent=True) or {}
        except Exception as json_error:
            logger.warning(f"JSON parsing error: {json_error}, using default config")
            data = {}
        
        # Use USER_DB_CONFIG as base, update with any provided data
        config_to_use = USER_DB_CONFIG.copy()
        config_to_use.update(data)
        
        logger.info(f"Testing database connection with config: {config_to_use['host']}:{config_to_use['port']}/{config_to_use['database']}")
        
        # Test database connection
        conn = pymysql.connect(
            host=config_to_use['host'],
            port=int(config_to_use['port']),
            user=config_to_use['user'],
            password=config_to_use['password'],
            database=config_to_use['database'],
            connect_timeout=5,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        
        # Test if tables exist - use CURRENT USER CONFIGURATION
        tables_status = {}
        test_tables = {
            'order': config_to_use.get('order_table', 'wms_to_wcs_order_line_request_data'),
            'sku_master': config_to_use.get('sku_master_table', 'sku_master'), 
            'rules': config_to_use.get('rules_table', 'sku_recommendations'),
            'history': config_to_use.get('history_table', 'mining_history'),
            'stats': config_to_use.get('stats_table', 'mining_statistics')
        }
        
        logger.info(f"Testing tables: {list(test_tables.keys())}")
        
        for table_key, table_name in test_tables.items():
            if table_name:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name} LIMIT 1")
                    count = cursor.fetchone()[0]
                    tables_status[table_key] = {"exists": True, "count": count}
                    logger.info(f"Table {table_name}: {count} records")
                except pymysql.MySQLError as e:
                    tables_status[table_key] = {"exists": False, "count": 0}
                    logger.warning(f"Table {table_name} does not exist: {e}")
            else:
                tables_status[table_key] = {"exists": False, "count": 0}
        
        cursor.close()
        conn.close()
        
        # Log successful connection
        if mining_logger:
            mining_logger.log_database_connection(config_to_use, success=True)
        
        return jsonify({
            "success": True,
            "message": "Database connection successful",
            "mysql_version": version[0] if version else "Unknown",
            "tables": tables_status
        })
        
    except pymysql.MySQLError as e:
        # Log failed connection
        if mining_logger:
            mining_logger.log_database_connection(config_to_use, success=False, error=str(e))
        
        return jsonify({
            "success": False,
            "error": f"Database connection failed: {str(e)}"
        })
    except Exception as e:
        # Log general error
        if mining_logger:
            mining_logger.log_database_connection(config_to_use, success=False, error=str(e))
        
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/save-db-config', methods=['POST'])
def save_db_config():
    """Save user-provided database configuration"""
    logger = logging.getLogger(__name__)
    
    try:
        # Get configuration from request
        data = request.get_json(silent=True) or {}
        
        # Validate required fields
        required_fields = ['host', 'user', 'database']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                })
        
        # Update global USER_DB_CONFIG
        global USER_DB_CONFIG
        old_config = USER_DB_CONFIG.copy()  # Save old config for logging
        
        USER_DB_CONFIG.update({
            'host': data.get('host'),
            'port': int(data.get('port', 3306)),
            'user': data.get('user'),
            'password': data.get('password', ''),
            'database': data.get('database')
        })
        
        # Log configuration change
        if mining_logger:
            # Remove passwords from logged configs for security
            safe_old_config = {k: v for k, v in old_config.items() if k != 'password'}
            safe_new_config = {k: v for k, v in USER_DB_CONFIG.items() if k != 'password'}
            mining_logger.log_config_change("database", safe_old_config, safe_new_config)
        
        logger.info(f"Updated database configuration: {USER_DB_CONFIG['host']}:{USER_DB_CONFIG['port']}/{USER_DB_CONFIG['database']}")
        
        # Test the new configuration immediately
        try:
            conn = pymysql.connect(
                host=USER_DB_CONFIG['host'],
                port=USER_DB_CONFIG['port'],
                user=USER_DB_CONFIG['user'],
                password=USER_DB_CONFIG['password'],
                database=USER_DB_CONFIG['database'],
                connect_timeout=5,
                charset='utf8mb4'
            )
            conn.close()
            
            # Log successful save and test
            if mining_logger:
                mining_logger.log_operation("Save Database Config", {
                    "type": "config_save",
                    "status": "success",
                    "tested": True,
                    "config": safe_new_config
                })
            
            return jsonify({
                "success": True,
                "message": "Database configuration saved and tested successfully",
                "config": {
                    "host": USER_DB_CONFIG['host'],
                    "port": USER_DB_CONFIG['port'],
                    "user": USER_DB_CONFIG['user'],
                    "database": USER_DB_CONFIG['database']
                }
            })
            
        except pymysql.MySQLError as test_error:
            # Configuration saved but connection failed
            if mining_logger:
                mining_logger.log_operation("Save Database Config", {
                    "type": "config_save",
                    "status": "partial_success",
                    "tested": False,
                    "error": str(test_error),
                    "config": safe_new_config
                })
            
            return jsonify({
                "success": True,
                "message": f"Configuration saved but connection test failed: {str(test_error)}",
                "config": {
                    "host": USER_DB_CONFIG['host'],
                    "port": USER_DB_CONFIG['port'],
                    "user": USER_DB_CONFIG['user'],
                    "database": USER_DB_CONFIG['database']
                }
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to save configuration: {str(e)}"
        })

@app.route('/api/test-connection')
def test_connection():
    """Test server and database connection using UI configuration"""
    # Test server connection
    server_ok, server_data = test_server_connection()
    
    # Test database connection using USER_DB_CONFIG
    db_ok = False
    db_error = None
    try:
        conn = pymysql.connect(
            host=USER_DB_CONFIG['host'],
            port=USER_DB_CONFIG['port'],
            user=USER_DB_CONFIG['user'],
            password=USER_DB_CONFIG['password'],
            database=USER_DB_CONFIG['database'],
            charset='utf8mb4'
        )
        conn.close()
        db_ok = True
    except Exception as e:
        db_error = str(e)
    
    return jsonify({
        "success": True,
        "server": {"connected": server_ok, "data": server_data},
        "database": {"connected": db_ok, "error": db_error}
    })

@app.route('/api/mine-direct', methods=['POST'])
def mine_direct():
    """Direct mining endpoint using user-defined database configuration"""
    data = request.get_json()
    days_back = data.get('days_back', 60)
    top_skus = data.get('top_skus', 20)
    
    # Extract algorithm parameters
    algorithm_params = {
        'min_support': data.get('min_support', 0.30),
        'min_confidence': data.get('min_confidence', 0.30),
        'min_lift': data.get('min_lift', 1.0),
        'max_recommendations': data.get('max_recommendations', 10),
        'decay_rate': data.get('decay_rate', 0.05)
    }
    
    # Generate unique job ID
    job_id = f"direct_mining_{int(time.time())}"
    user_ip = request.remote_addr
    
    # Variables for database logging
    log_db = None
    log_id = None
    start_time_dt = datetime.now()
    
    # Initialize history tracking and performance monitoring
    history_service = None
    performance_tracker = None
    
    if HISTORY_TRACKING_AVAILABLE:
        try:
            history_service = HistoryService(USER_DB_CONFIG)
            history_service.create_history_tables()  # Ensure tables exist
            
            # Start job tracking
            history_service.start_job(
                job_id=job_id,
                job_name=f"Direct Mining - Top {top_skus} SKUs",
                mining_method="direct",
                parameters={
                    "days_back": days_back,
                    "top_skus": top_skus,
                    "algorithm_params": algorithm_params
                },
                user_ip=user_ip
            )
            
            # Start performance tracking
            performance_tracker = JobPerformanceTracker(job_id)
            performance_tracker.start()
            
        except Exception as e:
            print(f"History tracking initialization failed: {e}")
    
    # Create database log entry for mining_job_logs table
    try:
        import pymysql
        import json
        from app.shared.config.config import Config
        
        config = Config()
        log_db = pymysql.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            port=config.DB_PORT
        )
        log_cursor = log_db.cursor()
        
        execution_params = {
            'days_back': days_back,
            'top_skus': top_skus,
            'min_support': algorithm_params.get('min_support'),
            'min_confidence': algorithm_params.get('min_confidence'),
            'min_lift': algorithm_params.get('min_lift'),
            'max_recommendations': algorithm_params.get('max_recommendations'),
            'decay_rate': algorithm_params.get('decay_rate'),
            'output_table': USER_DB_CONFIG.get('recommendations_table', 'sku_recommendations')
        }
        
        log_cursor.execute(
            """
            INSERT INTO mining_job_logs
            (schedule_id, job_name, execution_parameters, started_at, execution_status)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (0, f"UI Direct Mining - {job_id}", json.dumps(execution_params), start_time_dt, 'running')
        )
        log_id = log_cursor.lastrowid
        log_db.commit()
        print(f"Created mining job log {log_id} for UI direct mining")
    except Exception as log_error:
        print(f"Failed to create job log: {log_error}")
        if log_db:
            try:
                log_db.close()
            except:
                pass
        log_db = None
        log_id = None
    
    try:
        processing_start_time = time.time()
        
        # Log to mining_job_logs table
        log_id = None
        try:
            import pymysql
            import json
            from app.shared.config.config import Config
            
            config_obj = Config()
            log_conn = pymysql.connect(
                host=config_obj.DB_HOST,
                user=config_obj.DB_USER,
                password=config_obj.DB_PASSWORD,
                database=config_obj.DB_NAME,
                port=config_obj.DB_PORT
            )
            log_cursor = log_conn.cursor()
            
            execution_params = {
                'min_support': algorithm_params.get('min_support'),
                'min_confidence': algorithm_params.get('min_confidence'),
                'min_lift': algorithm_params.get('min_lift'),
                'max_recommendations': algorithm_params.get('max_recommendations'),
                'decay_rate': algorithm_params.get('decay_rate'),
                'days_back': days_back,
                'top_skus': top_skus,
                'output_table': USER_DB_CONFIG.get('recommendations_table', 'sku_recommendations')
            }
            
            log_cursor.execute(
                """
                INSERT INTO mining_job_logs
                (schedule_id, job_name, execution_parameters, started_at)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    0,  # 0 means API-based
                    f"API Direct - {job_id}",
                    json.dumps(execution_params),
                    datetime.now()
                )
            )
            log_id = log_cursor.lastrowid
            log_conn.commit()
            log_conn.close()
        except Exception as log_error:
            logger.warning(f"Failed to create job log: {log_error}")
        
        # Log mining operation start
        if mining_logger:
            mining_logger.log_mining_operation(
                mining_type="direct",
                parameters={
                    "job_id": job_id,
                    "days_back": days_back,
                    "top_skus": top_skus,
                    "algorithm_params": algorithm_params
                }
            )
        
        # Use user-defined database configuration with algorithm parameters
        stats, rules = generate_rules_top_skus(
            USER_DB_CONFIG, 
            top_n=top_skus, 
            days_back=days_back,
            **algorithm_params
        )
        
        if 'error' in stats:
            # Update database log with failure
            if log_id and log_db:
                try:
                    end_time = datetime.now()
                    execution_time = int((end_time - start_time_dt).total_seconds())
                    log_cursor = log_db.cursor()
                    log_cursor.execute("""
                        UPDATE mining_job_logs
                        SET completed_at=%s, execution_status='failed',
                            execution_time_seconds=%s
                        WHERE id=%s
                    """, (end_time, execution_time, log_id))
                    log_db.commit()
                    log_cursor.close()
                    log_db.close()
                except Exception as log_err:
                    print(f"Error updating job log: {log_err}")
            
            # Log mining failure
            if mining_logger:
                mining_logger.log_mining_operation(
                    mining_type="direct",
                    parameters={
                        "job_id": job_id,
                        "days_back": days_back,
                        "top_skus": top_skus,
                        "algorithm_params": algorithm_params
                    },
                    success=False,
                    error=stats['error']
                )
            
            # Finish job tracking with failure
            if history_service:
                history_service.finish_job(job_id, status='failed', error_message=stats['error'])
            
            return jsonify({"success": False, "error": stats['error']})
        
        # Record processing metrics
        if performance_tracker:
            performance_tracker.record_processing_metrics(processing_start_time)
            
            # Convert rules to DataFrame for analysis
            if rules:
                rules_df = pd.DataFrame(rules)
                performance_tracker.record_mining_results(rules_df)
        
        # Get final performance metrics
        performance_metrics = {}
        if performance_tracker:
            performance_metrics = performance_tracker.finish()
            
        # Log performance metrics to history
        if history_service and performance_metrics:
            history_service.log_performance_metrics(job_id, performance_metrics)
        
        # Update database log with success
        if log_id and log_db:
            try:
                end_time = datetime.now()
                execution_time = int((end_time - start_time_dt).total_seconds())
                db_stats = stats.get('database_stats', {})
                log_cursor = log_db.cursor()
                log_cursor.execute("""
                    UPDATE mining_job_logs
                    SET completed_at=%s, execution_status='success',
                        rules_generated=%s, records_processed=%s,
                        execution_time_seconds=%s
                    WHERE id=%s
                """, (end_time, db_stats.get('total_written', 0), 
                      stats.get('total_orders', 0), execution_time, log_id))
                log_db.commit()
                log_cursor.close()
                log_db.close()
            except Exception as log_err:
                print(f"Error updating job log: {log_err}")
        
        # Finish job tracking with success
        if history_service:
            history_service.finish_job(job_id, status='completed', results_count=len(rules))
        
        # Log successful mining
        if mining_logger:
            mining_logger.log_mining_operation(
                mining_type="direct",
                parameters={
                    "job_id": job_id,
                    "days_back": days_back,
                    "top_skus": top_skus,
                    "algorithm_params": algorithm_params
                },
                results={
                    "rules_count": len(rules),
                    "stats": stats,
                    "performance_metrics": performance_metrics
                },
                success=True
            )
        
        return jsonify({
            "success": True,
            "job_id": job_id,
            "stats": stats,
            "rules": rules[:100],  # Limit to first 100 rules for display
            "algorithm_params": algorithm_params,  # Include params in response for reference
            "performance_metrics": performance_metrics if performance_metrics else None
        })
    
    except Exception as e:
        # Update database log with exception
        if log_id and log_db:
            try:
                end_time = datetime.now()
                execution_time = int((end_time - start_time_dt).total_seconds())
                log_cursor = log_db.cursor()
                log_cursor.execute("""
                    UPDATE mining_job_logs
                    SET completed_at=%s, execution_status='failed',
                        execution_time_seconds=%s
                    WHERE id=%s
                """, (end_time, execution_time, log_id))
                log_db.commit()
                log_cursor.close()
                log_db.close()
            except Exception as log_err:
                print(f"Error updating job log: {log_err}")
        
        # Finish job tracking with error
        if history_service:
            history_service.finish_job(job_id, status='failed', error_message=str(e))
        
        # Log mining exception
        if mining_logger:
            mining_logger.log_mining_operation(
                mining_type="direct",
                parameters={
                    "job_id": job_id,
                    "days_back": days_back,
                    "top_skus": top_skus,
                    "algorithm_params": algorithm_params
                },
                success=False,
                error=str(e)
            )
        return jsonify({"success": False, "error": str(e), "job_id": job_id})

# Global variable to track API mining status
api_mining_status = {
    "status": "idle",
    "task_id": None,
    "progress": 0,
    "message": "",
    "start_time": None
}

@app.route('/api/mine-api', methods=['POST'])
def mine_api():
    """Enhanced API-based mining using UnifiedMiningService for consistency"""
    global api_mining_status
    
    data = request.get_json()
    
    # Extract parameters
    days_back = data.get('days_back', 60)
    top_skus = data.get('top_skus', 200)
    enhanced = data.get('enhanced', False)
    time_method = data.get('time_method', 'exponential_decay')
    
    # Extract algorithm parameters
    algorithm_params = {
        'min_support': data.get('min_support', 0.01),
        'min_confidence': data.get('min_confidence', 0.30),
        'min_lift': data.get('min_lift', 1.0),
        'max_recommendations': data.get('max_recommendations', 10),
        'decay_rate': data.get('decay_rate', 0.05),
        'max_items': top_skus
    }
    
    # Enhanced decay rates based on time method
    if enhanced:
        decay_mapping = {
            'linear': 0.03,
            'exponential_decay': 0.05,
            'logarithmic': 0.08
        }
        algorithm_params['decay_rate'] = decay_mapping.get(time_method, 0.05)
    
    # Get database configuration
    config_to_use = USER_DB_CONFIG.copy()
    if data.get('custom_db_config'):
        config_to_use.update(data['custom_db_config'])
    
    # Generate unique job ID
    job_id = f"api_mining_{int(time.time())}"
    user_ip = request.remote_addr
    
    # Database logging variables
    log_db = None
    log_id = None
    start_time_dt = datetime.now()
    
    # Initialize history tracking
    history_service = None
    performance_tracker = None
    
    if HISTORY_TRACKING_AVAILABLE:
        try:
            history_service = HistoryService(config_to_use)
            history_service.create_history_tables()
            
            history_service.start_job(
                job_id=job_id,
                job_name=f"API Mining - Enhanced: {enhanced}, Method: {time_method}",
                mining_method="api",
                parameters={
                    "days_back": days_back,
                    "enhanced": enhanced,
                    "time_method": time_method,
                    "algorithm_params": algorithm_params
                },
                user_ip=user_ip
            )
            
            performance_tracker = JobPerformanceTracker(job_id)
            performance_tracker.start()
            
        except Exception as e:
            print(f"History tracking initialization failed: {e}")
    
    # Create database log entry
    try:
        from app.shared.config.config import Config
        
        config = Config()
        log_db = pymysql.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        log_cursor = log_db.cursor()
        
        execution_params = {
            'days_back': days_back,
            'enhanced': enhanced,
            'time_method': time_method,
            **algorithm_params,
            'output_table': config_to_use.get('recommendations_table', 'sku_recommendations')
        }
        
        log_cursor.execute("""
            INSERT INTO mining_job_logs 
            (schedule_id, job_name, started_at, execution_status, execution_parameters)
            VALUES (%s, %s, %s, %s, %s)
        """, (0, f"UI API Mining - {job_id}", start_time_dt, 'running', json.dumps(execution_params)))
        log_db.commit()
        log_id = log_cursor.lastrowid
        log_cursor.close()
    except Exception as log_err:
        print(f"Error creating job log: {log_err}")
    
    try:
        processing_start_time = time.time()
        
        # Initialize progress tracking
        api_mining_status = {
            "status": "starting",
            "task_id": job_id,
            "progress": 0,
            "message": "Initializing unified mining service...",
            "start_time": time.time()
        }
        
        # Update progress
        api_mining_status.update({
            "status": "running",
            "progress": 10,
            "message": "Starting mining with CleanAssociationMiningService..."
        })
        
        # USE UNIFIED MINING SERVICE
        from app.modules.association_mining.services.unified_mining_service import UnifiedMiningService
        
        mining_params = {
            **algorithm_params,
            'days_back': days_back,
            'output_table': config_to_use.get('recommendations_table', 'sku_recommendations'),
            'use_enhanced_mining': enhanced,
            'time_weighting_method': time_method
        }
        
        logger.info(f"🚀 Starting UnifiedMiningService for job {job_id}")
        mining_service = UnifiedMiningService(config_to_use, mining_params)
        result = mining_service.run_mining(task_id=job_id)
        
        processing_time = time.time() - processing_start_time
        
        # Update progress: Completed
        api_mining_status.update({
            "progress": 100,
            "message": "Mining completed!"
        })
        
        # Extract results from unified service
        stats = result.get('stats', {})
        rules = result.get('recommendations', [])
        rules_generated = result.get('rules_generated', 0)
        records_processed = result.get('records_processed', 0)
        
        # Check if mining failed
        if not result.get('success', False) or 'error' in result:
            error_msg = result.get('error', stats.get('error', 'Unknown error'))
            
            # Update database log with failure
            if log_id and log_db:
                try:
                    end_time = datetime.now()
                    execution_time = int((end_time - start_time_dt).total_seconds())
                    log_cursor = log_db.cursor()
                    log_cursor.execute("""
                        UPDATE mining_job_logs
                        SET completed_at=%s, execution_status='failed',
                            execution_time_seconds=%s
                        WHERE id=%s
                    """, (end_time, execution_time, log_id))
                    log_db.commit()
                    log_cursor.close()
                    log_db.close()
                except Exception as log_err:
                    print(f"Error updating job log: {log_err}")
            
            api_mining_status.update({
                "status": "failed",
                "message": f"Mining failed: {error_msg}"
            })
            
            # Finish job tracking with failure
            if history_service:
                history_service.finish_job(job_id, status='failed', error_message=error_msg)
            
            # Log mining failure
            if mining_logger:
                mining_logger.log_mining_operation(
                    mining_type="api_unified",
                    parameters={
                        "job_id": job_id,
                        "days_back": days_back,
                        "top_skus": top_skus,
                        "enhanced": enhanced,
                        "time_method": time_method,
                        "algorithm_params": algorithm_params
                    },
                    success=False,
                    error=error_msg
                )
            
            return jsonify({"success": False, "error": error_msg, "job_id": job_id})
        
        # Record processing metrics
        if performance_tracker:
            performance_tracker.record_processing_metrics(processing_start_time)
            
            # Convert rules to DataFrame for analysis
            if rules:
                rules_df = pd.DataFrame(rules)
                performance_tracker.record_mining_results(rules_df)
        
        # Update database log with success
        if log_id and log_db:
            try:
                end_time = datetime.now()
                execution_time = int((end_time - start_time_dt).total_seconds())
                log_cursor = log_db.cursor()
                log_cursor.execute("""
                    UPDATE mining_job_logs
                    SET completed_at=%s, execution_status='success',
                        rules_generated=%s, records_processed=%s,
                        execution_time_seconds=%s
                    WHERE id=%s
                """, (end_time, rules_generated, records_processed, execution_time, log_id))
                log_db.commit()
                log_cursor.close()
                log_db.close()
            except Exception as log_err:
                print(f"Error updating job log: {log_err}")
        
        # Get final performance metrics
        performance_metrics = {}
        if performance_tracker:
            performance_metrics = performance_tracker.finish()
            
        # Log performance metrics to history
        if history_service and performance_metrics:
            history_service.log_performance_metrics(job_id, performance_metrics)
        
        # Update progress: Completed
        api_mining_status.update({
            "status": "completed",
            "progress": 100,
            "message": f"Mining completed! Found {len(rules)} association rules."
        })
        
        # Finish job tracking with success
        if history_service:
            history_service.finish_job(job_id, status='completed', results_count=len(rules))
        
        # Log successful mining
        if mining_logger:
            mining_logger.log_mining_operation(
                mining_type="api_unified",
                parameters={
                    "job_id": job_id,
                    "days_back": days_back,
                    "top_skus": top_skus,
                    "enhanced": enhanced,
                    "time_method": time_method,
                    "algorithm_params": algorithm_params
                },
                results={
                    "rules_count": len(rules),
                    "rules_generated": rules_generated,
                    "records_processed": records_processed,
                    "stats": stats,
                    "performance_metrics": performance_metrics
                },
                success=True
            )
        
        return jsonify({
            "success": True,
            "job_id": job_id,
            "stats": stats,
            "rules": rules[:100],  # Limit to first 100 rules for display
            "rules_generated": rules_generated,
            "records_processed": records_processed,
            "task_id": api_mining_status["task_id"],
            "algorithm_params": algorithm_params,
            "enhanced_features": {
                "temporal_weighting": enhanced,
                "time_method": time_method if enhanced else "none",
                "decay_rate": algorithm_params.get('decay_rate', 0.1)
            },
            "performance_metrics": performance_metrics if performance_metrics else None,
            "message": f"Unified mining completed successfully with {rules_generated} rules found"
        })
    
    except Exception as e:
        api_mining_status.update({
            "status": "failed",
            "message": f"Mining error: {str(e)}"
        })
        
        # Finish job tracking with error
        if history_service:
            history_service.finish_job(job_id, status='failed', error_message=str(e))
        
        # Log mining exception
        if mining_logger:
            mining_logger.log_mining_operation(
                mining_type="api_unified",
                parameters={
                    "job_id": job_id,
                    "days_back": days_back,
                    "top_skus": top_skus,
                    "enhanced": enhanced,
                    "time_method": time_method,
                    "algorithm_params": algorithm_params
                },
                success=False,
                error=str(e)
            )
        
        return jsonify({"success": False, "error": str(e), "job_id": job_id})

@app.route('/api/mining-progress')
def get_mining_progress():
    """Get current mining progress for API-based mining"""
    global api_mining_status
    
    # Return the current status of local API mining
    return jsonify({
        "status": api_mining_status.get("status", "idle"),
        "progress": api_mining_status.get("progress", 0),
        "message": api_mining_status.get("message", "No mining in progress"),
        "task_id": api_mining_status.get("task_id"),
        "start_time": api_mining_status.get("start_time"),
        "elapsed_time": time.time() - api_mining_status.get("start_time", time.time()) if api_mining_status.get("start_time") else 0
    })

@app.route('/api/mine-enhanced', methods=['POST'])
def mine_enhanced():
    """Enhanced Temporal Mining using FastAPI backend"""
    global api_mining_status
    logger = logging.getLogger(__name__)
    
    data = request.get_json()
    
    # Extract algorithm parameters
    algorithm_params = {
        'min_support': data.get('min_support', 0.30),
        'min_confidence': data.get('min_confidence', 0.30),
        'min_lift': data.get('min_lift', 1.0),
        'max_recommendations': data.get('max_recommendations', 10),
        'decay_rate': data.get('decay_rate', 0.05)
    }
    
    payload = {
        "days_back": data.get('days_back', 30),
        "use_enhanced_mining": True,  # Always use enhanced for this endpoint
        "time_weighting_method": data.get('time_weighting_method', 'exponential_decay'),
        "db_config": USER_DB_CONFIG,  # Include database configuration
        **algorithm_params  # Include algorithm parameters
    }
    
    logger.info(f"Starting enhanced mining with recommendations table: {USER_DB_CONFIG['recommendations_table']}")
    
    try:
        # Start mining request to FastAPI backend
        api_mining_status = {
            "status": "starting",
            "task_id": None,
            "progress": 0,
            "message": "Sending request to Enhanced Mining API...",
            "start_time": time.time()
        }
        
        # Call FastAPI backend directly (same as mine_api)
        response = requests.post(f"{API_BASE}/mine-rules", json=payload, timeout=10)
        
        if response.status_code == 200:
            result_data = response.json()
            task_id = result_data.get('task_id')
            
            api_mining_status.update({
                "status": "running", 
                "task_id": task_id,
                "progress": 10,
                "message": "Enhanced mining task started successfully",
            })
        else:
            api_mining_status.update({
                "status": "failed",
                "message": f"Failed to start mining: {response.text}",
                "error": f"HTTP {response.status_code}: {response.text}"
            })
        
        return jsonify({
            "success": True,
            "task_id": api_mining_status.get("task_id"),
            "message": "Enhanced mining started successfully"
        })
        
    except Exception as e:
        api_mining_status.update({
            "status": "failed",
            "message": f"Failed to start: {str(e)}",
            "error": str(e)
        })
        return jsonify({
            "success": False,
            "message": f"Failed to start enhanced mining: {str(e)}"
        }), 500

@app.route('/api/mine/fast', methods=['POST'])
def start_fast_mining():
    """Start FAST mining (top 100 SKUs, 15% support, 2-5 min completion)"""
    data = request.get_json()
    logger = logging.getLogger(__name__)
    
    payload = {
        "days_back": data.get('days_back', 30),
        "db_config": USER_DB_CONFIG
    }
    
    logger.info(f"Starting FAST mining for top 100 SKUs with 15% support")
    
    try:
        # Call FastAPI fast mining endpoint
        response = requests.post(f"{API_BASE}/mine-rules-fast", json=payload, timeout=10)
        
        if response.status_code == 200:
            result_data = response.json()
            task_id = result_data.get('task_id')
            
            return jsonify({
                "success": True,
                "task_id": task_id,
                "message": "FAST mining started - targeting top 100 SKUs (estimated 2-5 minutes)"
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Failed to start FAST mining: {response.text}"
            }), 500
        
    except Exception as e:
        logger.error(f"Error starting FAST mining: {e}")
        return jsonify({
            "success": False,
            "message": f"Failed to start FAST mining: {str(e)}"
        }), 500

@app.route('/api/mining-progress/<task_id>')
def get_task_progress(task_id):
    """Get progress for a specific task"""
    global api_mining_status
    
    if api_mining_status.get('task_id') == task_id:
        return jsonify(api_mining_status)
    else:
        return jsonify({
            "status": "not_found",
            "message": "Task not found",
            "progress": 0
        })

@app.route('/api/recommendations/<item>')
def get_recommendations(item):
    """Get recommendations for an item"""
    try:
        import urllib.parse
        encoded_item = urllib.parse.quote(item)
        response = requests.get(f"{API_BASE}/recommendations/{encoded_item}?limit=10")
        
        if response.status_code == 200:
            return jsonify({"success": True, "data": response.json()})
        else:
            return jsonify({"success": False, "error": response.text})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/export-csv', methods=['POST'])
def export_csv():
    """Export rules to CSV"""
    try:
        data = request.get_json()
        rules = data.get('rules', [])
        
        if not rules:
            return jsonify({"success": False, "error": "No rules to export"})
        
        # Create DataFrame
        df = pd.DataFrame(rules)
        
        # Select required columns
        if 'sku1' in df.columns and 'sku2' in df.columns and 'association_composite_score' in df.columns:
            export_df = df[['sku1', 'sku2', 'association_composite_score']].copy()
        else:
            return jsonify({"success": False, "error": "Invalid rule format"})
        
        # Save to CSV
        filename = f"association_rules_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        export_df.to_csv(filename, index=False)
        
        return jsonify({"success": True, "filename": filename})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/download/<filename>')
def download_file(filename):
    """Download a file"""
    try:
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route('/api/logs/<task_id>')
def get_task_logs(task_id):
    """Get real-time logs for a specific task"""
    try:
        import glob
        import os
        from datetime import datetime
        
        # Look for log files from today
        today = datetime.now().strftime('%Y%m%d')
        log_patterns = [
            f'logs/mining_detailed_{today}_*.log',
            f'logs/api_detailed_{today}_*.log'
        ]
        
        logs = []
        for pattern in log_patterns:
            for log_file in glob.glob(pattern):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        # Get recent lines that might contain our task_id
                        recent_lines = lines[-100:] if len(lines) > 100 else lines
                        for line in recent_lines:
                            if task_id in line or 'INFO' in line:
                                # Parse log line format: timestamp | level | logger | message
                                parts = line.strip().split(' | ')
                                if len(parts) >= 4:
                                    timestamp = parts[0]
                                    level = parts[1]
                                    message = ' | '.join(parts[3:])
                                    logs.append({
                                        'timestamp': timestamp,
                                        'level': level,
                                        'message': message
                                    })
                except Exception as e:
                    continue
        
        # Sort logs by timestamp and return recent ones
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        return jsonify(logs[:50])  # Return last 50 log entries
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs/live')
def get_live_logs():
    """Get comprehensive mining logs from database"""
    try:
        from datetime import datetime, timedelta
        import pymysql
        from app.shared.config.config import Config
        
        config = Config()
        connection = pymysql.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            port=config.DB_PORT,
            cursorclass=pymysql.cursors.DictCursor
        )
        
        cursor = connection.cursor()
        
        # Get logs from last 24 hours
        query = """
        SELECT 
            mjl.id,
            mjl.schedule_id,
            mjl.job_name,
            mjl.started_at,
            mjl.completed_at,
            mjl.execution_status,
            mjl.rules_generated,
            mjl.records_processed,
            mjl.execution_time_seconds,
            mjl.error_message,
            mjl.execution_parameters,
            ms.output_table,
            ms.schedule_type
        FROM mining_job_logs mjl
        LEFT JOIN mining_schedules ms ON mjl.schedule_id = ms.id
        WHERE mjl.started_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        ORDER BY mjl.started_at DESC
        LIMIT 50
        """
        
        cursor.execute(query)
        logs = cursor.fetchall()
        
        # Format logs for frontend
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                'id': log['id'],
                'timestamp': log['started_at'].strftime('%Y-%m-%d %H:%M:%S') if log['started_at'] else '',
                'operation': f"Mining: {log['job_name']}",
                'status': log['execution_status'],
                'level': 'ERROR' if log['execution_status'] == 'failed' else 'INFO',
                'details': {
                    'job_name': log['job_name'],
                    'schedule_type': log['schedule_type'] or 'API',
                    'output_table': log['output_table'] or 'N/A',
                    'rules_generated': log['rules_generated'],
                    'records_processed': log['records_processed'],
                    'execution_time': f"{log['execution_time_seconds']}s",
                    'started_at': log['started_at'].strftime('%Y-%m-%d %H:%M:%S') if log['started_at'] else '',
                    'completed_at': log['completed_at'].strftime('%Y-%m-%d %H:%M:%S') if log['completed_at'] else 'In Progress',
                    'parameters': log['execution_parameters'],
                    'error_message': log['error_message']
                },
                'message': f"{'✓' if log['execution_status'] == 'success' else '✗'} {log['job_name']}: {log['rules_generated']} rules generated from {log['records_processed']} records → {log['output_table'] or 'sku_recommendations'}"
            })
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'logs': formatted_logs
        })
    except Exception as e:
        print(f"Error fetching mining logs: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'logs': []
        })
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        return jsonify(logs[:30])  # Return last 30 log entries
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ========== SCHEDULER ROUTES ==========

@app.route('/api/scheduler-status')
def get_scheduler_status():
    """Get scheduler service status"""
    try:
        response = requests.get(f"{API_BASE}/scheduler/status")
        if response.status_code == 200:
            data = response.json()
            # Convert the boolean scheduler_running to a string status
            status = "running" if data.get("scheduler_running", False) else "stopped"
            return jsonify({
                'success': True,
                'status': status,
                'data': data
            })
        else:
            return jsonify({
                'success': False,
                'status': 'error',
                'error': f"FastAPI error: {response.status_code}"
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unknown',
            'error': str(e)
        })

@app.route('/api/start-scheduler', methods=['POST'])
def start_scheduler():
    """Start the scheduler service"""
    try:
        response = requests.post(f"{API_BASE}/scheduler/start")
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'data': response.json()
            })
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
            error_msg = error_data.get('detail', f'HTTP {response.status_code}')
            return jsonify({
                'success': False,
                'message': error_msg
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/stop-scheduler', methods=['POST'])
def stop_scheduler():
    """Stop the scheduler service"""
    try:
        response = requests.post(f"{API_BASE}/scheduler/stop")
        return jsonify({
            'success': True,
            'data': response.json()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/schedules')
def get_schedules():
    """Get all schedules"""
    try:
        response = requests.get(f"{API_BASE}/scheduler/schedules")
        if response.status_code == 200:
            schedules_data = response.json()
            return jsonify({
                'success': True,
                'schedules': schedules_data  # JavaScript expects 'schedules' key
            })
        else:
            return jsonify({
                'success': False,
                'schedules': [],
                'error': f"FastAPI error: {response.status_code}"
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'schedules': [],
            'error': str(e)
        })

@app.route('/api/create-schedule', methods=['POST'])
def create_schedule():
    """Create a new schedule"""
    try:
        schedule_data = request.json
        # Write debug info to file for inspection
        with open('debug_schedule_params.txt', 'a', encoding='utf-8') as f:
            from datetime import datetime
            f.write(f"\n=== {datetime.now()} ===\n")
            f.write(f"[DEBUG] Received schedule data from UI: {schedule_data}\n")
            
            if schedule_data:
                f.write(f"🎯 Mining parameters from UI:\n")
                f.write(f"   min_support: {schedule_data.get('min_support', 'NOT PROVIDED')}\n")
                f.write(f"   min_confidence: {schedule_data.get('min_confidence', 'NOT PROVIDED')}\n")
                f.write(f"   min_lift: {schedule_data.get('min_lift', 'NOT PROVIDED')}\n")
                f.write(f"   max_recommendations: {schedule_data.get('max_recommendations', 'NOT PROVIDED')}\n")
                f.write(f"   decay_rate: {schedule_data.get('decay_rate', 'NOT PROVIDED')}\n")
        
        print(f"[DEBUG] Received schedule data from UI: {schedule_data}")
        
        # Log specific mining parameters
        if schedule_data:
            print(f"🎯 Mining parameters from UI:")
            print(f"   min_support: {schedule_data.get('min_support', 'NOT PROVIDED')}")
            print(f"   min_confidence: {schedule_data.get('min_confidence', 'NOT PROVIDED')}")
            print(f"   min_lift: {schedule_data.get('min_lift', 'NOT PROVIDED')}")
            print(f"   max_recommendations: {schedule_data.get('max_recommendations', 'NOT PROVIDED')}")
            print(f"   decay_rate: {schedule_data.get('decay_rate', 'NOT PROVIDED')}")
        
        response = requests.post(
            f"{API_BASE}/scheduler/schedules",
            json=schedule_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"DEBUG: FastAPI response status: {response.status_code}")
        print(f"DEBUG: FastAPI response: {response.text}")
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'data': response.json()
            })
        else:
            error_detail = response.json().get('detail', 'Unknown error') if response.text else 'No response'
            print(f"DEBUG: Error detail: {error_detail}")
            return jsonify({
                'success': False,
                'error': error_detail
            })
    except Exception as e:
        print(f"DEBUG: Exception: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/toggle-schedule/<int:schedule_id>', methods=['POST'])
def toggle_schedule(schedule_id):
    """Toggle a schedule's active status"""
    try:
        response = requests.post(f"{API_BASE}/scheduler/schedules/{schedule_id}/toggle")
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'data': response.json()
            })
        else:
            return jsonify({
                'success': False,
                'error': response.json().get('detail', 'Unknown error')
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/delete-schedule/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """Delete a schedule"""
    try:
        response = requests.delete(f"{API_BASE}/scheduler/schedules/{schedule_id}")
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'data': response.json()
            })
        else:
            return jsonify({
                'success': False,
                'error': response.json().get('detail', 'Unknown error')
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/delete-all-schedules', methods=['DELETE'])
def delete_all_schedules():
    """Delete all schedules"""
    try:
        response = requests.delete(f"{API_BASE}/scheduler/schedules")
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'data': response.json()
            })
        else:
            return jsonify({
                'success': False,
                'error': response.json().get('detail', 'Unknown error')
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/clean-stuck-jobs', methods=['POST'])
def clean_stuck_jobs():
    """Clean stuck running jobs"""
    try:
        # Direct database update - mark all running jobs as failed
        db = DatabaseConnection()
        db.connect()
        
        # Get count of stuck jobs
        db.cursor.execute("SELECT COUNT(*) FROM mining_job_logs WHERE execution_status = 'running'")
        result = db.cursor.fetchone()
        stuck_count = result[0] if result else 0
        
        # Update stuck jobs to failed
        db.cursor.execute("""
            UPDATE mining_job_logs 
            SET execution_status = 'failed', 
                error_message = 'Job was stuck in running state - cleaned up',
                completed_at = NOW()
            WHERE execution_status = 'running'
        """)
        db.connection.commit()
        db.disconnect()
        
        return jsonify({
            'success': True,
            'cleaned_count': stuck_count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/run-schedule/<int:schedule_id>', methods=['POST'])
def run_schedule_now(schedule_id):
    """Manually run a schedule now"""
    try:
        response = requests.post(f"{API_BASE}/scheduler/schedules/{schedule_id}/run")
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'data': response.json()
            })
        else:
            return jsonify({
                'success': False,
                'error': response.json().get('detail', 'Unknown error')
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/schedule-logs/<int:schedule_id>')
def get_schedule_logs(schedule_id):
    """Get execution logs for a specific schedule"""
    try:
        limit = request.args.get('limit', 20)
        response = requests.get(f"{API_BASE}/scheduler/schedules/{schedule_id}/logs?limit={limit}")
        return jsonify({
            'success': True,
            'data': response.json()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/job-logs')
def get_job_logs():
    """Get all recent job execution logs"""
    try:
        limit = request.args.get('limit', 10)
        response = requests.get(f"{API_BASE}/scheduler/logs?limit={limit}")
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'logs': response.json()
            })
        else:
            return jsonify({
                'success': False,
                'logs': [],
                'error': f"FastAPI error: {response.status_code}"
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'logs': [],
            'error': str(e)
        })

# ==================== LOGGING API ENDPOINTS ====================

@app.route('/api/logs/recent')
def get_recent_logs():
    """Get recent system logs"""
    try:
        if not mining_logger:
            return jsonify({
                'success': False,
                'error': 'Logging system not available'
            })
        
        limit = int(request.args.get('limit', 100))
        operation_type = request.args.get('type', None)
        
        logs = mining_logger.get_recent_logs(limit=limit, operation_type=operation_type)
        
        return jsonify({
            'success': True,
            'logs': logs,
            'count': len(logs)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/logs/statistics')
def get_log_statistics():
    """Get logging statistics from database"""
    try:
        from datetime import datetime, timedelta
        import pymysql
        from app.shared.config.config import Config
        
        config = Config()
        connection = pymysql.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            port=config.DB_PORT,
            cursorclass=pymysql.cursors.DictCursor
        )
        
        cursor = connection.cursor()
        
        # Get statistics from last 24 hours
        cursor.execute("""
            SELECT 
                COUNT(*) as total_logs,
                SUM(CASE WHEN execution_status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN execution_status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                MAX(started_at) as last_log_time
            FROM mining_job_logs
            WHERE started_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """)
        
        stats = cursor.fetchone()
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_logs': stats['total_logs'] or 0,
                'status_distribution': {
                    'success': stats['success_count'] or 0,
                    'failed': stats['failed_count'] or 0
                },
                'last_log_time': stats['last_log_time'].isoformat() if stats['last_log_time'] else None
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/logs/by-date')
def get_logs_by_date():
    """Get logs for a specific date"""
    try:
        if not mining_logger:
            return jsonify({
                'success': False,
                'error': 'Logging system not available'
            })
        
        date_str = request.args.get('date')
        if not date_str:
            return jsonify({
                'success': False,
                'error': 'Date parameter required (YYYY-MM-DD format)'
            })
        
        logs = mining_logger.get_logs_by_date(date_str)
        
        return jsonify({
            'success': True,
            'logs': logs,
            'count': len(logs),
            'date': date_str
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/logs')
def logs_viewer():
    """Logs viewer page"""
    return render_template('logs_viewer.html')

# Fallback velocity API endpoints (if module import failed)
if not VELOCITY_ANALYSIS_AVAILABLE:
    print("🔧 Adding fallback velocity API endpoints...")
    
    @app.route('/api/velocity/test-connection', methods=['POST'])
    def fallback_velocity_test_connection():
        """Fallback velocity database connection test"""
        try:
            import pymysql
            from datetime import datetime
            
            # Use main app's database configuration
            db_config = {
                'host': USER_DB_CONFIG.get('host', 'localhost'),
                'user': USER_DB_CONFIG.get('user', 'root'),
                'password': USER_DB_CONFIG.get('password', ''),
                'database': USER_DB_CONFIG.get('database', 'neo'),
                'port': USER_DB_CONFIG.get('port', 3306)
            }
            
            # Test connection
            conn = pymysql.connect(
                host=db_config['host'],
                port=db_config['port'],
                user=db_config['user'],
                password=db_config['password'],
                database=db_config['database'],
                connect_timeout=5,
                charset='utf8mb4'
            )
            
            # Check velocity tables
            cursor = conn.cursor()
            velocity_tables = [
                'sku_master',
                'sku_velocity_history', 
                'bin_velocity_scores',
                'velocity_calculation_config',
                'velocity_calculation_jobs',
                'bin_configuration',
                'wms_to_wcs_order_line_request_data'
            ]
            
            tables_status = {}
            for table in velocity_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    tables_status[table] = True
                except:
                    tables_status[table] = False
            
            cursor.close()
            conn.close()
            
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
            
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Connection test error: {str(e)}"
            }), 500
    
    @app.route('/api/velocity/test-connection-custom', methods=['POST'])
    def fallback_velocity_test_connection_custom():
        """Fallback custom velocity database connection test"""
        try:
            import pymysql
            from datetime import datetime
            
            db_config = request.get_json()
            if not db_config:
                return jsonify({
                    "success": False,
                    "message": "Database configuration required"
                }), 400
            
            # Test connection
            conn = pymysql.connect(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 3306),
                user=db_config.get('user', 'root'),
                password=db_config.get('password', ''),
                database=db_config.get('database', 'neo'),
                connect_timeout=5,
                charset='utf8mb4'
            )
            conn.close()
            
            return jsonify({
                "success": True,
                "message": "Custom database connection successful",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Custom connection test error: {str(e)}"
            }), 500

# Historical Analysis API Endpoints
@app.route('/api/history/jobs', methods=['GET'])
def get_job_history():
    """Get job history with optional filtering"""
    if not HISTORY_TRACKING_AVAILABLE:
        return jsonify({"success": False, "error": "History tracking not available"})
    
    try:
        # Get query parameters
        limit = min(int(request.args.get('limit', 100)), 1000)  # Max 1000 records
        offset = max(int(request.args.get('offset', 0)), 0)
        status = request.args.get('status')  # completed, failed, running, cancelled
        days = int(request.args.get('days', 30)) if request.args.get('days') else None
        
        # Get database configuration (try user config first, then default)
        config_to_use = USER_DB_CONFIG.copy()
        
        history_service = HistoryService(config_to_use)
        jobs = history_service.get_job_history(limit=limit, offset=offset, status=status, days=days)
        
        return jsonify({
            "success": True,
            "jobs": jobs,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "count": len(jobs)
            },
            "filters": {
                "status": status,
                "days": days
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/history/analytics', methods=['GET'])
def get_performance_analytics():
    """Get performance analytics for specified period"""
    if not HISTORY_TRACKING_AVAILABLE:
        return jsonify({"success": False, "error": "History tracking not available"})
    
    try:
        days = min(int(request.args.get('days', 30)), 365)  # Max 1 year
        
        config_to_use = USER_DB_CONFIG.copy()
        history_service = HistoryService(config_to_use)
        analytics = history_service.get_performance_analytics(days=days)
        
        return jsonify({
            "success": True,
            "analytics": analytics
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/history/job/<job_id>', methods=['GET'])
def get_job_details(job_id):
    """Get detailed information about a specific job"""
    if not HISTORY_TRACKING_AVAILABLE:
        return jsonify({"success": False, "error": "History tracking not available"})
    
    try:
        config_to_use = USER_DB_CONFIG.copy()
        history_service = HistoryService(config_to_use)
        job_details = history_service.get_job_details(job_id)
        
        if not job_details:
            return jsonify({"success": False, "error": "Job not found"})
        
        return jsonify({
            "success": True,
            "job_details": job_details
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/history/cleanup', methods=['POST'])
def cleanup_history():
    """Cleanup old history records"""
    if not HISTORY_TRACKING_AVAILABLE:
        return jsonify({"success": False, "error": "History tracking not available"})
    
    try:
        data = request.get_json() or {}
        days = min(int(data.get('days', 90)), 365)  # Max 1 year
        
        config_to_use = USER_DB_CONFIG.copy()
        history_service = HistoryService(config_to_use)
        success = history_service.cleanup_old_records(days=days)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Successfully cleaned up records older than {days} days"
            })
        else:
            return jsonify({"success": False, "error": "Cleanup failed"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/history/status')
def get_history_status():
    """Get history tracking system status"""
    status = {
        "history_tracking_available": HISTORY_TRACKING_AVAILABLE,
        "performance_monitoring_available": HISTORY_TRACKING_AVAILABLE,
        "database_config": "configured" if USER_DB_CONFIG else "not_configured"
    }
    
    if HISTORY_TRACKING_AVAILABLE:
        try:
            config_to_use = USER_DB_CONFIG.copy()
            history_service = HistoryService(config_to_use)
            
            # Test database connection and table creation
            tables_created = history_service.create_history_tables()
            status["tables_status"] = "ready" if tables_created else "error"
            
        except Exception as e:
            status["tables_status"] = f"error: {str(e)}"
    
    return jsonify(status)

@app.route('/history')
def history_dashboard():
    """Serve the history and analytics dashboard"""
    return render_template('history_dashboard.html')

@app.route('/api/history/init', methods=['POST'])
def initialize_history_tables():
    """Initialize history tracking tables"""
    if not HISTORY_TRACKING_AVAILABLE:
        return jsonify({"success": False, "error": "History tracking not available"})
    
    try:
        data = request.get_json() or {}
        config_to_use = USER_DB_CONFIG.copy()
        
        # Allow custom database config for initialization
        if data.get('custom_db_config'):
            config_to_use.update(data['custom_db_config'])
        
        history_service = HistoryService(config_to_use)
        success = history_service.create_history_tables()
        
        if success:
            return jsonify({
                "success": True,
                "message": "History tracking tables initialized successfully"
            })
        else:
            return jsonify({"success": False, "error": "Failed to initialize tables"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ========================================
# NEO CHATBOT API ENDPOINTS
# ========================================

@app.route('/api/chatbot/chat', methods=['POST'])
def chatbot_chat():
    """Main chatbot endpoint - handles all three assistant types"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        chatbot_type = data.get('chatbot_type', 'knowledge_base')
        session_id = data.get('session_id')
        
        print(f"🤖 [CHATBOT] Received message: {message[:50]}... | Type: {chatbot_type}")
        
        # Import chatbot services
        from app.modules.neo_chatbot.services.knowledge_base_service import KnowledgeBaseService
        from app.modules.neo_chatbot.services.sql_assistant_service import SQLAssistantService
        from app.modules.neo_chatbot.services.diagnostic_service import DiagnosticService
        from app.modules.neo_chatbot.models.schemas import ChatRequest, ChatbotType
        
        # Create request object
        chat_request = ChatRequest(
            message=message,
            chatbot_type=ChatbotType(chatbot_type),
            session_id=session_id,
            conversation_history=data.get('conversation_history', [])
        )
        
        # Route to appropriate service
        if chatbot_type == 'knowledge_base':
            service = KnowledgeBaseService()
            response = service.process_query(chat_request)
        elif chatbot_type == 'sql_assistant':
            service = SQLAssistantService()
            response = service.process_query(chat_request)
        elif chatbot_type == 'diagnostic':
            service = DiagnosticService()
            response = service.process_query(chat_request)
        else:
            return jsonify({"error": f"Invalid chatbot type: {chatbot_type}"}), 400
        
        print(f"[OK] [CHATBOT] Response generated successfully")
        
        # Convert response to dict
        return jsonify({
            "response": response.response,
            "chatbot_type": response.chatbot_type.value,
            "session_id": response.session_id,
            "chat_id": response.chat_id if hasattr(response, 'chat_id') else None,  # Add chat_id
            "confidence_score": response.confidence_score,
            "source_documents": [
                {
                    "document_name": doc.document_name,
                    "content_snippet": doc.content_snippet,
                    "relevance_score": doc.relevance_score,
                    "page_number": doc.page_number,
                    "document_type": doc.document_type
                }
                for doc in (response.sources or [])
            ],
            "suggested_actions": response.suggested_actions or [],
            "sql_query": response.sql_query if hasattr(response, 'sql_query') else None
        })
        
    except Exception as e:
        print(f"[ERROR] [CHATBOT] Error: {e}")
        logger.error(f"Chatbot error: {e}", exc_info=True)
        return jsonify({
            "response": f"Sorry, I encountered an error: {str(e)}",
            "chatbot_type": chatbot_type,
            "session_id": session_id,
            "confidence_score": 0.0
        }), 500

@app.route('/api/chatbot/statistics', methods=['GET'])
def chatbot_statistics():
    """Get chatbot statistics"""
    try:
        from app.modules.neo_chatbot.services.knowledge_base_service import KnowledgeBaseService
        from app.modules.neo_chatbot.services.sql_assistant_service import SQLAssistantService
        from app.modules.neo_chatbot.services.diagnostic_service import DiagnosticService
        
        kb_service = KnowledgeBaseService()
        sql_service = SQLAssistantService()
        diag_service = DiagnosticService()
        
        return jsonify({
            "knowledge_base": kb_service.get_statistics(),
            "sql_assistant": sql_service.get_statistics(),
            "diagnostic": diag_service.get_statistics(),
            "total_sessions": 0
        })
    except Exception as e:
        logger.error(f"Error getting chatbot statistics: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chatbot/system-health', methods=['GET'])
def chatbot_system_health():
    """Get system health status"""
    try:
        from app.modules.neo_chatbot.services.diagnostic_service import DiagnosticService
        
        service = DiagnosticService()
        health = service.check_system_health()
        
        return jsonify({
            "overall_status": health.overall_status,
            "components": health.components,
            "issues": health.issues or []
        })
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chatbot/upload-document', methods=['POST'])
def chatbot_upload_document():
    """Upload a document to knowledge base"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        category = request.form.get('category', 'general')
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Save file temporarily
        from pathlib import Path
        upload_dir = Path(__file__).parent.parent / "modules" / "neo_chatbot" / "data" / "documents"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / file.filename
        file.save(str(file_path))
        
        # Ingest document
        from app.modules.neo_chatbot.services.knowledge_base_service import KnowledgeBaseService
        kb_service = KnowledgeBaseService()
        result = kb_service.ingest_document(str(file_path), category)
        
        return jsonify({
            "filename": file.filename,
            "category": category,
            "status": "success",
            "message": f"Document uploaded successfully. {result.get('chunks', 0)} chunks created."
        })
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/chatbot/feedback', methods=['POST'])
def chatbot_feedback():
    """Record user feedback on SQL query"""
    try:
        from app.modules.neo_chatbot.services.feedback_service import feedback_collector
        
        data = request.json
        
        feedback_record = feedback_collector.record_feedback(
            query=data.get('user_question', ''),
            sql_generated=data.get('sql_query', ''),
            user_question=data.get('user_question', ''),
            feedback_type=data.get('feedback_type', 'positive'),  # 'positive', 'negative', 'corrected'
            corrected_sql=data.get('corrected_sql'),
            error_message=data.get('error_message'),
            session_id=data.get('session_id'),
            tables_used=data.get('tables_used')
        )
        
        return jsonify({
            "status": "success",
            "message": "Thank you for your feedback!",
            "feedback_id": feedback_record.get('timestamp')
        })
        
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chatbot/feedback/stats', methods=['GET'])
def chatbot_feedback_stats():
    """Get feedback statistics"""
    try:
        from app.modules.neo_chatbot.services.feedback_service import feedback_collector
        
        stats = feedback_collector.get_feedback_stats()
        top_patterns = feedback_collector.get_top_positive_patterns(limit=10)
        
        return jsonify({
            "stats": stats,
            "top_patterns": top_patterns
        })
        
    except Exception as e:
        logger.error(f"Error getting feedback stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chatbot/feedback/auto-update', methods=['POST'])
def chatbot_feedback_auto_update():
    """Trigger auto-update of documentation based on feedback"""
    try:
        from app.modules.neo_chatbot.services.feedback_service import feedback_collector
        
        min_feedback = request.json.get('min_positive_feedback', 5)
        
        updated = feedback_collector.auto_update_quick_reference(min_positive_feedback=min_feedback)
        
        return jsonify({
            "status": "success" if updated else "no_updates",
            "message": "Documentation updated successfully" if updated else "No patterns meet criteria for documentation",
            "updated": updated
        })
        
    except Exception as e:
        logger.error(f"Error auto-updating documentation: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# RLHF (Reinforcement Learning from Human Feedback) Endpoints
# ============================================================================

@app.route('/api/chatbot/rlhf/feedback', methods=['POST'])
def rlhf_record_feedback():
    """Record detailed RLHF feedback with ratings and comments"""
    try:
        from app.modules.neo_chatbot.services.rlhf_service import RLHFService
        
        rlhf_service = RLHFService()
        data = request.json
        
        feedback_record = rlhf_service.record_feedback(
            chatbot_type=data.get('chatbot_type', 'sql_assistant'),
            query=data.get('query', ''),
            response=data.get('response', ''),
            feedback_type=data.get('feedback_type', 'neutral'),  # positive, negative, neutral
            rating=data.get('rating'),  # 1-5 scale
            comment=data.get('comment'),
            metadata=data.get('metadata', {})
        )
        
        return jsonify({
            "status": "success",
            "message": "Thank you for your detailed feedback!",
            "feedback_id": feedback_record.get('feedback_id'),
            "reward_score": feedback_record.get('reward_score')
        })
        
    except Exception as e:
        logger.error(f"Error recording RLHF feedback: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/chatbot/rlhf/analytics', methods=['GET'])
def rlhf_analytics():
    """Get RLHF analytics and learning metrics"""
    try:
        from app.modules.neo_chatbot.services.rlhf_service import RLHFService
        
        rlhf_service = RLHFService()
        
        chatbot_type = request.args.get('chatbot_type')  # Optional filter
        days = int(request.args.get('days', 30))
        
        analytics = rlhf_service.get_analytics(
            chatbot_type=chatbot_type,
            days=days
        )
        
        return jsonify(analytics)
        
    except Exception as e:
        logger.error(f"Error getting RLHF analytics: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/chatbot/rlhf/suggestions', methods=['POST'])
def rlhf_get_suggestions():
    """Get response improvement suggestions based on learned patterns"""
    try:
        from app.modules.neo_chatbot.services.rlhf_service import RLHFService
        
        rlhf_service = RLHFService()
        data = request.json
        
        suggestions = rlhf_service.get_response_suggestions(
            chatbot_type=data.get('chatbot_type', 'sql_assistant'),
            query=data.get('query', ''),
            current_response=data.get('response', ''),
            metadata=data.get('metadata')
        )
        
        return jsonify(suggestions)
        
    except Exception as e:
        logger.error(f"Error getting RLHF suggestions: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Generate HTML template with progress tracking
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Association Rule Mining Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        .status-connected { background-color: #28a745; }
        .status-disconnected { background-color: #dc3545; }
        .rule-card {
            border-left: 4px solid #007bff;
            margin-bottom: 10px;
        }
        .score-badge {
            font-size: 0.9em;
            padding: 4px 8px;
        }
        .progress-container {
            display: none;
            margin-top: 15px;
        }
        .progress-bar-animated {
            animation: progress-bar-stripes 1s linear infinite;
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <!-- Header -->
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary mb-4">
            <div class="container-fluid">
                <span class="navbar-brand mb-0 h1">
                    <i class="fas fa-chart-network me-2"></i>
                    Association Rule Mining Dashboard
                </span>
                <button class="btn btn-outline-light btn-sm" onclick="checkConnections()">
                    <i class="fas fa-sync-alt me-1"></i>
                    Check Status
                </button>
            </div>
        </nav>

        <!-- Status Row -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-title">
                            <i class="fas fa-server me-2"></i>
                            API Server Status
                        </h6>
                        <div id="server-status">
                            <span class="status-indicator status-disconnected"></span>
                            <span>Checking...</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-title">
                            <i class="fas fa-database me-2"></i>
                            Database Status
                        </h6>
                        <div id="database-status">
                            <span class="status-indicator status-disconnected"></span>
                            <span>Checking...</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="row">
            <!-- Mining Panel -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-pickaxe me-2"></i>Association Rule Mining</h5>
                    </div>
                    <div class="card-body">
                        <!-- Mining Method Selection -->
                        <div class="mb-3">
                            <label class="form-label">Mining Method</label>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="miningMethod" id="directMining" value="direct" checked>
                                <label class="form-check-label" for="directMining">
                                    <strong>Direct Mining</strong> <span class="badge bg-success">Recommended</span>
                                    <small class="d-block text-muted">Uses optimized algorithm for reliable results</small>
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="miningMethod" id="apiMining" value="api">
                                <label class="form-check-label" for="apiMining">
                                    <strong>API-based Mining</strong>
                                    <small class="d-block text-muted">Enhanced temporal mining with progress tracking</small>
                                </label>
                            </div>
                        </div>

                        <!-- Mining Parameters -->
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <label for="daysBack" class="form-label">Days Back</label>
                                <input type="number" class="form-control" id="daysBack" value="60" min="1" max="365">
                            </div>
                            <div class="col-md-6">
                                <label for="topSkus" class="form-label">Top SKUs</label>
                                <input type="number" class="form-control" id="topSkus" value="20" min="5" max="100">
                            </div>
                        </div>

                        <!-- API-specific options -->
                        <div id="apiOptions" style="display: none;">
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="checkbox" id="useEnhanced">
                                <label class="form-check-label" for="useEnhanced">
                                    Use Enhanced Temporal Mining
                                </label>
                            </div>
                            <div id="methodSection" style="display: none;">
                                <label for="timeMethod" class="form-label">Time Weighting Method</label>
                                <select class="form-select mb-3" id="timeMethod">
                                    <option value="exponential_decay">Exponential Decay</option>
                                    <option value="seasonal_patterns">Seasonal Patterns</option>
                                    <option value="trend_adaptive">Trend Adaptive</option>
                                    <option value="recency_frequency">Recency Frequency</option>
                                </select>
                            </div>
                        </div>

                        <!-- Action Buttons -->
                        <div class="d-grid gap-2">
                            <button class="btn btn-primary btn-lg" onclick="startMining()" id="startMiningBtn">
                                <i class="fas fa-play me-2"></i>
                                Start Mining
                            </button>
                            <button class="btn btn-warning btn-sm" onclick="cancelMining()" id="cancelMiningBtn" style="display: none;">
                                <i class="fas fa-stop me-2"></i>
                                Cancel Mining
                            </button>
                        </div>

                        <!-- Progress Bar for API Mining -->
                        <div id="progress-container" class="progress-container">
                            <div class="d-flex justify-content-between mb-1">
                                <span class="text-muted">Mining Progress</span>
                                <span class="text-muted" id="progress-percentage">0%</span>
                            </div>
                            <div class="progress mb-2">
                                <div class="progress-bar progress-bar-striped progress-bar-animated bg-primary" 
                                     id="progress-bar" role="progressbar" style="width: 0%"></div>
                            </div>
                            <div class="text-center">
                                <small class="text-muted" id="progress-message">Initializing...</small>
                            </div>
                        </div>

                        <!-- Mining Status -->
                        <div id="mining-status" class="mt-3" style="display: none;"></div>
                    </div>
                </div>
            </div>

            <!-- Results Panel -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5><i class="fas fa-chart-bar me-2"></i>Mining Results</h5>
                        <button class="btn btn-outline-success btn-sm" onclick="exportCSV()" id="exportBtn" disabled>
                            <i class="fas fa-download me-1"></i>
                            Export CSV
                        </button>
                    </div>
                    <div class="card-body">
                        <div id="mining-results">
                            <div class="text-center text-muted py-5">
                                <i class="fas fa-chart-bar fa-3x mb-3"></i>
                                <p>No mining results yet.<br>Start a mining operation to see results here.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Recommendations Section -->
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-lightbulb me-2"></i>Item Recommendations</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-8">
                                <div class="input-group">
                                    <input type="text" class="form-control" id="itemSearch" 
                                           placeholder="Enter item name to get recommendations...">
                                    <button class="btn btn-outline-primary" onclick="getRecommendations()">
                                        <i class="fas fa-search me-1"></i>
                                        Get Recommendations
                                    </button>
                                </div>
                            </div>
                        </div>
                        <div id="recommendations-results" class="mt-3"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Live Logs Section -->
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5><i class="fas fa-terminal me-2"></i>Live Mining Logs</h5>
                        <div>
                            <button class="btn btn-outline-success btn-sm me-2" onclick="toggleAutoRefresh()" id="autoRefreshBtn">
                                <i class="fas fa-play me-1"></i>
                                Auto Refresh
                            </button>
                            <button class="btn btn-outline-secondary btn-sm" onclick="refreshLogs()">
                                <i class="fas fa-sync me-1"></i>
                                Refresh
                            </button>
                        </div>
                    </div>
                    <div class="card-body">
                        <div id="live-logs" style="max-height: 400px; overflow-y: auto; background-color: #f8f9fa; padding: 15px; border-radius: 5px; font-family: monospace; font-size: 0.9em;">
                            <div class="text-center text-muted py-3">
                                <i class="fas fa-terminal fa-2x mb-2"></i>
                                <p>Live logs will appear here during mining operations.</p>
                                <small>Click "Auto Refresh" to start monitoring logs in real-time.</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let currentRules = [];
        let progressInterval = null;
        let currentTaskId = null;

        // Check connections on page load
        window.onload = function() {
            checkConnections();
            
            // Toggle API options based on mining method
            document.querySelectorAll('input[name="miningMethod"]').forEach(radio => {
                radio.addEventListener('change', function() {
                    document.getElementById('apiOptions').style.display = 
                        this.value === 'api' ? 'block' : 'none';
                });
            });
        };

        function checkConnections() {
            document.getElementById('server-status').innerHTML = 
                '<span class="status-indicator status-disconnected"></span><span>Checking...</span>';
            document.getElementById('database-status').innerHTML = 
                '<span class="status-indicator status-disconnected"></span><span>Checking...</span>';

            fetch('/api/test-connection')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Server status
                        const serverStatus = data.server.connected 
                            ? '<span class="status-indicator status-connected"></span><span>Connected</span>'
                            : '<span class="status-indicator status-disconnected"></span><span>Disconnected</span>';
                        document.getElementById('server-status').innerHTML = serverStatus;

                        // Database status
                        const dbStatus = data.database.connected 
                            ? '<span class="status-indicator status-connected"></span><span>Connected</span>'
                            : '<span class="status-indicator status-disconnected"></span><span>Error: ' + (data.database.error || 'Unknown') + '</span>';
                        document.getElementById('database-status').innerHTML = dbStatus;
                    } else {
                        document.getElementById('server-status').innerHTML = 
                            '<span class="status-indicator status-disconnected"></span><span>Error: ' + data.error + '</span>';
                        document.getElementById('database-status').innerHTML = 
                            '<span class="status-indicator status-disconnected"></span><span>Cannot check</span>';
                    }
                })
                .catch(error => {
                    document.getElementById('server-status').innerHTML = 
                        '<span class="status-indicator status-disconnected"></span><span>Connection failed</span>';
                    document.getElementById('database-status').innerHTML = 
                        '<span class="status-indicator status-disconnected"></span><span>Connection failed</span>';
                });
        }

        function startMining() {
            const miningMethod = document.querySelector('input[name="miningMethod"]:checked').value;
            const daysBack = parseInt(document.getElementById('daysBack').value);
            const topSkus = parseInt(document.getElementById('topSkus').value);
            
            // Show status
            const statusDiv = document.getElementById('mining-status');
            statusDiv.style.display = 'block';
            statusDiv.innerHTML = '<div class="alert alert-info"><i class="fas fa-spinner fa-spin me-2"></i>Starting mining operation...</div>';

            if (miningMethod === 'direct') {
                // Direct mining
                fetch('/api/mine-direct', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        days_back: daysBack,
                        top_skus: topSkus
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        displayResults(data.stats, data.rules);
                        statusDiv.innerHTML = '<div class="alert alert-success"><i class="fas fa-check me-2"></i>Mining completed successfully!</div>';
                    } else {
                        statusDiv.innerHTML = '<div class="alert alert-danger"><i class="fas fa-exclamation-triangle me-2"></i>Error: ' + data.error + '</div>';
                    }
                })
                .catch(error => {
                    statusDiv.innerHTML = '<div class="alert alert-danger"><i class="fas fa-exclamation-triangle me-2"></i>Error: ' + error + '</div>';
                });
            } else {
                // API mining with progress tracking
                const useEnhanced = document.getElementById('useEnhanced').checked;
                const timeMethod = document.getElementById('timeMethod').value;

                // Show progress bar
                showProgressBar();
                
                // Choose endpoint based on enhanced mining option
                const endpoint = useEnhanced ? '/api/mine-enhanced' : '/api/mine-api';
                const payload = {
                    days_back: daysBack,
                    top_skus: topSkus
                };
                
                // Add enhanced options if using enhanced mining
                if (!useEnhanced) {
                    payload.use_enhanced_mining = false;
                    payload.time_weighting_method = timeMethod;
                }
                
                fetch(endpoint, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        currentTaskId = data.task_id;
                        statusDiv.innerHTML = '<div class="alert alert-info"><i class="fas fa-clock me-2"></i>' + 
                            (useEnhanced ? 'Enhanced Temporal Mining' : 'API Mining') + ' started! Tracking progress...</div>';
                        
                        // Start progress monitoring
                        startProgressMonitoring();
                    } else {
                        hideProgressBar();
                        statusDiv.innerHTML = '<div class="alert alert-danger"><i class="fas fa-exclamation-triangle me-2"></i>Error: ' + data.error + '</div>';
                    }
                })
                .catch(error => {
                    hideProgressBar();
                    statusDiv.innerHTML = '<div class="alert alert-danger"><i class="fas fa-exclamation-triangle me-2"></i>Error: ' + error + '</div>';
                });
            }
        }

        function showProgressBar() {
            document.getElementById('progress-container').style.display = 'block';
            document.getElementById('startMiningBtn').style.display = 'none';
            document.getElementById('cancelMiningBtn').style.display = 'block';
        }

        function hideProgressBar() {
            document.getElementById('progress-container').style.display = 'none';
            document.getElementById('startMiningBtn').style.display = 'block';
            document.getElementById('cancelMiningBtn').style.display = 'none';
            
            if (progressInterval) {
                clearInterval(progressInterval);
                progressInterval = null;
            }
        }

        function startProgressMonitoring() {
            progressInterval = setInterval(() => {
                fetch('/api/mining-progress')
                    .then(response => response.json())
                    .then(data => {
                        updateProgress(data.progress, data.message);
                        
                        if (data.status === 'completed') {
                            clearInterval(progressInterval);
                            progressInterval = null;
                            hideProgressBar();
                            
                            // Debug: Log the complete data structure
                            console.log('Task completed. Full data structure:', data);
                            console.log('data.result exists:', !!data.result);
                            console.log('data.stats exists:', !!data.stats);
                            console.log('data.rules exists:', !!data.rules);
                            console.log('data.rules length:', data.rules ? data.rules.length : 'N/A');
                            
                            // Check if we have results (using the extracted stats and rules from Flask endpoint)
                            if (data.result && data.stats && data.rules && data.rules.length > 0) {
                                displayResults(data.stats, data.rules);
                                
                                // Show comprehensive mining results
                                let message = '<div class="alert alert-success"><i class="fas fa-check me-2"></i>API mining completed successfully!<br>';
                                message += '<strong>Generated:</strong> ' + data.stats.total_rules + ' total rules<br>';
                                if (data.stats.displayed_rules && data.stats.displayed_rules < data.stats.total_rules) {
                                    message += '<strong>Displayed:</strong> Top ' + data.stats.displayed_rules + ' rules (UI limit)<br>';
                                }
                                message += '<strong>Saved to database:</strong> All ' + data.stats.total_rules + ' rules</div>';
                                
                                document.getElementById('mining-status').innerHTML = message;
                            } else if (data.result && data.stats && (!data.rules || data.rules.length === 0)) {
                                document.getElementById('mining-status').innerHTML = 
                                    '<div class="alert alert-warning"><i class="fas fa-exclamation-triangle me-2"></i>Mining completed but no association rules found. Try lowering the confidence threshold.</div>';
                            } else if (data.error) {
                                document.getElementById('mining-status').innerHTML = 
                                    '<div class="alert alert-warning"><i class="fas fa-exclamation-triangle me-2"></i>Mining completed but results unavailable: ' + data.error + '</div>';
                            } else {
                                // Debug: Log the data structure to console
                                console.log('Mining completed but no results. Data structure:', data);
                                document.getElementById('mining-status').innerHTML = 
                                    '<div class="alert alert-warning"><i class="fas fa-exclamation-triangle me-2"></i>Mining completed but no results returned. Check console for debug info.</div>';
                            }
                        } else if (data.status === 'failed') {
                            clearInterval(progressInterval);
                            progressInterval = null;
                            hideProgressBar();
                            
                            const errorMsg = data.error || data.message || 'Unknown error occurred';
                            document.getElementById('mining-status').innerHTML = 
                                '<div class="alert alert-danger"><i class="fas fa-exclamation-triangle me-2"></i>Mining failed: ' + errorMsg + '</div>';
                        }
                    })
                    .catch(error => {
                        console.error('Progress monitoring error:', error);
                        document.getElementById('progress-message').textContent = 'Connection error: ' + error.message;
                    });
            }, 2000); // Check every 2 seconds
        }

        function updateProgress(percentage, message) {
            document.getElementById('progress-bar').style.width = percentage + '%';
            document.getElementById('progress-percentage').textContent = percentage + '%';
            document.getElementById('progress-message').textContent = message;
        }

        function cancelMining() {
            if (progressInterval) {
                clearInterval(progressInterval);
                progressInterval = null;
            }
            hideProgressBar();
            document.getElementById('mining-status').innerHTML = 
                '<div class="alert alert-warning"><i class="fas fa-exclamation-triangle me-2"></i>Mining operation cancelled by user.</div>';
        }

        function displayResults(stats, rules) {
            const resultsDiv = document.getElementById('mining-results');
            currentRules = rules;
            
            let html = `
                <div class="row mb-3">
                    <div class="col-md-3">
                        <div class="text-center">
                            <div class="h4 mb-0">${stats.total_rules}</div>
                            <small class="text-muted">Total Rules</small>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="text-center">
                            <div class="h4 mb-0">${stats.top_n_skus}</div>
                            <small class="text-muted">Top SKUs</small>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="text-center">
                            <div class="h4 mb-0">${stats.total_orders}</div>
                            <small class="text-muted">Orders</small>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="text-center">
                            <div class="h4 mb-0">${stats.score_range.max.toFixed(3)}</div>
                            <small class="text-muted">Max Score</small>
                        </div>
                    </div>
                </div>
                <div class="border-top pt-3">
                    <h6>Top Association Rules</h6>
            `;

            rules.slice(0, 10).forEach((rule, index) => {
                const scoreColor = rule.association_composite_score > 0.7 ? 'success' : 
                                 rule.association_composite_score > 0.5 ? 'warning' : 'secondary';
                
                html += `
                    <div class="rule-card p-2 border rounded mb-2">
                        <div class="d-flex justify-content-between align-items-center">
                            <div class="flex-grow-1">
                                <strong>${rule.sku1.substring(0, 25)}${rule.sku1.length > 25 ? '...' : ''}</strong>
                                <i class="fas fa-arrow-right mx-2 text-muted"></i>
                                <strong>${rule.sku2.substring(0, 25)}${rule.sku2.length > 25 ? '...' : ''}</strong>
                            </div>
                            <span class="badge bg-${scoreColor} score-badge">${rule.association_composite_score.toFixed(4)}</span>
                        </div>
                    </div>
                `;
            });

            html += '</div>';
            resultsDiv.innerHTML = html;
            
            // Enable export button
            document.getElementById('exportBtn').disabled = false;
        }

        function getRecommendations() {
            const item = document.getElementById('itemSearch').value.trim();
            if (!item) {
                alert('Please enter an item name');
                return;
            }

            const resultsDiv = document.getElementById('recommendations-results');
            resultsDiv.innerHTML = '<div class="alert alert-info"><i class="fas fa-spinner fa-spin me-2"></i>Getting recommendations...</div>';

            fetch(`/api/recommendations/${encodeURIComponent(item)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.data.recommendations) {
                        const recommendations = data.data.recommendations;
                        if (recommendations.length > 0) {
                            let html = '<h6>Recommendations for: ' + data.data.main_item + '</h6><ul class="list-group list-group-flush">';
                            recommendations.forEach((rec, index) => {
                                html += '<li class="list-group-item d-flex justify-content-between align-items-center">' +
                                    rec.recommended_item.substring(0, 30) +
                                    '<span class="badge bg-primary rounded-pill">' + rec.score.toFixed(4) + '</span></li>';
                            });
                            html += '</ul>';
                            resultsDiv.innerHTML = html;
                        } else {
                            resultsDiv.innerHTML = '<div class="alert alert-warning">No recommendations found for this item.</div>';
                        }
                    } else {
                        resultsDiv.innerHTML = '<div class="alert alert-danger">Error: ' + (data.error || 'Unknown error') + '</div>';
                    }
                })
                .catch(error => {
                    resultsDiv.innerHTML = '<div class="alert alert-danger">Error: ' + error + '</div>';
                });
        }
        
        function exportCSV() {
            if (currentRules.length === 0) {
                alert('No rules to export');
                return;
            }
            
            fetch('/api/export-csv', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({rules: currentRules})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Create download link
                    const link = document.createElement('a');
                    link.href = '/download/' + data.filename;
                    link.download = data.filename;
                    link.click();
                } else {
                    alert('Export failed: ' + data.error);
                }
            })
            .catch(error => {
                alert('Export error: ' + error);
            });
        }

        // Toggle method section based on enhanced mining checkbox
        document.getElementById('useEnhanced').addEventListener('change', function() {
            const methodSection = document.getElementById('methodSection');
            methodSection.style.display = this.checked ? 'block' : 'none';
        });

        // Live Logs Functionality
        let logRefreshInterval = null;
        let autoRefreshEnabled = false;

        function refreshLogs() {
            fetch('/api/logs/live')
                .then(response => response.json())
                .then(logs => {
                    const logsContainer = document.getElementById('live-logs');
                    
                    if (logs.length === 0) {
                        logsContainer.innerHTML = `
                            <div class="text-center text-muted py-3">
                                <i class="fas fa-terminal fa-2x mb-2"></i>
                                <p>No recent logs found.</p>
                                <small>Logs will appear here when mining operations are running.</small>
                            </div>`;
                        return;
                    }

                    let logHtml = '';
                    logs.forEach(log => {
                        const levelClass = getLevelClass(log.level);
                        const levelIcon = getLevelIcon(log.level);
                        
                        logHtml += `
                            <div class="log-entry mb-2 p-2 border-start border-2 ${levelClass}" style="border-color: ${getLevelColor(log.level)} !important;">
                                <div class="d-flex justify-content-between align-items-start">
                                    <div class="flex-grow-1">
                                        <small class="text-muted me-2">${log.timestamp}</small>
                                        <span class="badge ${levelClass} me-2">
                                            <i class="${levelIcon} me-1"></i>${log.level}
                                        </span>
                                        <small class="text-muted">${log.source || 'unknown'}</small>
                                    </div>
                                </div>
                                <div class="mt-1" style="white-space: pre-wrap; word-break: break-all;">
                                    ${escapeHtml(log.message)}
                                </div>
                            </div>`;
                    });

                    logsContainer.innerHTML = logHtml;
                    // Auto-scroll to bottom to show latest logs
                    logsContainer.scrollTop = logsContainer.scrollHeight;
                })
                .catch(error => {
                    console.error('Error fetching logs:', error);
                    const logsContainer = document.getElementById('live-logs');
                    logsContainer.innerHTML = `
                        <div class="text-center text-danger py-3">
                            <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                            <p>Error loading logs: ${error.message}</p>
                        </div>`;
                });
        }

        function toggleAutoRefresh() {
            const btn = document.getElementById('autoRefreshBtn');
            
            if (autoRefreshEnabled) {
                // Stop auto refresh
                if (logRefreshInterval) {
                    clearInterval(logRefreshInterval);
                    logRefreshInterval = null;
                }
                autoRefreshEnabled = false;
                btn.innerHTML = '<i class="fas fa-play me-1"></i>Auto Refresh';
                btn.className = 'btn btn-outline-success btn-sm me-2';
            } else {
                // Start auto refresh
                autoRefreshEnabled = true;
                btn.innerHTML = '<i class="fas fa-pause me-1"></i>Stop Auto Refresh';
                btn.className = 'btn btn-outline-warning btn-sm me-2';
                
                // Refresh immediately
                refreshLogs();
                
                // Set up interval for every 2 seconds
                logRefreshInterval = setInterval(refreshLogs, 2000);
            }
        }

        function getLevelClass(level) {
            switch(level) {
                case 'ERROR': return 'bg-danger text-white';
                case 'WARNING': return 'bg-warning text-dark';
                case 'INFO': return 'bg-info text-white';
                case 'DEBUG': return 'bg-secondary text-white';
                default: return 'bg-light text-dark';
            }
        }

        function getLevelIcon(level) {
            switch(level) {
                case 'ERROR': return 'fas fa-times-circle';
                case 'WARNING': return 'fas fa-exclamation-triangle';
                case 'INFO': return 'fas fa-info-circle';
                case 'DEBUG': return 'fas fa-bug';
                default: return 'fas fa-circle';
            }
        }

        function getLevelColor(level) {
            switch(level) {
                case 'ERROR': return '#dc3545';
                case 'WARNING': return '#ffc107';
                case 'INFO': return '#0dcaf0';
                case 'DEBUG': return '#6c757d';
                default: return '#dee2e6';
            }
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Start auto-refresh when mining operations begin
        function startMiningWithLogs() {
            // Enable auto-refresh for logs when mining starts
            if (!autoRefreshEnabled) {
                toggleAutoRefresh();
            }
        }

        // Modify the original startMining function to include log monitoring
        const originalStartMining = startMining;
        startMining = function() {
            originalStartMining();
            startMiningWithLogs();
        };
    </script>
</body>
</html>'''
    
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("[START] Starting Enhanced Association Rule Mining Dashboard...")
    print("[INFO] Open your browser to: http://localhost:5000")
    print("[WARN] FastAPI server should be running on http://127.0.0.1:8080 for API-based mining")
    
    app.run(debug=True, host='0.0.0.0', port=5000)