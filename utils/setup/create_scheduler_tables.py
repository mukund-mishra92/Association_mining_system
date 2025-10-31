import pymysql
from app.shared.config.config import config

def create_scheduler_tables():
    """Create scheduler tables for association mining automation"""
    try:
        # Connect to database
        conn = pymysql.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )
        cursor = conn.cursor()
        
        # Create mining_schedules table
        print("Creating mining_schedules table...")
        create_schedules_table = """
        CREATE TABLE IF NOT EXISTS mining_schedules (
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
        cursor.execute(create_schedules_table)
        print("✅ mining_schedules table created")
        
        # Create mining_job_logs table
        print("Creating mining_job_logs table...")
        create_logs_table = """
        CREATE TABLE IF NOT EXISTS mining_job_logs (
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
        cursor.execute(create_logs_table)
        print("✅ mining_job_logs table created")
        
        # Create mining_schedule_stats table
        print("Creating mining_schedule_stats table...")
        create_stats_table = """
        CREATE TABLE IF NOT EXISTS mining_schedule_stats (
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
        cursor.execute(create_stats_table)
        print("✅ mining_schedule_stats table created")
        
        # Insert sample schedules
        print("Inserting sample schedules...")
        insert_samples = """
        INSERT INTO mining_schedules (
            job_name, 
            job_description,
            schedule_type, 
            schedule_time, 
            schedule_day_of_week,
            min_support,
            min_confidence,
            min_lift,
            max_recommendations,
            decay_rate,
            is_active
        ) VALUES 
        (
            'Daily Morning Mining',
            'Daily association rule mining at 6:00 AM with balanced parameters',
            'daily',
            '06:00:00',
            NULL,
            0.300,
            0.300,
            1.0,
            10,
            0.050,
            FALSE
        ),
        (
            'Weekly Report Mining',
            'Comprehensive weekly mining every Monday at 9:00 AM',
            'weekly',
            '09:00:00',
            0,
            0.250,
            0.250,
            1.0,
            15,
            0.030,
            FALSE
        )
        """
        cursor.execute(insert_samples)
        print("✅ Sample schedules inserted")
        
        # Commit all changes
        conn.commit()
        print("✅ All scheduler tables created successfully!")
        
        # Close connection
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating scheduler tables: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise

if __name__ == "__main__":
    create_scheduler_tables()