"""
Migration script to update mining_schedules table schema
from old format (name, cron_expression) to new format (job_name, schedule_type, schedule_time)
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

db_config = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

print("=" * 80)
print("MINING SCHEDULER TABLE MIGRATION")
print("=" * 80)
print(f"\nConnecting to: {db_config['host']}:{db_config['port']} as {db_config['user']}")

try:
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    
    # Backup old table if it exists
    print("\n[1/6] Backing up old mining_schedules table...")
    cursor.execute("SHOW TABLES LIKE 'mining_schedules'")
    if cursor.fetchone():
        cursor.execute("DROP TABLE IF EXISTS mining_schedules_backup")
        cursor.execute("CREATE TABLE mining_schedules_backup AS SELECT * FROM mining_schedules")
        cursor.execute("SELECT COUNT(*) FROM mining_schedules_backup")
        backup_count = cursor.fetchone()[0]
        print(f"      ✓ Backed up {backup_count} records to mining_schedules_backup")
    else:
        print("      - No existing table to backup")
    
    # Drop dependent tables first (due to foreign keys)
    print("\n[2/6] Dropping old scheduler tables...")
    cursor.execute("DROP TABLE IF EXISTS mining_schedule_stats")
    print("      ✓ Dropped mining_schedule_stats")
    cursor.execute("DROP TABLE IF EXISTS mining_schedule_history")
    print("      ✓ Dropped mining_schedule_history (if existed)")
    cursor.execute("DROP TABLE IF EXISTS mining_job_logs")
    print("      ✓ Dropped mining_job_logs (if existed)")
    cursor.execute("DROP TABLE IF EXISTS mining_schedules")
    print("      ✓ Dropped mining_schedules")
    
    # Create new mining_schedules table
    print("\n[3/6] Creating new mining_schedules table...")
    create_schedules_sql = """
    CREATE TABLE mining_schedules (
        id INT AUTO_INCREMENT PRIMARY KEY,
        job_name VARCHAR(255) NOT NULL,
        job_description TEXT,
        schedule_type ENUM('daily', 'weekly') NOT NULL,
        schedule_time TIME NOT NULL,
        schedule_day_of_week INT(1) NULL,
        
        min_support DECIMAL(4,3) DEFAULT 0.300,
        min_confidence DECIMAL(4,3) DEFAULT 0.300,
        min_lift DECIMAL(4,2) DEFAULT 1.00,
        max_recommendations INT DEFAULT 10,
        decay_rate DECIMAL(4,3) DEFAULT 0.050,
        
        output_table VARCHAR(255) DEFAULT 'sku_recommendations',
        is_active BOOLEAN DEFAULT TRUE,
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        last_run_at TIMESTAMP NULL,
        next_run_at TIMESTAMP NULL,
        
        created_by VARCHAR(255) DEFAULT 'system',
        
        INDEX idx_schedule_type (schedule_type),
        INDEX idx_is_active (is_active),
        INDEX idx_next_run (next_run_at),
        UNIQUE KEY unique_job_name (job_name)
    )
    """
    cursor.execute(create_schedules_sql)
    print("      ✓ Created mining_schedules table")
    
    # Create mining_job_logs table
    print("\n[4/6] Creating mining_job_logs table...")
    create_logs_sql = """
    CREATE TABLE mining_job_logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        schedule_id INT NOT NULL,
        job_name VARCHAR(255) NOT NULL,
        
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP NULL,
        execution_status ENUM('running', 'success', 'failed', 'cancelled') DEFAULT 'running',
        
        rules_generated INT DEFAULT 0,
        records_processed INT DEFAULT 0,
        execution_time_seconds INT DEFAULT 0,
        
        error_message TEXT NULL,
        error_details JSON NULL,
        execution_parameters JSON NULL,
        
        INDEX idx_schedule_id (schedule_id),
        INDEX idx_execution_status (execution_status),
        INDEX idx_started_at (started_at),
        FOREIGN KEY (schedule_id) REFERENCES mining_schedules(id) ON DELETE CASCADE
    )
    """
    cursor.execute(create_logs_sql)
    print("      ✓ Created mining_job_logs table")
    
    # Create mining_schedule_stats table
    print("\n[5/6] Creating mining_schedule_stats table...")
    create_stats_sql = """
    CREATE TABLE mining_schedule_stats (
        schedule_id INT PRIMARY KEY,
        total_executions INT DEFAULT 0,
        successful_executions INT DEFAULT 0,
        failed_executions INT DEFAULT 0,
        last_success_at TIMESTAMP NULL,
        last_failure_at TIMESTAMP NULL,
        avg_execution_time_seconds DECIMAL(10,2) DEFAULT 0,
        total_rules_generated INT DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        
        FOREIGN KEY (schedule_id) REFERENCES mining_schedules(id) ON DELETE CASCADE
    )
    """
    cursor.execute(create_stats_sql)
    print("      ✓ Created mining_schedule_stats table")
    
    # Insert example schedules
    print("\n[6/6] Inserting example schedules...")
    insert_sql = """
    INSERT INTO mining_schedules (
        job_name, job_description, schedule_type, schedule_time, schedule_day_of_week,
        min_support, min_confidence, min_lift, max_recommendations, decay_rate, is_active
    ) VALUES 
    ('Daily Morning Mining', 'Daily association rule mining at 6:00 AM', 'daily', '06:00:00', NULL,
     0.050, 0.250, 1.0, 10, 0.050, FALSE),
    ('Weekly Report Mining', 'Weekly mining every Monday at 9:00 AM', 'weekly', '09:00:00', 0,
     0.050, 0.250, 1.0, 15, 0.030, FALSE)
    """
    cursor.execute(insert_sql)
    
    # Initialize stats for example schedules
    cursor.execute("INSERT INTO mining_schedule_stats (schedule_id) VALUES (1), (2)")
    
    conn.commit()
    print("      ✓ Inserted 2 example schedules (INACTIVE)")
    
    # Verify
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    cursor.execute("SELECT COUNT(*) FROM mining_schedules")
    count = cursor.fetchone()[0]
    print(f"✓ mining_schedules: {count} records")
    
    cursor.execute("SELECT COUNT(*) FROM mining_schedule_stats")
    count = cursor.fetchone()[0]
    print(f"✓ mining_schedule_stats: {count} records")
    
    cursor.execute("SELECT COUNT(*) FROM mining_job_logs")
    count = cursor.fetchone()[0]
    print(f"✓ mining_job_logs: {count} records")
    
    # Show schedules
    print("\nExisting schedules:")
    cursor.execute("""
        SELECT id, job_name, schedule_type, schedule_time, is_active 
        FROM mining_schedules
    """)
    for sched in cursor.fetchall():
        status = "ACTIVE" if sched[4] else "INACTIVE"
        print(f"  [{status}] ID:{sched[0]} - {sched[1]} ({sched[2]} at {sched[3]})")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✓✓✓ MIGRATION COMPLETED SUCCESSFULLY! ✓✓✓")
    print("=" * 80)
    print("\nYou can now:")
    print("  1. Use the scheduler API to create new schedules")
    print("  2. Activate/deactivate schedules via the UI")
    print("  3. View schedule execution history")
    print("\nNOTE: Example schedules are INACTIVE. Activate them via API or create new ones.")
    
except Exception as e:
    print(f"\n❌ Migration failed: {e}")
    import traceback
    traceback.print_exc()
    if 'conn' in locals():
        conn.rollback()
