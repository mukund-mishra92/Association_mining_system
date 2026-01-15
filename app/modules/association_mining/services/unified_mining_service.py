"""
Unified Mining Service - Single source of truth for all mining operations
Uses CleanAssociationMiningService for consistent rule generation
"""

import logging
import pandas as pd
import pymysql
from datetime import datetime
from app.modules.association_mining.services.clean_mining_service import CleanAssociationMiningService
from app.shared.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class UnifiedMiningService:
    """Unified service for all mining operations (API, UI, Scheduler)"""
    
    def __init__(self, db_config, mining_params):
        self.db_config = db_config
        self.mining_params = mining_params
        
    def run_mining(self, task_id=None, task_manager=None):
        """
        Run mining using CleanAssociationMiningService
        Returns: dict with results and stats
        """
        try:
            start_time = datetime.now()
            
            # 1. Load data from database
            logger.info("Loading order data from database...")
            df_basket = self._load_order_data()
            
            if df_basket.empty:
                logger.warning("No order data found")
                return {
                    "success": False,
                    "error": "No order data found",
                    "rules_generated": 0,
                    "records_processed": 0
                }
            
            logger.info(f"Loaded {len(df_basket)} order records")
            
            # 2. Run clean mining service
            logger.info(f"Running CleanAssociationMiningService with params: {self.mining_params}")
            mining_service = CleanAssociationMiningService(
                task_id=task_id,
                task_manager=task_manager,
                algorithm_params=self.mining_params
            )
            
            recommendations_df = mining_service.run_mining_pipeline(df_basket)
            
            if recommendations_df.empty:
                logger.warning("No recommendations generated")
                return {
                    "success": True,
                    "rules_generated": 0,
                    "records_processed": len(df_basket),
                    "stats": {
                        "total_orders": df_basket['ORDER_ID'].nunique() if 'ORDER_ID' in df_basket.columns else 0
                    }
                }
            
            # 3. Save recommendations to database using shared DatabaseConnection
            logger.info(f"Saving {len(recommendations_df)} recommendations...")
            output_table = self.mining_params.get('output_table', 'sku_recommendations')
            
            # Use the proper DatabaseConnection save method
            db_conn = DatabaseConnection(custom_config=self.db_config)
            db_conn.connect()
            db_conn.recommendations_table = output_table  # Set the target table
            save_result = db_conn.save_recommendations(recommendations_df)
            db_conn.disconnect()
            
            # 4. Return results
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            rules_count = save_result.get("total_written", len(recommendations_df))
            records_count = df_basket['ORDER_ID'].nunique() if 'ORDER_ID' in df_basket.columns else len(df_basket)
            
            logger.info(f"========== MINING RESULTS ==========")
            logger.info(f"Rules generated: {rules_count}")
            logger.info(f"Records processed: {records_count}")
            logger.info(f"Database save result: {save_result}")
            logger.info(f"====================================")
            
            return {
                "success": True,
                "rules_generated": rules_count,
                "records_processed": records_count,
                "database_stats": save_result,
                "stats": {
                    "total_orders": records_count,
                    "total_rules": rules_count
                },
                "execution_time": duration,
                "output_table": output_table
            }
            
        except Exception as e:
            logger.error(f"Mining failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "rules_generated": 0,
                "records_processed": 0
            }
    
    def _load_order_data(self):
        """Load order data from database for mining"""
        days_back = self.mining_params.get('days_back', 365)
        max_items = self.mining_params.get('max_items', 200)
        
        conn = pymysql.connect(
            host=self.db_config['host'],
            port=self.db_config.get('port', 3306),
            user=self.db_config['user'],
            password=self.db_config['password'],
            database=self.db_config['database'],
            charset='utf8mb4'
        )
        
        try:
            # Get top N SKUs first
            popularity_query = f"""
            SELECT 
                s.SKU_NAME,
                COUNT(DISTINCT o.ORDER_ID) as order_count
            FROM {self.db_config['order_table']} o
            JOIN {self.db_config['sku_master_table']} s ON o.ARTICLE_ID = s.SKU_ID
            WHERE o.INSERTED_TIMESTAMP >= DATE_SUB(CURDATE(), INTERVAL {days_back} DAY)
            AND s.SKU_NAME IS NOT NULL
            GROUP BY s.SKU_NAME
            HAVING order_count >= 5
            ORDER BY order_count DESC
            LIMIT {max_items}
            """
            
            popular_skus_df = pd.read_sql(popularity_query, conn)
            popular_sku_list = popular_skus_df['SKU_NAME'].tolist()
            
            if not popular_sku_list:
                logger.warning("No popular SKUs found")
                conn.close()
                return pd.DataFrame()
            
            logger.info(f"Found {len(popular_sku_list)} popular SKUs")
            
            # Load order data for these SKUs
            placeholders = ','.join(['%s'] * len(popular_sku_list))
            main_query = f"""
            SELECT 
                o.ORDER_ID,
                o.ARTICLE_ID,
                s.SKU_NAME,
                o.INSERTED_TIMESTAMP as order_date,
                DATEDIFF(CURDATE(), DATE(o.INSERTED_TIMESTAMP)) as days_ago
            FROM {self.db_config['order_table']} o
            JOIN {self.db_config['sku_master_table']} s ON o.ARTICLE_ID = s.SKU_ID
            WHERE o.INSERTED_TIMESTAMP >= DATE_SUB(CURDATE(), INTERVAL {days_back} DAY)
            AND s.SKU_NAME IN ({placeholders})
            """
            
            df = pd.read_sql(main_query, conn, params=popular_sku_list)
            conn.close()
            
            logger.info(f"Loaded {len(df)} order records for mining")
            return df
            
        except Exception as e:
            logger.error(f"Error loading order data: {e}")
            conn.close()
            raise
