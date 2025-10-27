"""Check sku_master table and join"""
import sys
sys.path.append('.')

from app.database.connection import DatabaseConnection
import pandas as pd

print("="*60)
print("Checking SKU Master Table and Join")
print("="*60)

db = DatabaseConnection()
if not db.connect():
    print("Failed to connect")
    exit(1)

try:
    cursor = db.cursor
    
    # Check sku_master structure
    print("\n1. SKU Master Table Structure:")
    cursor.execute("DESCRIBE sku_master")
    for col in cursor.fetchall():
        print(f"   {col[0]} ({col[1]})")
    
    # Count SKUs
    cursor.execute("SELECT COUNT(*) FROM sku_master")
    sku_count = cursor.fetchone()[0]
    print(f"\n2. Total SKUs in master: {sku_count}")
    
    # Sample SKUs
    print("\n3. Sample SKUs:")
    cursor.execute("SELECT * FROM sku_master LIMIT 3")
    cols = [desc[0] for desc in cursor.description]
    print(f"   Columns: {cols}")
    for row in cursor.fetchall():
        print(f"   {row}")
    
    # Check join result
    print("\n4. Testing Join (last 30 days):")
    query = """
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT o.ORDER_ID) as unique_orders,
        COUNT(DISTINCT o.ARTICLE_ID) as unique_articles,
        COUNT(DISTINCT s.SKU_NAME) as unique_sku_names
    FROM wms_to_wcs_order_line_request_data o
    JOIN sku_master s ON o.ARTICLE_ID = s.SKU_ID
    WHERE o.INSERTED_TIMESTAMP >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    AND s.SKU_NAME IS NOT NULL
    """
    
    df = pd.read_sql(query, db.connection)
    print(f"   Total joined rows: {df['total_rows'][0]}")
    print(f"   Unique orders: {df['unique_orders'][0]}")
    print(f"   Unique articles: {df['unique_articles'][0]}")
    print(f"   Unique SKU names: {df['unique_sku_names'][0]}")
    
    # Sample joined data
    print("\n5. Sample Joined Data:")
    sample_query = """
    SELECT 
        o.ORDER_ID,
        o.ARTICLE_ID,
        s.SKU_NAME,
        o.INSERTED_TIMESTAMP
    FROM wms_to_wcs_order_line_request_data o
    JOIN sku_master s ON o.ARTICLE_ID = s.SKU_ID
    WHERE o.INSERTED_TIMESTAMP >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    AND s.SKU_NAME IS NOT NULL
    LIMIT 5
    """
    sample_df = pd.read_sql(sample_query, db.connection)
    print(sample_df.to_string())
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.disconnect()

print("\n" + "="*60)
