from flask import Flask, render_template, request, jsonify, send_file
import requests
import pandas as pd
import numpy as np
import mysql.connector
from datetime import datetime
import json
import os
import time
import logging
from mlxtend.frequent_patterns import apriori, association_rules
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('association_mining.log'),
        logging.StreamHandler()
    ]
)

# Configuration - Updated for port 8001
BASE_URL = "http://127.0.0.1:8001"
API_BASE = f"{BASE_URL}/api/v1"

# Global variable to store user-defined database configuration
USER_DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'neo',
    'order_table': 'wms_to_wcs_order_line_request_data',
    'sku_master_table': 'sku_master',
    'recommendations_table': 'sku_recommendations'
}

def load_config():
    """Load database configuration"""
    try:
        import sys
        sys.path.append('.')
        from app.utils.config import config
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

def save_rules_to_database(user_config, rules_df):
    """Save association rules to database"""
    try:
        logger = logging.getLogger(__name__)
        logger.info(f"Saving {len(rules_df)} recommendations to table: {user_config['recommendations_table']}")
        
        # Connect to database
        connection = mysql.connector.connect(
            host=user_config['host'],
            user=user_config['user'],
            password=user_config['password'],
            database=user_config['database']
        )
        cursor = connection.cursor()
        
        # First ensure the table exists with correct schema
        table_name = user_config['recommendations_table']
        
        # Drop and recreate table to ensure correct schema
        drop_query = f"DROP TABLE IF EXISTS {table_name}"
        cursor.execute(drop_query)
        logger.info(f"Recreated table: {table_name}")
        
        create_query = f"""
        CREATE TABLE {table_name} (
            SCORE_ID BIGINT NOT NULL AUTO_INCREMENT,
            PARENT_ARTICLE_ID VARCHAR(200) NOT NULL,
            CHILD_ARTICLE_ID VARCHAR(200) NOT NULL,
            PROXIMITY_SCORE DECIMAL(10,3) NULL,
            PRIMARY KEY (PARENT_ARTICLE_ID, CHILD_ARTICLE_ID),
            KEY SCORE_ID_INDEX (SCORE_ID)
        )
        """
        cursor.execute(create_query)
        
        # Prepare rules data for insertion
        recommendations_data = []
        for _, rule in rules_df.iterrows():
            recommendations_data.append((
                rule['sku1'],  # PARENT_ARTICLE_ID
                rule['sku2'],  # CHILD_ARTICLE_ID
                float(rule['association_composite_score'])  # PROXIMITY_SCORE
            ))
        
        # Insert recommendations
        insert_query = f"""
        INSERT INTO {table_name} 
        (PARENT_ARTICLE_ID, CHILD_ARTICLE_ID, PROXIMITY_SCORE)
        VALUES (%s, %s, %s)
        """
        
        cursor.executemany(insert_query, recommendations_data)
        connection.commit()
        
        logger.info(f"Successfully saved {len(recommendations_data)} recommendations to {table_name}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Database save error: {e}")
        return False

def generate_rules_top_skus(user_config=None, top_n=20, days_back=60):
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
        conn = mysql.connector.connect(
            host=user_config['host'],
            user=user_config['user'],
            password=user_config['password'],
            database=user_config['database']
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
        placeholders = ','.join(['%s'] * len(popular_sku_list))
        main_query = f"""
        SELECT 
            o.ORDER_ID,
            s.SKU_NAME,
            DATEDIFF(CURDATE(), DATE(o.INSERTED_TIMESTAMP)) as days_ago
        FROM {user_config['order_table']} o
        JOIN {user_config['sku_master_table']} s ON o.ARTICLE_ID = s.SKU_ID
        WHERE o.INSERTED_TIMESTAMP >= DATE_SUB(CURDATE(), INTERVAL {days_back} DAY)
        AND s.SKU_NAME IN ({placeholders})
        """
        
        df = pd.read_sql(main_query, conn, params=popular_sku_list)
        conn.close()
        
        if df.empty:
            return {"error": "No order data found"}, None
        
        # Apply simple time weighting
        df['weight'] = np.exp(-df['days_ago'] / 30)
        
        # Create market basket (simple binary)
        basket = df.groupby(['ORDER_ID', 'SKU_NAME'])['weight'].sum().reset_index()
        basket_matrix = basket.pivot_table(
            index='ORDER_ID', 
            columns='SKU_NAME', 
            values='weight', 
            fill_value=0
        )
        basket_binary = (basket_matrix > 0).astype(int)
        
        # Mine with very high support
        frequent_itemsets = apriori(basket_binary, min_support=0.03, use_colnames=True, max_len=2)
        
        if len(frequent_itemsets) == 0:
            # Try lower threshold
            frequent_itemsets = apriori(basket_binary, min_support=0.02, use_colnames=True, max_len=2)
        
        if len(frequent_itemsets) > 0:
            # Generate rules
            rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.2)
            
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
                
                # Save to database
                database_saved = False
                try:
                    database_saved = save_rules_to_database(user_config, final_rules)
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
                
                return stats, final_rules.to_dict('records')
        
        return {"error": "No association rules could be generated"}, None
        
    except Exception as e:
        return {"error": str(e)}, None

