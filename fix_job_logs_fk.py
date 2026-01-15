#!/usr/bin/env python3
"""
Fix mining_job_logs table to allow schedule_id = 0 for UI/API based mining
"""

import pymysql
from app.shared.config.config import Config

def fix_foreign_key():
    """Drop and recreate mining_job_logs table without foreign key constraint"""
    
    config = Config()
    
    try:
        connection = pymysql.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            port=config.DB_PORT
        )
        
        cursor = connection.cursor()
        
        print("Fixing mining_job_logs table...")
        print("=" * 60)
        
        # Check if table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = %s 
            AND table_name = 'mining_job_logs'
        """, (config.DB_NAME,))
        
        table_exists = cursor.fetchone()[0] > 0
        
        if table_exists:
            # Backup existing data
            print("📦 Backing up existing log data...")
            cursor.execute("SELECT * FROM mining_job_logs")
            existing_logs = cursor.fetchall()
            print(f"   Found {len(existing_logs)} existing log entries")
            
            # Get column names
            cursor.execute("SHOW COLUMNS FROM mining_job_logs")
            columns = [col[0] for col in cursor.fetchall()]
            
            # Drop the table
            print("\n🗑️  Dropping old table with foreign key constraint...")
            cursor.execute("DROP TABLE IF EXISTS mining_job_logs")
            print("   ✓ Table dropped")
        
        # Create table without foreign key constraint
        print("\n📝 Creating new mining_job_logs table (without FK constraint)...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mining_job_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                schedule_id INT NOT NULL DEFAULT 0,
                job_name VARCHAR(255) NOT NULL,
                started_at TIMESTAMP NOT NULL,
                completed_at TIMESTAMP NULL,
                execution_status VARCHAR(20) DEFAULT 'running',
                rules_generated INT DEFAULT 0,
                records_processed INT DEFAULT 0,
                execution_time_seconds INT DEFAULT 0,
                error_message TEXT,
                error_details JSON,
                execution_parameters JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_schedule_id (schedule_id),
                INDEX idx_job_name (job_name),
                INDEX idx_started_at (started_at),
                INDEX idx_status (execution_status),
                INDEX idx_completed_at (completed_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("   ✓ Table created successfully")
        
        # Restore data if any existed
        if table_exists and existing_logs:
            print(f"\n📥 Restoring {len(existing_logs)} log entries...")
            
            # Build insert query based on columns
            placeholders = ', '.join(['%s'] * len(columns))
            insert_query = f"INSERT INTO mining_job_logs ({', '.join(columns)}) VALUES ({placeholders})"
            
            cursor.executemany(insert_query, existing_logs)
            print("   ✓ Data restored successfully")
        
        connection.commit()
        
        # Verify the fix
        print("\n" + "=" * 60)
        print("✅ VERIFICATION")
        print("=" * 60)
        
        cursor.execute("SHOW CREATE TABLE mining_job_logs")
        create_statement = cursor.fetchone()[1]
        
        if 'FOREIGN KEY' in create_statement:
            print("⚠️  WARNING: Foreign key constraint still exists!")
        else:
            print("✓ Foreign key constraint removed successfully")
            print("✓ Table can now accept schedule_id = 0 for UI/API mining")
        
        # Show current row count
        cursor.execute("SELECT COUNT(*) FROM mining_job_logs")
        count = cursor.fetchone()[0]
        print(f"✓ Current log entries: {count}")
        
        print("\n" + "=" * 60)
        print("✅ Fix completed successfully!")
        print("=" * 60)
        print("\nYou can now run UI-based mining jobs and they will be logged properly.")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_foreign_key()
