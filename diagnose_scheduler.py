"""
Diagnostic script to identify why scheduler is offline
"""
import os
import sys
import pymysql
from dotenv import load_dotenv

print("=" * 60)
print("SCHEDULER DIAGNOSTICS")
print("=" * 60)

# 1. Check .env file
print("\n1. Checking .env file...")
load_dotenv()
required_vars = ['DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
missing = []
for var in required_vars:
    value = os.getenv(var)
    if value:
        if 'PASSWORD' in var:
            print(f"   ✓ {var}=***")
        else:
            print(f"   ✓ {var}={value}")
    else:
        print(f"   ✗ {var} is MISSING")
        missing.append(var)

if missing:
    print(f"\n❌ ERROR: Missing environment variables: {', '.join(missing)}")
    sys.exit(1)

# 2. Check database connection
print("\n2. Testing database connection...")
try:
    conn = pymysql.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        connect_timeout=5
    )
    print(f"   ✓ Connected to {os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}")
    cursor = conn.cursor()
    
    # 3. Check required tables
    print("\n3. Checking required tables...")
    required_tables = ['mining_schedules', 'mining_schedule_stats', 'mining_job_logs', 
                      'sku_recommendations', 'article_proximity_score']
    
    cursor.execute("SHOW TABLES")
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    missing_tables = []
    for table in required_tables:
        if table in existing_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   ✓ {table} exists ({count} rows)")
        else:
            print(f"   ✗ {table} MISSING")
            missing_tables.append(table)
    
    if missing_tables:
        print(f"\n❌ ERROR: Missing tables: {', '.join(missing_tables)}")
        print("\n   FIX: Run 'python reset_mining_tables.py' to create tables")
        sys.exit(1)
    
    # 4. Check mining_schedules schema
    print("\n4. Checking mining_schedules schema...")
    cursor.execute("DESCRIBE mining_schedules")
    columns = [row[0] for row in cursor.fetchall()]
    required_columns = ['id', 'job_name', 'schedule_type', 'schedule_time', 
                       'is_active', 'next_run_at', 'last_run_at']
    
    missing_cols = [col for col in required_columns if col not in columns]
    if missing_cols:
        print(f"   ✗ Missing columns: {', '.join(missing_cols)}")
        print("\n   FIX: Run 'python reset_mining_tables.py' to fix schema")
        sys.exit(1)
    else:
        print(f"   ✓ All required columns exist")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ ALL CHECKS PASSED - Scheduler should work!")
    print("=" * 60)
    print("\nIf scheduler is still offline, check:")
    print("  1. Port 8080 is not in use (netstat -ano | findstr :8080)")
    print("  2. Python packages installed (pip install -r requirements.txt)")
    print("  3. Check logs in terminal when running quick_start.py")
    
except pymysql.Error as e:
    print(f"\n❌ DATABASE ERROR: {e}")
    print("\nPossible causes:")
    print("  - Database server not running")
    print("  - Wrong credentials in .env")
    print("  - Firewall blocking MySQL port")
    print("  - Database does not exist")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ UNEXPECTED ERROR: {e}")
    sys.exit(1)