def direct_mining(user_config=None, days_back=30):
    """Direct mining without API - updated to use user configuration"""
    return generate_rules_top_skus(user_config, top_n=20, days_back=days_back)

@app.route('/')
def index():
    """Main dashboard page - Complete integrated system"""
    return render_template('complete_dashboard_enhanced.html')

@app.route('/api/db-config', methods=['GET'])
def get_db_config():
    """Get current database configuration"""
    return jsonify({
        "success": True,
        "config": USER_DB_CONFIG
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
            
            # Update global configuration
            USER_DB_CONFIG.update({
                'host': data.get('host', 'localhost'),
                'user': data.get('user', 'root'),
                'password': data.get('password', ''),
                'database': data.get('database', 'neo'),
                'order_table': data.get('order_table', 'wms_to_wcs_order_line_request_data'),
                'sku_master_table': data.get('sku_master_table', 'sku_master'),
                'recommendations_table': data.get('recommendations_table', 'sku_recommendations')
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
        data = request.get_json() if request.get_json() else USER_DB_CONFIG
        
        logger.info("Testing database connection")
        
        # Test database connection
        conn = mysql.connector.connect(
            host=data.get('host', 'localhost'),
            user=data.get('user', 'root'),
            password=data.get('password', ''),
            database=data.get('database', 'neo'),
            connection_timeout=5
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        
        # Test if tables exist - use CURRENT USER CONFIGURATION
        tables_status = {}
        test_tables = {
            'order': data.get('order_table', 'wms_to_wcs_order_line_request_data'),
            'sku_master': data.get('sku_master_table', 'sku_master'), 
            'recommendations': data.get('recommendations_table', 'sku_recommendations')
        }
        
        logger.info(f"Testing tables: {list(test_tables.keys())}")
        
        for table_key, table_name in test_tables.items():
            if table_name:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name} LIMIT 1")
                    count = cursor.fetchone()[0]
                    tables_status[table_key] = {"exists": True, "count": count}
                    logger.info(f"Table {table_name}: {count} records")
                except mysql.connector.Error as e:
                    tables_status[table_key] = {"exists": False, "count": 0}
                    logger.warning(f"Table {table_name} does not exist: {e}")
            else:
                tables_status[table_key] = {"exists": False, "count": 0}
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Database connection successful",
            "mysql_version": version[0] if version else "Unknown",
            "tables": tables_status
        })
        
    except mysql.connector.Error as e:
        return jsonify({
            "success": False,
            "error": f"Database connection failed: {str(e)}"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/test-connection')
def test_connection():
    """Test server and database connection"""
    config = load_config()
    if not config:
        return jsonify({"success": False, "error": "Could not load configuration"})
    
    # Test server connection
    server_ok, server_data = test_server_connection()
    
    # Test database connection
    db_ok = False
    db_error = None
    try:
        conn = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
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
    
    try:
        # Use user-defined database configuration
        stats, rules = generate_rules_top_skus(USER_DB_CONFIG, top_n=top_skus, days_back=days_back)
        
        if 'error' in stats:
            return jsonify({"success": False, "error": stats['error']})
        
        return jsonify({
            "success": True,
            "stats": stats,
            "rules": rules[:100]  # Limit to first 100 rules for display
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

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
    """Mine using the API server with progress tracking"""
    global api_mining_status
    
    data = request.get_json()
    
    payload = {
        "days_back": data.get('days_back', 30),
        "use_enhanced_mining": data.get('use_enhanced_mining', False),
        "time_weighting_method": data.get('time_weighting_method', 'exponential_decay'),
        "db_config": USER_DB_CONFIG  # Include database configuration
    }
    
    try:
        # Start mining request
        api_mining_status = {
            "status": "starting",
            "task_id": None,
            "progress": 0,
            "message": "Sending request to API server...",
            "start_time": time.time()
        }
        
        response = requests.post(f"{API_BASE}/mine-rules", json=payload, timeout=30)
        
        if response.status_code == 200:
            response_data = response.json()
            api_mining_status.update({
                "status": "running",
                "task_id": response_data.get('task_id'),
                "progress": 10,
                "message": "Mining request accepted by API server"
            })
            
            return jsonify({
                "success": True, 
                "data": response_data,
                "task_id": response_data.get('task_id'),
                "message": "Mining started successfully"
            })
        else:
            api_mining_status.update({
                "status": "failed",
                "message": f"API error: {response.text}"
            })
            return jsonify({"success": False, "error": f"API server error: {response.text}"})
            
    except Exception as e:
        api_mining_status.update({
            "status": "failed",
            "message": f"Connection error: {str(e)}"
        })
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/mining-progress')
def get_mining_progress():
    """Get current mining progress"""
    global api_mining_status
    
    # If we have a task_id and haven't gotten the final results yet, check the API server
    if (api_mining_status.get("task_id") and 
        (api_mining_status.get("status") in ["running", "starting"] or 
         (api_mining_status.get("status") == "completed" and not api_mining_status.get("rules")))):
        try:
            # Check task status from API
            task_response = requests.get(f"{API_BASE}/task/{api_mining_status['task_id']}", timeout=10)
            
            if task_response.status_code == 200:
                task_data = task_response.json()
                task_status = task_data.get('status', 'running')
                
                # Update local status
                api_mining_status.update({
                    "status": task_status,
                    "progress": int(task_data.get('progress', 0) * 100),
                    "message": task_data.get('message', 'Processing...'),
                })
                
                # If completed, get the results from task data
                if task_status == 'completed':
                    try:
                        # Results should be in the task data itself
                        task_result = task_data.get('result', {})
                        
                        print(f"DEBUG: Task result keys: {list(task_result.keys()) if task_result else 'None'}")
                        print(f"DEBUG: Task result type: {type(task_result)}")
                        
                        if task_result:
                            stats = task_result.get('stats', {})
                            rules = task_result.get('rules', [])
                            
                            print(f"DEBUG: Stats keys: {list(stats.keys()) if stats else 'None'}")
                            print(f"DEBUG: Rules count: {len(rules) if rules else 0}")
                            
                            api_mining_status.update({
                                "status": "completed",
                                "progress": 100,
                                "message": "Mining completed successfully!",
                                "result": task_result,
                                "stats": stats,
                                "rules": rules[:100]  # First 100 rules
                            })
                        else:
                            api_mining_status.update({
                                "status": "completed",
                                "progress": 100,
                                "message": "Mining completed but no results found",
                                "error": "No result data in task"
                            })
                    except Exception as e:
                        api_mining_status.update({
                            "status": "completed",
                            "progress": 100,
                            "message": f"Mining completed but result processing error: {str(e)}",
                            "error": str(e)
                        })
                
                # If failed, get error details
                elif task_status == 'failed':
                    error_msg = task_data.get('error', 'Unknown error occurred')
                    api_mining_status.update({
                        "status": "failed",
                        "progress": 0,
                        "message": f"Mining failed: {error_msg}",
                        "error": error_msg
                    })
                    
        except Exception as e:
            # If we can't get progress, estimate based on time elapsed
            elapsed = time.time() - api_mining_status.get('start_time', time.time())
            estimated_progress = min(90, int(elapsed / 6))  # Roughly 1% per 6 seconds, max 90%
            
            api_mining_status.update({
                "progress": estimated_progress,
                "message": f"Processing... ({elapsed:.0f}s elapsed, connection issue: {str(e)})"
            })
    
    return jsonify(api_mining_status)

@app.route('/api/mine-enhanced', methods=['POST'])
def mine_enhanced():
    """Enhanced Temporal Mining using FastAPI backend"""
    global api_mining_status
    logger = logging.getLogger(__name__)
    
    data = request.get_json()
    
    payload = {
        "days_back": data.get('days_back', 30),
        "use_enhanced_mining": True,  # Always use enhanced for this endpoint
        "time_weighting_method": data.get('time_weighting_method', 'exponential_decay'),
        "db_config": USER_DB_CONFIG  # Include database configuration
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
        return jsonify({"success": False, "error": str(e)})

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
    """Get live logs from all recent log files"""
    try:
        import glob
        import os
        from datetime import datetime
        
        # Look for log files from today
        today = datetime.now().strftime('%Y%m%d')
        log_patterns = [
            f'logs/mining_detailed_{today}_*.log',
            f'logs/api_detailed_{today}_*.log',
            f'logs/performance_{today}_*.log'
        ]
        
        logs = []
        for pattern in log_patterns:
            for log_file in glob.glob(pattern):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        # Get recent lines
                        recent_lines = lines[-20:] if len(lines) > 20 else lines
                        for line in recent_lines:
                            if any(keyword in line for keyword in ['INFO', 'ERROR', 'WARNING']):
                                # Parse log line format: timestamp | level | logger | message
                                parts = line.strip().split(' | ')
                                if len(parts) >= 4:
                                    timestamp = parts[0]
                                    level = parts[1]
                                    logger_name = parts[2]
                                    message = ' | '.join(parts[3:])
                                    logs.append({
                                        'timestamp': timestamp,
                                        'level': level,
                                        'logger': logger_name,
                                        'message': message,
                                        'source': os.path.basename(log_file)
                                    })
                except Exception as e:
                    continue
        
        # Sort logs by timestamp and return recent ones
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        return jsonify(logs[:30])  # Return last 30 log entries
        
    except Exception as e:
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
                                document.getElementById('mining-status').innerHTML = 
                                    '<div class="alert alert-success"><i class="fas fa-check me-2"></i>API mining completed successfully! Found ' + data.stats.total_rules + ' rules.</div>';
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
    
    print("🚀 Starting Enhanced Association Rule Mining Dashboard...")
    print("📍 Open your browser to: http://localhost:5000")
    print("⚠️  FastAPI server should be running on http://127.0.0.1:8001 for API-based mining")
    
    app.run(debug=True, host='0.0.0.0', port=5000)