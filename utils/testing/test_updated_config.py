import pymysql

# Test the updated configuration
USER_DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'database': 'neo',
    'order_table': 'wms_to_wcs_order_line_request_data',
    'sku_master_table': 'sku_master',
    'recommendations_table': 'sku_recommendations'
}

print("Testing updated database configuration...")
try:
    conn = pymysql.connect(
        host=USER_DB_CONFIG['host'],
        port=USER_DB_CONFIG['port'],
        user=USER_DB_CONFIG['user'],
        password=USER_DB_CONFIG['password'],
        database=USER_DB_CONFIG['database'],
        charset='utf8mb4'
    )
    
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()
    print(f"SUCCESS: Connected to MySQL {version[0]}")
    
    # Test if tables exist
    print("\nChecking tables...")
    test_tables = {
        'order': USER_DB_CONFIG['order_table'],
        'sku_master': USER_DB_CONFIG['sku_master_table'], 
        'recommendations': USER_DB_CONFIG['recommendations_table']
    }
    
    for table_key, table_name in test_tables.items():
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} LIMIT 1")
            count = cursor.fetchone()[0]
            print(f"✓ Table {table_name}: {count} records")
        except Exception as e:
            print(f"✗ Table {table_name}: Not found - {e}")
    
    cursor.close()
    conn.close()
    print("\nDatabase connection test completed successfully!")
    
except Exception as e:
    print(f"FAILED: {e}")