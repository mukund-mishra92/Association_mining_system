#!/usr/bin/env python3
"""
Rule Count Validation Script - Standalone Version
Investigates discrepancy between UI displayed rules and database saved rules
"""

import pymysql
import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def get_db_config():
    """Get database configuration from .env file"""
    config = {
        'DB_HOST': 'localhost',
        'DB_PORT': 3306,
        'DB_USER': 'root',
        'DB_PASSWORD': '',
        'DB_NAME': 'neo'
    }
    
    # Try to read from .env file
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    if key in config:
                        # Remove quotes if present
                        value = value.strip('"\'')
                        if key == 'DB_PORT':
                            config[key] = int(value)
                        else:
                            config[key] = value
    
    return config

def validate_rule_counts():
    """Validate and analyze rule count discrepancies"""
    
    print("🔍 RULE COUNT VALIDATION ANALYSIS")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get database config
    config = get_db_config()
    print(f"🔧 Database Config: {config['DB_HOST']}:{config['DB_PORT']}/{config['DB_NAME']}")
    
    # Database connection
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
        return
    
    print("\n📊 DATABASE ANALYSIS:")
    print("-" * 40)
    
    # Check all recommendation tables
    cursor.execute("SHOW TABLES LIKE '%recommendation%'")
    tables = cursor.fetchall()
    
    total_db_rules = 0
    table_details = {}
    
    for table in tables:
        table_name = table[0]
        
        # Get count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        total_db_rules += count
        table_details[table_name] = count
        
        print(f"📋 {table_name}: {count} rules")
        
        # Get table structure
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        print(f"   Columns: {[col[0] for col in columns]}")
        
        # Sample some records to check structure
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 2")
            samples = cursor.fetchall()
            for i, sample in enumerate(samples):
                print(f"   Sample {i+1}: {sample}")
    
    print(f"\n📊 TOTAL DATABASE RULES: {total_db_rules}")
    
    # Focus on the main recommendation table
    main_table = None
    max_count = 0
    for table, count in table_details.items():
        if count > max_count:
            max_count = count
            main_table = table
    
    if main_table:
        print(f"\n🎯 ANALYZING MAIN TABLE: {main_table} ({max_count} rules)")
        print("-" * 50)
        
        # Check for duplicates
        try:
            cursor.execute(f"""
                SELECT PARENT_ARTICLE_ID, CHILD_ARTICLE_ID, COUNT(*) as duplicate_count
                FROM {main_table}
                GROUP BY PARENT_ARTICLE_ID, CHILD_ARTICLE_ID
                HAVING COUNT(*) > 1
                ORDER BY duplicate_count DESC
                LIMIT 10
            """)
            duplicates = cursor.fetchall()
            if duplicates:
                print(f"⚠️  DUPLICATES FOUND: {len(duplicates)} duplicate pairs")
                for dup in duplicates[:5]:
                    print(f"   {dup[0]} -> {dup[1]}: {dup[2]} copies")
            else:
                print("✅ NO DUPLICATES FOUND")
        except Exception as e:
            print(f"❌ Could not check duplicates: {e}")
        
        # Analyze score distribution
        try:
            cursor.execute(f"""
                SELECT 
                    MIN(PROXIMITY_SCORE) as min_score,
                    MAX(PROXIMITY_SCORE) as max_score,
                    AVG(PROXIMITY_SCORE) as avg_score,
                    COUNT(*) as total_count,
                    COUNT(DISTINCT PARENT_ARTICLE_ID) as unique_parents,
                    COUNT(DISTINCT CHILD_ARTICLE_ID) as unique_children
                FROM {main_table}
            """)
            stats = cursor.fetchone()
            if stats:
                print(f"\n📊 SCORE STATISTICS:")
                print(f"   Min Score: {stats[0]}")
                print(f"   Max Score: {stats[1]}")
                print(f"   Avg Score: {stats[2]:.3f}")
                print(f"   Total Rules: {stats[3]}")
                print(f"   Unique Parent SKUs: {stats[4]}")
                print(f"   Unique Child SKUs: {stats[5]}")
                
                # Calculate potential maximum combinations
                if stats[4] and stats[5]:
                    max_possible = stats[4] * stats[5]
                    print(f"   Max Possible Combinations: {max_possible}")
                    print(f"   Actual vs Max: {stats[3]}/{max_possible} ({stats[3]/max_possible*100:.1f}%)")
        except Exception as e:
            print(f"❌ Could not analyze scores: {e}")
        
        # Check score distribution
        try:
            cursor.execute(f"""
                SELECT 
                    CASE 
                        WHEN PROXIMITY_SCORE >= 0.8 THEN '0.8-1.0'
                        WHEN PROXIMITY_SCORE >= 0.6 THEN '0.6-0.8'
                        WHEN PROXIMITY_SCORE >= 0.4 THEN '0.4-0.6'
                        WHEN PROXIMITY_SCORE >= 0.2 THEN '0.2-0.4'
                        ELSE '0.0-0.2'
                    END as score_range,
                    COUNT(*) as count
                FROM {main_table}
                GROUP BY 
                    CASE 
                        WHEN PROXIMITY_SCORE >= 0.8 THEN '0.8-1.0'
                        WHEN PROXIMITY_SCORE >= 0.6 THEN '0.6-0.8'
                        WHEN PROXIMITY_SCORE >= 0.4 THEN '0.4-0.6'
                        WHEN PROXIMITY_SCORE >= 0.2 THEN '0.2-0.4'
                        ELSE '0.0-0.2'
                    END
                ORDER BY score_range
            """)
            distribution = cursor.fetchall()
            if distribution:
                print(f"\n📊 SCORE DISTRIBUTION:")
                for range_name, count in distribution:
                    print(f"   {range_name}: {count} rules")
        except Exception as e:
            print(f"⚠️  Could not analyze score distribution: {e}")
    
    # Check for any mining job logs
    print("\n🔍 MINING JOB ANALYSIS:")
    print("-" * 30)
    try:
        cursor.execute("SHOW TABLES LIKE '%job%'")
        job_tables = cursor.fetchall()
        if job_tables:
            for table in job_tables:
                table_name = table[0]
                print(f"📋 Found job table: {table_name}")
                
                # Try to get recent jobs
                cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 3")
                jobs = cursor.fetchall()
                for job in jobs:
                    print(f"   Recent job: {job}")
        else:
            print("❌ No job tables found")
    except Exception as e:
        print(f"⚠️  Could not check job logs: {e}")
    
    connection.close()
    
    print("\n" + "=" * 60)
    print("🎯 DISCREPANCY ANALYSIS:")
    print("=" * 60)
    print(f"📊 UI Reported: 575 rules")
    print(f"💾 Database Saved: {total_db_rules} rules")
    print(f"🔍 Missing Rules: {575 - total_db_rules} rules ({(575 - total_db_rules)/575*100:.1f}%)")
    
    print("\n🔍 LIKELY CAUSES:")
    print("-" * 20)
    if 575 - total_db_rules == 286:  # Exactly half
        print("1. 🎯 TOP N FILTERING: System may save only top 289 rules")
    else:
        print("1. 🎯 SCORE THRESHOLD: Rules below certain score filtered out")
    
    print("2. 🔄 DEDUPLICATION: UI counts raw generation, DB removes duplicates")
    print("3. 📊 INSERTION LIMITS: Database constraints limiting saves")
    print("4. 🐛 INSERTION ERRORS: Some rules failed to insert")
    print("5. 🎭 COUNTING DIFFERENCE: UI vs DB counting logic differs")
    
    print("\n🔧 RECOMMENDATIONS:")
    print("-" * 20)
    print("1. Add logging to track rules before/after DB insertion")
    print("2. Check mining algorithm for any built-in filtering")
    print("3. Review database insertion code for limits or filters")
    print("4. Verify UI counting mechanism accuracy")

if __name__ == "__main__":
    validate_rule_counts()
    print("\n📋 VALIDATION COMPLETE")
    print("Run this script after each mining operation to track the discrepancy pattern.")