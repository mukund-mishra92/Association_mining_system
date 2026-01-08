import pymysql

conn = pymysql.connect(
    host='192.168.1.149',
    port=3307,
    user='CBSUSER',
    password='Falcon@2022',
    database='neo'
)

cur = conn.cursor()
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'neo' 
    AND table_name IN ('mining_schedules', 'mining_schedule_stats', 'mining_job_logs')
""")

tables = [t[0] for t in cur.fetchall()]

print("="*60)
print("SCHEDULER TABLES STATUS")
print("="*60)

if tables:
    print("\n✅ SCHEDULER TABLES ALREADY EXIST:")
    for t in tables:
        print(f"  ✓ {t}")
else:
    print("\n❌ NO SCHEDULER TABLES FOUND")

print(f"\nTotal: {len(tables)}/3 tables exist")

if len(tables) < 3:
    print("\n" + "="*60)
    print("ACTION REQUIRED:")
    print("="*60)
    print("\nRun the SQL script to create missing tables:")
    print("  scripts\\create_scheduler_tables.sql")
    print("\nOr execute manually in your MySQL client.")

conn.close()
