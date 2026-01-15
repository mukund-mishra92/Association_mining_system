"""
Direct Mining Service - Fast mining for direct/immediate requests
Uses Apriori algorithm with minimal processing for speed
"""
import time
import logging
from datetime import datetime
import pymysql
import pandas as pd
import numpy as np
from mlxtend.frequent_patterns import apriori, association_rules
from app.shared.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


def save_rules_to_database(user_config, rules_df, sku_name_to_id):
    """
    Save association rules to database using shared DatabaseConnection.save_recommendations
    
    Args:
        user_config: Database configuration dictionary
        rules_df: DataFrame with columns sku1, sku2, association_composite_score, confidence, lift, support
        sku_name_to_id: Dictionary mapping SKU_NAME to SKU_ID
        
    Returns:
        dict: Summary statistics from save operation
    """
    try:
        logger.info(f"Saving {len(rules_df)} rules to {user_config['recommendations_table']}")
        
        # Build recommendations DataFrame compatible with DatabaseConnection.save_recommendations
        records = []
        for _, rule in rules_df.iterrows():
            parent_id = sku_name_to_id.get(rule['sku1'], rule['sku1'])
            child_id = sku_name_to_id.get(rule['sku2'], rule['sku2'])
            
            records.append({
                "main_item": parent_id,
                "recommended_item": child_id,
                "main_item_name": rule['sku1'],
                "recommended_item_name": rule['sku2'],
                "confidence_score": float(rule.get('confidence', 0.0)),
                "lift_score": float(rule.get('lift', 0.0)),
                "support_score": float(rule.get('support', 0.0)),
                "composite_score": float(rule['association_composite_score']),
                "temporal_stability": 0.5,
                "temporal_trend": 0.0,
                "temporal_composite_score": float(rule['association_composite_score']),
                "recommendation_rank": 1,
            })
        
        if not records:
            logger.warning("No rules to save")
            return None
        
        recommendations_df = pd.DataFrame(records)
        
        # Use shared DatabaseConnection with save_recommendations method
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
            logger.error("Failed to connect to database")
            return None
        
        try:
            summary = db.save_recommendations(recommendations_df)
        finally:
            db.disconnect()
        
        if not summary:
            logger.error("save_recommendations returned empty summary")
            return None
        
        logger.info(
            f"✅ Saved using DatabaseConnection.save_recommendations: "
            f"{summary.get('total_written', 0)} written, "
            f"{summary.get('new_inserts', 0)} inserts, "
            f"{summary.get('updated_existing', 0)} updates"
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"Database save error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


# Default database configuration - loaded from config or fallback
try:
    from app.shared.config.config import config
    
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
    logger.info(f"Loaded database configuration from .env file")
except Exception as e:
    logger.warning(f"Could not load configuration from .env, using defaults: {e}")
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