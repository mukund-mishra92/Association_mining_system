#!/usr/bin/env python3
"""
Test script to check historical data range
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.shared.database.connection import DatabaseConnection
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_historical_data():
    """Test historical data availability"""
    try:
        db = DatabaseConnection()
        
        if not db.connect():
            logger.error("❌ Failed to connect to database")
            return False
            
        logger.info("✅ Database connection successful")
        
        # Check date range of data
        db.cursor.execute(f"""
            SELECT 
                MIN(DATE(INSERTED_TIMESTAMP)) as earliest_date,
                MAX(DATE(INSERTED_TIMESTAMP)) as latest_date,
                COUNT(*) as total_records
            FROM {db.order_table}
        """)
        result = db.cursor.fetchone()
        earliest, latest, total = result
        
        logger.info(f"📅 Data range: {earliest} to {latest}")
        logger.info(f"📊 Total records: {total:,}")
        
        # Check records in different time periods
        periods = [30, 90, 180, 365, 730, None]  # None = all data
        
        for period in periods:
            if period is None:
                condition = ""
                period_name = "ALL DATA"
            else:
                condition = f"WHERE o.INSERTED_TIMESTAMP >= DATE_SUB(CURDATE(), INTERVAL {period} DAY)"
                period_name = f"Last {period} days"
                
            db.cursor.execute(f"""
                SELECT COUNT(*) FROM {db.order_table} o
                JOIN {db.sku_master_table} s ON o.ARTICLE_ID = s.SKU_ID
                {condition}
                AND s.SKU_NAME IS NOT NULL
            """)
            count = db.cursor.fetchone()[0]
            logger.info(f"📊 {period_name}: {count:,} valid records")
        
        # Test actual data fetch with no date restriction
        logger.info("\n🧪 Testing fetch_order_data with no date restriction...")
        df = db.fetch_order_data(days_back=None, max_items=1000, min_item_frequency=2)
        logger.info(f"Result shape: {df.shape if df is not None else 'None'}")
        
        if df is not None and not df.empty:
            logger.info(f"📊 Unique orders: {df['ORDER_ID'].nunique()}")
            logger.info(f"📊 Unique items: {df['ARTICLE_ID'].nunique()}")
            logger.info(f"📊 Date range in fetched data: {df['INSERTED_TIMESTAMP'].min()} to {df['INSERTED_TIMESTAMP'].max()}")
        
        db.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔍 Starting historical data test...")
    success = test_historical_data()
    if success:
        logger.info("✅ Historical data test completed")
    else:
        logger.error("❌ Historical data test failed")