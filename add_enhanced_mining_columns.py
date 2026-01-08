"""
Add remaining schedule parameters to mining_schedules table
"""
import pymysql
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.shared.config.config import Config

# Database configuration from config
DB_CONFIG = {
    'host': Config.DB_HOST,
    'port': Config.DB_PORT,
    'user': Config.DB_USER,
    'password': Config.DB_PASSWORD,
    'database': Config.DB_NAME,
    'charset': 'utf8mb4'
}

def add_columns():
    """Add use_enhanced_mining, time_weighting_method, time_segmentation columns"""
    try:
        print("Connecting to database...")
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Check existing columns
        cursor.execute("SHOW COLUMNS FROM mining_schedules")
        existing_columns = {row[0] for row in cursor.fetchall()}
        print(f"Existing columns: {existing_columns}")
        
        columns_to_add = [
            ("use_enhanced_mining", "BOOLEAN DEFAULT 1 COMMENT 'Use enhanced mining with time weighting'"),
            ("time_weighting_method", "VARCHAR(50) DEFAULT 'exponential_decay' COMMENT 'Time weighting method: exponential_decay, linear_decay, seasonal_patterns, etc.'"),
            ("time_segmentation", "VARCHAR(20) DEFAULT 'weekly' COMMENT 'Time segmentation: weekly, monthly, daily'")
        ]
        
        for col_name, col_def in columns_to_add:
            if col_name not in existing_columns:
                print(f"\nAdding column: {col_name}")
                alter_query = f"ALTER TABLE mining_schedules ADD COLUMN {col_name} {col_def}"
                cursor.execute(alter_query)
                connection.commit()
                print(f"✅ Added {col_name} column")
            else:
                print(f"⚠️ Column {col_name} already exists, skipping")
        
        # Verify
        cursor.execute("SHOW COLUMNS FROM mining_schedules")
        all_columns = [row[0] for row in cursor.fetchall()]
        print(f"\n✅ All columns in mining_schedules: {all_columns}")
        
        cursor.close()
        connection.close()
        print("\n✅ Database schema update complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    add_columns()
