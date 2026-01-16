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
            schedule_type VARCHAR(20) NOT NULL,
            schedule_time VARCHAR(10) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            min_support FLOAT DEFAULT 0.1,
            min_confidence FLOAT DEFAULT 0.3,
            min_lift FLOAT DEFAULT 1.0,
            max_recommendations INT DEFAULT 10,
            decay_rate FLOAT DEFAULT 0.05,
            output_table VARCHAR(255) DEFAULT 'sku_recommendations',
            max_items INT DEFAULT 200,
            min_item_frequency INT DEFAULT 5,
            days_back INT DEFAULT 365,
            use_enhanced_mining BOOLEAN DEFAULT TRUE,
            time_weighting_method VARCHAR(32) DEFAULT 'exponential_decay',
            time_segmentation VARCHAR(32) DEFAULT 'weekly',
            last_run_at DATETIME DEFAULT NULL,
            next_run_at DATETIME DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    "mining_schedule_stats": """
        CREATE TABLE mining_schedule_stats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            schedule_id INT NOT NULL,
            last_run_at TIMESTAMP NULL,
            last_execution_status VARCHAR(20),
            last_rules_generated INT DEFAULT 0,
            last_execution_time_seconds INT DEFAULT 0,
            avg_execution_time_seconds FLOAT DEFAULT 0,
            FOREIGN KEY (schedule_id) REFERENCES mining_schedules(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    "mining_job_logs": """
        CREATE TABLE mining_job_logs (
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
    print("Connected to DB:", DB_NAME)

    for table, ddl in TABLES.items():
        print(f"\nFlushing table: {table}")
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"  - Dropped {table}")
        except Exception as e:
            print(f"  - Error dropping {table}: {e}")

        try:
            cursor.execute(ddl)
            print(f"  - Created {table}")
        except Exception as e:
            print(f"  - Error creating {table}: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print("\n✅ All mining-related tables flushed and recreated.")

if __name__ == "__main__":
    flush_and_recreate_tables()