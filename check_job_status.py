#!/usr/bin/env python3
"""Check status of running mining jobs"""
import pymysql
from app.shared.config.config import config
from datetime import datetime

def check_job_status():
    conn = pymysql.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        port=config.DB_PORT
    )
    cursor = conn.cursor()
    
    # Check running jobs
    print("=== RUNNING/RECENT JOBS ===")
    cursor.execute("""
        SELECT id, schedule_id, job_name, started_at, completed_at, execution_status, error_message, rules_generated, records_processed
        FROM mining_job_logs 
        WHERE started_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        ORDER BY started_at DESC
        LIMIT 10
    """)
    running = cursor.fetchall()
    for row in running:
        print(f"\nID: {row[0]}, Schedule: {row[1]}, Job: {row[2]}")
        print(f"  Started: {row[3]}")
        print(f"  Completed: {row[4]}")
        print(f"  Status: {row[5]}")
        print(f"  Rules: {row[7]}, Records: {row[8]}")
        if row[6]:
            print(f"  Error: {row[6]}")
        
        # Calculate runtime
        if row[3]:
            if row[4]:  # Completed
                runtime = (row[4] - row[3]).total_seconds()
            else:  # Still running
                runtime = (datetime.now() - row[3]).total_seconds()
            print(f"  Runtime: {runtime:.0f} seconds")
    
    # Check if article_proximity_score table exists
    print("\n=== TABLE CHECK ===")
    cursor.execute("SHOW TABLES LIKE 'article_proximity_score'")
    table_exists = cursor.fetchone()
    print(f"article_proximity_score exists: {table_exists is not None}")
    
    if table_exists:
        cursor.execute("DESCRIBE article_proximity_score")
        columns = cursor.fetchall()
        print("  Columns:")
        for col in columns:
            print(f"    - {col[0]} ({col[1]})")
        
        cursor.execute("SELECT COUNT(*) FROM article_proximity_score")
        count = cursor.fetchone()[0]
        print(f"  Row count: {count}")
    
    # Check schedule config
    print("\n=== SCHEDULE CONFIG ===")
    cursor.execute("""
        SELECT id, job_name, output_table, is_active 
        FROM mining_schedules 
        WHERE id = 52
    """)
    schedule = cursor.fetchone()
    if schedule:
        print(f"ID: {schedule[0]}, Name: {schedule[1]}")
        print(f"  Output Table: {schedule[2]}")
        print(f"  Active: {schedule[3]}")
    
    conn.close()

if __name__ == "__main__":
    check_job_status()
