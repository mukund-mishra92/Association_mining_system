#!/usr/bin/env python3
"""
Check if recommendations table exists and contains data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.shared.database.connection import DatabaseConnection
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_recommendations_table():
    """Check if recommendations table exists and has data"""
    try:
        db = DatabaseConnection()
        
        if not db.connect():
            logger.error("❌ Failed to connect to database")
            return False
            
        logger.info("✅ Database connection successful")
        
        # Check if table exists
        db.cursor.execute("SHOW TABLES LIKE %s", (db.recommendations_table,))
        table_exists = db.cursor.fetchone() is not None
        logger.info(f"📊 Table '{db.recommendations_table}' exists: {table_exists}")
        
        if table_exists:
            # Check table structure
            db.cursor.execute(f"DESCRIBE {db.recommendations_table}")
            columns = db.cursor.fetchall()
            logger.info(f"📊 Table structure:")
            for col in columns:
                logger.info(f"  - {col[0]}: {col[1]}")
                
            # Check record count
            db.cursor.execute(f"SELECT COUNT(*) FROM {db.recommendations_table}")
            count = db.cursor.fetchone()[0]
            logger.info(f"📊 Total records in table: {count}")
            
            if count > 0:
                # Show sample records
                db.cursor.execute(f"""
                    SELECT PARENT_ARTICLE_ID, CHILD_ARTICLE_ID, PROXIMITY_SCORE 
                    FROM {db.recommendations_table} 
                    ORDER BY PROXIMITY_SCORE DESC 
                    LIMIT 10
                """)
                records = db.cursor.fetchall()
                logger.info(f"📊 Top 10 recommendations:")
                for i, (parent, child, score) in enumerate(records, 1):
                    logger.info(f"  {i}. {parent} → {child} (score: {score})")
                    
                # Check when data was last updated
                db.cursor.execute(f"SELECT MAX(SCORE_ID) FROM {db.recommendations_table}")
                max_id = db.cursor.fetchone()[0]
                logger.info(f"📊 Latest record ID: {max_id}")
                
        else:
            logger.warning(f"⚠️ Table '{db.recommendations_table}' does not exist")
            
            # Check what tables do exist
            db.cursor.execute("SHOW TABLES")
            tables = [row[0] for row in db.cursor.fetchall()]
            logger.info(f"📊 Available tables: {tables}")
        
        db.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔍 Checking recommendations table...")
    success = check_recommendations_table()
    if success:
        logger.info("✅ Table check completed")
    else:
        logger.error("❌ Table check failed")