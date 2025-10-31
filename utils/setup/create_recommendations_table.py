#!/usr/bin/env python3
"""
Create the sku_recommendations table if it doesn't exist
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.shared.database.connection import DatabaseConnection
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_recommendations_table():
    """Create the sku_recommendations table"""
    try:
        db = DatabaseConnection()
        
        if not db.connect():
            logger.error("❌ Failed to connect to database")
            return False
            
        logger.info("✅ Database connection successful")
        
        # Create sku_recommendations table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS sku_recommendations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            antecedent_item_id VARCHAR(50) NOT NULL,
            antecedent_name VARCHAR(255) NOT NULL,
            consequent_item_id VARCHAR(50) NOT NULL,
            consequent_name VARCHAR(255) NOT NULL,
            support DECIMAL(10,6) NOT NULL,
            confidence DECIMAL(10,6) NOT NULL,
            lift DECIMAL(10,6) NOT NULL,
            conviction DECIMAL(10,6) DEFAULT NULL,
            composite_score DECIMAL(10,6) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_antecedent (antecedent_item_id),
            INDEX idx_consequent (consequent_item_id),
            INDEX idx_composite_score (composite_score DESC),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        logger.info("Creating sku_recommendations table...")
        db.cursor.execute(create_table_query)
        db.connection.commit()
        
        logger.info("✅ sku_recommendations table created successfully")
        
        # Check if table was created
        db.cursor.execute("SHOW TABLES LIKE 'sku_recommendations'")
        result = db.cursor.fetchone()
        
        if result:
            logger.info("✅ Table verification successful")
            
            # Show table structure
            db.cursor.execute("DESCRIBE sku_recommendations")
            columns = db.cursor.fetchall()
            logger.info("📋 Table structure:")
            for col in columns:
                logger.info(f"   {col[0]} - {col[1]} - {col[2]} - {col[3]}")
        else:
            logger.error("❌ Table creation verification failed")
            
        db.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔧 Creating sku_recommendations table...")
    success = create_recommendations_table()
    if success:
        logger.info("✅ Table creation completed successfully")
    else:
        logger.error("❌ Table creation failed")