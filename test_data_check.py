#!/usr/bin/env python3
"""
Quick test script to check if data is available in the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.shared.database.connection import DatabaseConnection
from app.shared.config.config import config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_data_availability():
    """Test if we can fetch data from the database"""
    try:
        # Create database connection
        db = DatabaseConnection()
        
        logger.info(f"Testing database connection...")
        logger.info(f"Host: {db.db_host}, Database: {db.db_name}")
        logger.info(f"Order table: {db.order_table}")
        logger.info(f"SKU table: {db.sku_master_table}")
        
        if not db.connect():
            logger.error("❌ Failed to connect to database")
            return False
            
        logger.info("✅ Database connection successful")
        
        # Test raw data count
        logger.info("Testing raw data counts...")
        
        # Count total orders
        db.cursor.execute(f"SELECT COUNT(*) FROM {db.order_table}")
        total_orders = db.cursor.fetchone()[0]
        logger.info(f"📊 Total orders in {db.order_table}: {total_orders:,}")
        
        # Count total SKUs
        db.cursor.execute(f"SELECT COUNT(*) FROM {db.sku_master_table}")
        total_skus = db.cursor.fetchone()[0]
        logger.info(f"📊 Total SKUs in {db.sku_master_table}: {total_skus:,}")
        
        # Test recent orders (last 30 days)
        db.cursor.execute(f"""
            SELECT COUNT(*) FROM {db.order_table} 
            WHERE INSERTED_TIMESTAMP >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """)
        recent_orders = db.cursor.fetchone()[0]
        logger.info(f"📊 Orders in last 30 days: {recent_orders:,}")
        
        # Test joined data
        db.cursor.execute(f"""
            SELECT COUNT(*) FROM {db.order_table} o
            JOIN {db.sku_master_table} s ON o.ARTICLE_ID = s.SKU_ID
            WHERE s.SKU_NAME IS NOT NULL
            AND o.INSERTED_TIMESTAMP >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """)
        joined_recent = db.cursor.fetchone()[0]
        logger.info(f"📊 Valid joined records (last 30 days): {joined_recent:,}")
        
        # Test item frequency (current default criteria)
        db.cursor.execute(f"""
            SELECT COUNT(DISTINCT o.ARTICLE_ID) FROM {db.order_table} o
            JOIN {db.sku_master_table} s ON o.ARTICLE_ID = s.SKU_ID
            WHERE s.SKU_NAME IS NOT NULL
            AND o.INSERTED_TIMESTAMP >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY o.ARTICLE_ID
            HAVING COUNT(DISTINCT o.ORDER_ID) >= {config.MIN_ITEM_FREQUENCY}
        """)
        qualifying_items = len(db.cursor.fetchall())
        logger.info(f"📊 Items with >= {config.MIN_ITEM_FREQUENCY} orders: {qualifying_items}")
        
        # Test with lenient criteria
        db.cursor.execute(f"""
            SELECT COUNT(DISTINCT o.ARTICLE_ID) FROM {db.order_table} o
            JOIN {db.sku_master_table} s ON o.ARTICLE_ID = s.SKU_ID
            WHERE s.SKU_NAME IS NOT NULL
            AND o.INSERTED_TIMESTAMP >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY o.ARTICLE_ID
            HAVING COUNT(DISTINCT o.ORDER_ID) >= 1
        """)
        lenient_items = len(db.cursor.fetchall())
        logger.info(f"📊 Items with >= 1 order: {lenient_items}")
        
        # Now test the actual fetch_order_data method
        logger.info("\n🧪 Testing fetch_order_data method...")
        
        # Test with default parameters
        logger.info("Testing with default parameters...")
        df1 = db.fetch_order_data(days_back=30)
        logger.info(f"Result shape: {df1.shape if df1 is not None else 'None'}")
        
        # Test with lenient parameters
        logger.info("Testing with lenient parameters...")
        df2 = db.fetch_order_data(days_back=30, max_items=2000, min_item_frequency=1)
        logger.info(f"Result shape: {df2.shape if df2 is not None else 'None'}")
        
        db.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔍 Starting data availability test...")
    success = test_data_availability()
    if success:
        logger.info("✅ Data test completed successfully")
    else:
        logger.error("❌ Data test failed")