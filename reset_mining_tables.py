import os
import pymysql
from dotenv import load_dotenv

# Load .env config
load_dotenv()
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_NAME = os.getenv("DB_NAME", "neo")

TABLES = {
    "mining_schedules": """
        CREATE TABLE mining_schedules (
            id INT AUTO_INCREMENT PRIMARY KEY,
            job_name VARCHAR(255) NOT NULL,
            job_description TEXT,
            schedule_type ENUM('daily', 'weekly') NOT NULL,
            schedule_time TIME NOT NULL,
            schedule_day_of_week INT DEFAULT NULL,
            min_support DECIMAL(4,3) DEFAULT 0.100,
            min_confidence DECIMAL(4,3) DEFAULT 0.300,
            min_lift DECIMAL(4,2) DEFAULT 1.00,
            max_recommendations INT DEFAULT 10,
            decay_rate DECIMAL(4,3) DEFAULT 0.050,
            output_table VARCHAR(255) DEFAULT 'sku_recommendations',
            is_active TINYINT(1) DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            last_run_at TIMESTAMP NULL DEFAULT NULL,
            next_run_at TIMESTAMP NULL DEFAULT NULL,
            created_by VARCHAR(255) DEFAULT 'system',
            max_items INT DEFAULT 200,
            min_item_frequency INT DEFAULT 5,
            days_back INT DEFAULT 365,
            use_enhanced_mining TINYINT(1) DEFAULT 1,
            time_weighting_method VARCHAR(50) DEFAULT 'exponential_decay',
            time_segmentation VARCHAR(20) DEFAULT 'weekly',
            INDEX idx_job_name (job_name),
            INDEX idx_is_active (is_active),
            INDEX idx_next_run_at (next_run_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    "mining_schedule_stats": """
        CREATE TABLE mining_schedule_stats (
            schedule_id INT NOT NULL PRIMARY KEY,
            total_executions INT DEFAULT 0,
            successful_executions INT DEFAULT 0,
            failed_executions INT DEFAULT 0,
            last_success_at TIMESTAMP NULL DEFAULT NULL,
            last_failure_at TIMESTAMP NULL DEFAULT NULL,
            avg_execution_time_seconds DECIMAL(10,2) DEFAULT 0.00,
            total_rules_generated INT DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (schedule_id) REFERENCES mining_schedules(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    "mining_job_logs": """
        CREATE TABLE mining_job_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            schedule_id INT NOT NULL,
            job_name VARCHAR(255) NOT NULL,
            started_at TIMESTAMP NULL DEFAULT NULL,
            completed_at TIMESTAMP NULL DEFAULT NULL,
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    "sku_recommendations": """
        CREATE TABLE sku_recommendations (
            SCORE_ID BIGINT AUTO_INCREMENT PRIMARY KEY,
            PARENT_ARTICLE_ID VARCHAR(200),
            CHILD_ARTICLE_ID VARCHAR(200)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    "article_proximity_score": """
        CREATE TABLE article_proximity_score (
            SCORE_ID BIGINT AUTO_INCREMENT PRIMARY KEY,
            PARENT_ARTICLE_ID VARCHAR(200) NOT NULL,
            CHILD_ARTICLE_ID VARCHAR(200) NOT NULL,
            PROXIMITY_SCORE DECIMAL(10,3)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """
}

def flush_and_recreate_tables():
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4"
    )
    cursor = conn.cursor()
    print("=" * 60)
    print(f"Connected to DB: {DB_NAME} at {DB_HOST}:{DB_PORT}")
    print("=" * 60)

    # Drop tables in correct order (child tables first due to foreign keys)
    drop_order = ["mining_job_logs", "mining_schedule_stats", "mining_schedules", 
                  "sku_recommendations", "article_proximity_score"]
    
    print("\n[STEP 1] Dropping existing tables...")
    for table in drop_order:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"  ✓ Dropped {table}")
        except Exception as e:
            print(f"  ✗ Error dropping {table}: {e}")
    
    conn.commit()
    
    # Create tables in correct order (parent tables first)
    create_order = ["mining_schedules", "mining_schedule_stats", "mining_job_logs",
                    "sku_recommendations", "article_proximity_score"]
    
    print("\n[STEP 2] Creating tables...")
    for table in create_order:
        if table in TABLES:
            try:
                cursor.execute(TABLES[table])
                print(f"  ✓ Created {table}")
                
                # Verify creation
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                print(f"     - {len(columns)} columns defined")
            except Exception as e:
                print(f"  ✗ Error creating {table}: {e}")
                print(f"     SQL: {TABLES[table][:100]}...")
    
    conn.commit()
    
    # Verify all tables
    print("\n[STEP 3] Verifying tables...")
    cursor.execute("SHOW TABLES")
    existing = [row[0] for row in cursor.fetchall()]
    
    for table in create_order:
        if table in existing:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  ✓ {table} exists ({count} rows)")
        else:
            print(f"  ✗ {table} MISSING")

    conn.commit()
    cursor.close()
    conn.close()
    print("\n✅ All mining-related tables flushed and recreated.")

if __name__ == "__main__":
    flush_and_recreate_tables()