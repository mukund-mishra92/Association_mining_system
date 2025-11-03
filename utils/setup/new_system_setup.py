#!/usr/bin/env python3
"""
New System Database Setup Script
Run this on a NEW SYSTEM after pulling code from GitHub
Creates all required database tables for scheduling functionality
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

def setup_new_system_database():
    """Complete database setup for new system"""
    
    print("🚀 NEW SYSTEM DATABASE SETUP")
    print("=" * 50)
    print("This script will create ALL required tables for scheduling")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    config = get_db_config()
    print(f"🔧 Target Database: {config['DB_HOST']}:{config['DB_PORT']}/{config['DB_NAME']}")
    
    # First check if database exists
    try:
        connection = pymysql.connect(
            host=config['DB_HOST'],
            port=config['DB_PORT'],
            user=config['DB_USER'],
            password=config['DB_PASSWORD'],
            charset='utf8mb4'
        )
        cursor = connection.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['DB_NAME']}")
        cursor.execute(f"USE {config['DB_NAME']}")
        print(f"✅ Database '{config['DB_NAME']}' ready")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Make sure MySQL server is running")
        print("2. Check your .env file configuration")
        print("3. Verify MySQL credentials")
        return False
    
    # Create all required tables
    tables_to_create = {
        'mining_schedules': '''
            CREATE TABLE IF NOT EXISTS mining_schedules (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
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
            CREATE TABLE IF NOT EXISTS mining_schedule_stats (
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
                INDEX idx_schedule_id (schedule_id)
            )
        ''',
        'mining_job_logs': '''
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
                INDEX idx_status (execution_status),
                INDEX idx_started_at (started_at)
            )
        ''',
        'my_recommendation': '''
            CREATE TABLE IF NOT EXISTS my_recommendation (
                SCORE_ID BIGINT NOT NULL AUTO_INCREMENT,
                PARENT_ARTICLE_ID VARCHAR(200) NOT NULL,
                CHILD_ARTICLE_ID VARCHAR(200) NOT NULL,
                PROXIMITY_SCORE DECIMAL(10,3) NULL,
                PRIMARY KEY (PARENT_ARTICLE_ID, CHILD_ARTICLE_ID),
                KEY SCORE_ID_INDEX (SCORE_ID)
            )
        ''',
        'sku_recommendations': '''
            CREATE TABLE IF NOT EXISTS sku_recommendations (
                SCORE_ID BIGINT NOT NULL AUTO_INCREMENT,
                PARENT_ARTICLE_ID VARCHAR(200) NOT NULL,
                CHILD_ARTICLE_ID VARCHAR(200) NOT NULL,
                PROXIMITY_SCORE DECIMAL(10,3) NULL,
                PRIMARY KEY (PARENT_ARTICLE_ID, CHILD_ARTICLE_ID),
                KEY SCORE_ID_INDEX (SCORE_ID)
            )
        '''
    }
    
    print(f"\n🔧 CREATING REQUIRED TABLES:")
    print("-" * 30)
    
    tables_created = 0
    for table_name, create_sql in tables_to_create.items():
        try:
            print(f"📝 Creating {table_name}...")
            cursor.execute(create_sql)
            tables_created += 1
            print(f"✅ {table_name} - SUCCESS")
        except Exception as e:
            print(f"❌ {table_name} - FAILED: {e}")
    
    connection.commit()
    
    # Verify tables were created
    print(f"\n🔍 VERIFYING CREATED TABLES:")
    print("-" * 30)
    
    cursor.execute("SHOW TABLES")
    existing_tables = [table[0] for table in cursor.fetchall()]
    
    all_required_exist = True
    for table_name in tables_to_create.keys():
        if table_name in existing_tables:
            print(f"✅ {table_name} - EXISTS")
        else:
            print(f"❌ {table_name} - MISSING")
            all_required_exist = False
    
    # Test basic functionality
    if all_required_exist:
        print(f"\n🧪 TESTING SCHEDULER FUNCTIONALITY:")
        print("-" * 35)
        
        try:
            # Test basic insert/delete
            test_sql = """
                INSERT INTO mining_schedules 
                (name, cron_expression, is_active) 
                VALUES ('Test Schedule', '0 9 * * *', FALSE)
            """
            cursor.execute(test_sql)
            test_id = cursor.lastrowid
            
            cursor.execute("DELETE FROM mining_schedules WHERE id = %s", (test_id,))
            connection.commit()
            
            print("✅ Scheduler functionality - WORKING")
            
        except Exception as e:
            print(f"❌ Scheduler test failed: {e}")
            all_required_exist = False
    
    connection.close()
    
    print(f"\n" + "=" * 50)
    if all_required_exist:
        print("🎉 NEW SYSTEM SETUP COMPLETE!")
        print("=" * 50)
        print("✅ Database created and configured")
        print("✅ All required tables created")
        print("✅ Scheduler functionality verified")
        print()
        print("🚀 YOUR SYSTEM IS NOW READY:")
        print("   ✅ You can create schedules")
        print("   ✅ You can save schedule configurations")
        print("   ✅ You can run mining operations")
        print()
        print("📋 NEXT STEPS:")
        print("   1. Start your application: start_system.bat")
        print("   2. Access web interface: http://localhost:5000")
        print("   3. Create your first schedule!")
        
        return True
    else:
        print("❌ SETUP FAILED!")
        print("=" * 50)
        print("Some tables could not be created.")
        print("Please check the errors above and try again.")
        return False

if __name__ == "__main__":
    print("🔧 ASSOCIATION MINING SYSTEM - NEW SYSTEM SETUP")
    print("This script prepares the database for a fresh installation")
    print()
    
    if setup_new_system_database():
        print(f"\n✅ SUCCESS! Your new system is ready to use.")
    else:
        print(f"\n❌ FAILED! Please fix the errors and run again.")