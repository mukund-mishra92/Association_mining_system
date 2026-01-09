#!/usr/bin/env python3
"""
Setup script for scheduler-related database tables.
Creates all necessary tables with primary keys for the mining scheduler system.
"""

import mysql.connector
from app.shared.config.config import Config

def setup_scheduler_tables():
    """Create or recreate all scheduler-related tables"""
    
    config = Config()
    
    try:
        # Connect to database
        connection = mysql.connector.connect(
            host=config.db_host,
            user=config.db_user,
            password=config.db_password,
            database=config.db_name,
            port=config.db_port
        )
        
        cursor = connection.cursor()
        print("✓ Connected to database")
        
        # Table 1: mining_schedules - Main scheduler configuration
        print("\n📋 Creating mining_schedules table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mining_schedules (
                id INT AUTO_INCREMENT PRIMARY KEY,
                job_name VARCHAR(255) NOT NULL UNIQUE,
                job_description TEXT,
                schedule_type ENUM('daily', 'weekly') NOT NULL DEFAULT 'daily',
                schedule_time TIME NOT NULL,
                schedule_day_of_week INT,
                min_support DECIMAL(5,3) DEFAULT 0.300,
                min_confidence DECIMAL(5,3) DEFAULT 0.300,
                min_lift DECIMAL(5,2) DEFAULT 1.00,
                max_recommendations INT DEFAULT 10,
                decay_rate DECIMAL(5,3) DEFAULT 0.050,
                days_back INT DEFAULT 365,
                max_items INT DEFAULT 200,
                min_item_frequency INT DEFAULT 5,
                use_enhanced_mining BOOLEAN DEFAULT TRUE,
                time_weighting_method VARCHAR(50) DEFAULT 'exponential_decay',
                time_segmentation VARCHAR(20) DEFAULT 'weekly',
                output_table VARCHAR(255) DEFAULT 'sku_recommendations',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                last_run_at TIMESTAMP NULL,
                next_run_at TIMESTAMP NULL,
                created_by VARCHAR(100) DEFAULT 'system',
                INDEX idx_job_name (job_name),
                INDEX idx_schedule_type (schedule_type),
                INDEX idx_is_active (is_active),
                INDEX idx_next_run (next_run_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ mining_schedules table created/verified")
        
        # Table 2: mining_schedule_stats - Execution statistics per schedule
        print("\n📊 Creating mining_schedule_stats table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mining_schedule_stats (
                schedule_id INT PRIMARY KEY,
                total_runs INT DEFAULT 0,
                successful_runs INT DEFAULT 0,
                failed_runs INT DEFAULT 0,
                avg_execution_time_seconds DECIMAL(10,2) DEFAULT 0.00,
                last_execution_status VARCHAR(20),
                last_execution_time TIMESTAMP NULL,
                total_rules_generated INT DEFAULT 0,
                last_error_message TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (schedule_id) REFERENCES mining_schedules(id) ON DELETE CASCADE,
                INDEX idx_last_execution (last_execution_time),
                INDEX idx_status (last_execution_status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ mining_schedule_stats table created/verified")
        
        # Table 3: mining_job_logs - Individual job execution logs
        print("\n📝 Creating mining_job_logs table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mining_job_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                schedule_id INT NOT NULL,
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
                FOREIGN KEY (schedule_id) REFERENCES mining_schedules(id) ON DELETE CASCADE,
                INDEX idx_schedule_id (schedule_id),
                INDEX idx_job_name (job_name),
                INDEX idx_started_at (started_at),
                INDEX idx_status (execution_status),
                INDEX idx_completed_at (completed_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ mining_job_logs table created/verified")
        
        connection.commit()
        
        # Display table information
        print("\n" + "="*60)
        print("DATABASE TABLES SUMMARY")
        print("="*60)
        
        tables = [
            ('mining_schedules', 'Main scheduler configuration'),
            ('mining_schedule_stats', 'Execution statistics per schedule'),
            ('mining_job_logs', 'Individual job execution logs')
        ]
        
        for table_name, description in tables:
            cursor.execute(f"SHOW COLUMNS FROM {table_name}")
            columns = cursor.fetchall()
            
            print(f"\n📋 {table_name}")
            print(f"   Description: {description}")
            print(f"   Columns: {len(columns)}")
            
            # Find primary key
            pk_columns = [col[0] for col in columns if 'PRI' in col[3]]
            if pk_columns:
                print(f"   Primary Key: {', '.join(pk_columns)}")
            
            # Count rows
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   Records: {count}")
        
        print("\n" + "="*60)
        print("✅ All scheduler tables are ready!")
        print("="*60)
        
        cursor.close()
        connection.close()
        
    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    print("="*60)
    print("SCHEDULER TABLES SETUP")
    print("="*60)
    print("\nThis script will create/verify the following tables:")
    print("  1. mining_schedules - Schedule configurations")
    print("  2. mining_schedule_stats - Execution statistics")
    print("  3. mining_job_logs - Job execution history")
    print("\nAll tables will have proper primary keys and indexes.")
    print("="*60)
    
    response = input("\nProceed with setup? (yes/no): ").strip().lower()
    if response in ['yes', 'y']:
        setup_scheduler_tables()
    else:
        print("❌ Setup cancelled")
