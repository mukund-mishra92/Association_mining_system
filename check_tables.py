import pymysql

conn = pymysql.connect(
    host='192.168.1.149',
    port=3307,
    user='CBSUSER',
    password='Falcon@2022',
    database='neo'
)

cur = conn.cursor()

# Check all mining tables
cur.execute("SHOW TABLES LIKE 'mining%'")
mining_tables = cur.fetchall()

# Check SKU recommendations table
cur.execute("SHOW TABLES LIKE 'sku_recommendations'")
sku_tables = cur.fetchall()

# Check performance metrics
cur.execute("SHOW TABLES LIKE 'performance_metrics'")
perf_tables = cur.fetchall()

all_tables = mining_tables + sku_tables + perf_tables

print("All relevant tables in database:")
print("="*80)
if all_tables:
    for t in all_tables:
        table_name = t[0]
        print(f"\n📋 Table: {table_name}")
        print("-"*80)
        
        # Show create table
        cur.execute(f"SHOW CREATE TABLE {table_name}")
        create_stmt = cur.fetchone()[1]
        
        # Check for PRIMARY KEY
        if 'PRIMARY KEY' in create_stmt:
            print("✅ HAS PRIMARY KEY")
        else:
            print("❌ MISSING PRIMARY KEY!")
            
        print(f"\n{create_stmt}\n")
else:
    print("  No tables found")

conn.close()
