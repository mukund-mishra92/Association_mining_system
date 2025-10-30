#!/usr/bin/env python3
"""
Test script to verify auto-table creation works
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.shared.database.connection import DatabaseConnection
import pandas as pd
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_table_creation():
    """Test auto-table creation"""
    try:
        db = DatabaseConnection()
        
        if not db.connect():
            logger.error("❌ Failed to connect to database")
            return False
            
        logger.info("✅ Database connection successful")
        
        # Check if recommendations table exists
        db.cursor.execute("SHOW TABLES LIKE %s", (db.recommendations_table,))
        table_exists = db.cursor.fetchone() is not None
        logger.info(f"📊 Table {db.recommendations_table} exists: {table_exists}")
        
        # Create a small test DataFrame
        test_data = pd.DataFrame({
            'antecedent_article_ids': ['A123'],
            'consequent_article_ids': ['B456'],
            'confidence': [0.8],
            'lift': [1.5],
            'support': [0.2],
            'composite_score': [0.65]
        })
        
        logger.info("🧪 Testing save_recommendations (this should auto-create table)...")
        success = db.save_recommendations(test_data)
        logger.info(f"Save result: {success}")
        
        # Check if table was created
        db.cursor.execute("SHOW TABLES LIKE %s", (db.recommendations_table,))
        table_exists_after = db.cursor.fetchone() is not None
        logger.info(f"📊 Table {db.recommendations_table} exists after save: {table_exists_after}")
        
        # Check table structure
        if table_exists_after:
            db.cursor.execute(f"DESCRIBE {db.recommendations_table}")
            columns = db.cursor.fetchall()
            logger.info(f"📊 Table structure:")
            for col in columns:
                logger.info(f"  - {col[0]}: {col[1]}")
                
            # Check if data was saved
            db.cursor.execute(f"SELECT COUNT(*) FROM {db.recommendations_table}")
            count = db.cursor.fetchone()[0]
            logger.info(f"📊 Records in table: {count}")
        
        db.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔍 Testing auto-table creation...")
    success = test_table_creation()
    if success:
        logger.info("✅ Table creation test completed")
    else:
        logger.error("❌ Table creation test failed")