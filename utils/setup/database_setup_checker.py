#!/usr/bin/env python3
"""
Database Setup Checker for New Systems
Verifies all required tables exist and creates missing ones
"""

import pymysql
import os
import sys
from datetime import datetime

def get_db_config():
    """Get database configuration from .env file"""
    config = {
        'DB_HOST': 'localhost',
        'DB_PORT': 3306,
        'DB_USER': 'root',
        'DB_PASSWORD': '',
        'DB_NAME': 'neo'
    }
    
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    if key in config:
                        value = value.strip('"\'')
                        if key == 'DB_PORT':
                            config[key] = int(value)
                        else:
                            config[key] = value
    
    return config

def check_and_create_tables():
    """Check for required tables and create missing ones"""
    
    print("🔍 DATABASE SETUP CHECKER FOR NEW SYSTEMS")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    config = get_db_config()
    print(f"🔧 Database: {config['DB_HOST']}:{config['DB_PORT']}/{config['DB_NAME']}")
    
    try:
        connection = pymysql.connect(
            host=config['DB_HOST'],
            port=config['DB_PORT'],
            user=config['DB_USER'],
            password=config['DB_PASSWORD'],
            database=config['DB_NAME'],
            charset='utf8mb4'
        )
        cursor = connection.cursor()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Required tables for the system
    required_tables = {
        'mining_schedules': '''
            CREATE TABLE mining_schedules (
                id INT AUTO_INCREMENT PRIMARY KEY,
                schedule_name VARCHAR(255) NOT NULL,
                cron_expression VARCHAR(100) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                min_support DECIMAL(3,2) DEFAULT 0.30,
                min_confidence DECIMAL(3,2) DEFAULT 0.30,
                min_lift DECIMAL(3,2) DEFAULT 1.00,
                max_recommendations INT DEFAULT 10,
                decay_rate DECIMAL(3,2) DEFAULT 0.05,
                days_back INT DEFAULT 30
            )
        ''',
        'mining_schedule_stats': '''
            CREATE TABLE mining_schedule_stats (
                id INT AUTO_INCREMENT PRIMARY KEY,
                schedule_id INT NOT NULL,
                total_runs INT DEFAULT 0,
                successful_runs INT DEFAULT 0,
                failed_runs INT DEFAULT 0,
                last_run_at TIMESTAMP NULL,
                next_run_at TIMESTAMP NULL,
                average_execution_time DECIMAL(10,2) DEFAULT 0,
                last_error_message TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (schedule_id) REFERENCES mining_schedules(id) ON DELETE CASCADE
            )
        ''',
        'mining_job_logs': '''
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
                FOREIGN KEY (schedule_id) REFERENCES mining_schedules(id) ON DELETE CASCADE
            )
        ''',
        'my_recommendation': '''
            CREATE TABLE my_recommendation (
                SCORE_ID BIGINT NOT NULL AUTO_INCREMENT,
                PARENT_ARTICLE_ID VARCHAR(200) NOT NULL,
                CHILD_ARTICLE_ID VARCHAR(200) NOT NULL,
                PROXIMITY_SCORE DECIMAL(10,3) NULL,
                PRIMARY KEY (PARENT_ARTICLE_ID, CHILD_ARTICLE_ID),
                KEY SCORE_ID_INDEX (SCORE_ID)
            )
        ''',
        'sku_recommendations': '''
            CREATE TABLE sku_recommendations (
                SCORE_ID BIGINT NOT NULL AUTO_INCREMENT,
                PARENT_ARTICLE_ID VARCHAR(200) NOT NULL,
                CHILD_ARTICLE_ID VARCHAR(200) NOT NULL,
                PROXIMITY_SCORE DECIMAL(10,3) NULL,
                PRIMARY KEY (PARENT_ARTICLE_ID, CHILD_ARTICLE_ID),
                KEY SCORE_ID_INDEX (SCORE_ID)
            )
        '''
    }
    
    print("\n🔍 CHECKING REQUIRED TABLES:")
    print("-" * 40)
    
    # Get existing tables
    cursor.execute("SHOW TABLES")
    existing_tables = {table[0] for table in cursor.fetchall()}
    
    missing_tables = []
    for table_name in required_tables:
        if table_name in existing_tables:
            print(f"✅ {table_name} - EXISTS")
        else:
            print(f"❌ {table_name} - MISSING")
            missing_tables.append(table_name)
    
    if missing_tables:
        print(f"\n🔧 CREATING MISSING TABLES:")
        print("-" * 30)
        
        for table_name in missing_tables:
            try:
                print(f"📝 Creating {table_name}...")
                cursor.execute(required_tables[table_name])
                print(f"✅ {table_name} created successfully")
            except Exception as e:
                print(f"❌ Failed to create {table_name}: {e}")
                return False
        
        connection.commit()
        print(f"\n✅ All missing tables created successfully!")
    else:
        print(f"\n✅ ALL REQUIRED TABLES EXIST!")
    
    # Verify scheduler functionality
    print(f"\n🔍 TESTING SCHEDULER FUNCTIONALITY:")
    print("-" * 35)
    
    try:
        # Test inserting a sample schedule
        test_schedule = """
            INSERT INTO mining_schedules 
            (schedule_name, cron_expression, is_active, min_support, min_confidence)
            VALUES ('Test Schedule', '0 9 * * *', FALSE, 0.30, 0.30)
        """
        cursor.execute(test_schedule)
        schedule_id = cursor.lastrowid
        
        # Test inserting stats record
        test_stats = """
            INSERT INTO mining_schedule_stats (schedule_id)
            VALUES (%s)
        """
        cursor.execute(test_stats, (schedule_id,))
        
        # Clean up test data
        cursor.execute("DELETE FROM mining_schedule_stats WHERE schedule_id = %s", (schedule_id,))
        cursor.execute("DELETE FROM mining_schedules WHERE id = %s", (schedule_id,))
        
        connection.commit()
        print("✅ Scheduler functionality test PASSED")
        
    except Exception as e:
        print(f"❌ Scheduler functionality test FAILED: {e}")
        return False
    
    connection.close()
    
    print(f"\n" + "=" * 60)
    print("🎉 DATABASE SETUP COMPLETE!")
    print("=" * 60)
    print("✅ All required tables exist")
    print("✅ Scheduler functionality verified")
    print("✅ System ready for scheduling operations")
    print()
    print("🚀 You can now:")
    print("   - Create new schedules")
    print("   - Save schedule configurations")
    print("   - Run scheduled mining jobs")
    
    return True

if __name__ == "__main__":
    if check_and_create_tables():
        print(f"\n✅ SUCCESS: Database is properly set up for scheduling!")
    else:
        print(f"\n❌ FAILED: Please check the errors above and fix them.")