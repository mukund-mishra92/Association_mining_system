"""
Migration script to add missing columns to mining_schedules table
Run this to update existing mining_schedules table with new columns
"""
import pymysql

# Update these values as needed
DB_CONFIG = {
    'host': '10.102.246.10',
    'port': 6033,
    'user': 'root',
    'password': 'Falcon@123@WCS',
    'database': 'neo',
    'charset': 'utf8mb4'
}

def add_missing_columns():
    """Add missing columns to mining_schedules table"""
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    try:
        print("Checking and adding missing columns to mining_schedules table...")
        
        # Get existing columns
        cursor.execute("DESCRIBE mining_schedules")
        existing_columns = {row[0] for row in cursor.fetchall()}
        print(f"Existing columns: {existing_columns}")
        
        # Define columns to add with their definitions
        columns_to_add = {
            'max_items': 'INT DEFAULT 200',
            'min_item_frequency': 'INT DEFAULT 5',
            'days_back': 'INT DEFAULT 365',
            'use_enhanced_mining': 'BOOLEAN DEFAULT TRUE',
            'time_weighting_method': "VARCHAR(32) DEFAULT 'exponential_decay'",
            'time_segmentation': "VARCHAR(32) DEFAULT 'weekly'"
        }
        
        # Add missing columns
        for column_name, column_def in columns_to_add.items():
            if column_name not in existing_columns:
                alter_sql = f"ALTER TABLE mining_schedules ADD COLUMN {column_name} {column_def}"
                print(f"Adding column: {column_name}")
                cursor.execute(alter_sql)
                connection.commit()
                print(f"✓ Added column: {column_name}")
            else:
                print(f"✓ Column already exists: {column_name}")
        
        print("\n✅ Migration completed successfully!")
        print("\nCurrent mining_schedules schema:")
        cursor.execute("DESCRIBE mining_schedules")
        for row in cursor.fetchall():
            print(f"  {row[0]:30s} {row[1]:20s} {row[2]:5s} {row[3]:5s} {str(row[4]):10s}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    add_missing_columns()
