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

def create_tables():
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()

    # 1. mining_schedules
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mining_schedules (
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ''')

    # 2. mining_schedule_stats
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mining_schedule_stats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            schedule_id INT NOT NULL,
            last_run_at TIMESTAMP NULL,
            last_execution_status VARCHAR(20),
            last_rules_generated INT DEFAULT 0,
            last_execution_time_seconds INT DEFAULT 0,
            avg_execution_time_seconds FLOAT DEFAULT 0,
            FOREIGN KEY (schedule_id) REFERENCES mining_schedules(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ''')

    # 3. mining_job_logs
    cursor.execute('''
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ''')

    # 4. sku_recommendations (default mining output table)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sku_recommendations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            main_item VARCHAR(255) NOT NULL,
            recommended_item VARCHAR(255) NOT NULL,
            main_item_name VARCHAR(255),
            recommended_item_name VARCHAR(255),
            confidence FLOAT,
            lift FLOAT,
            support FLOAT,
            composite_score FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_rule (main_item, recommended_item)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ''')

    # 5. article_proximity_score (alternative mining output table)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS article_proximity_score (
            id INT AUTO_INCREMENT PRIMARY KEY,
            parent_article_id VARCHAR(255) NOT NULL,
            child_article_id VARCHAR(255) NOT NULL,
            proximity_score FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_pair (parent_article_id, child_article_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ''')

    connection.commit()
    cursor.close()
    connection.close()
    print("All required tables created successfully.")

if __name__ == "__main__":
    create_tables()
