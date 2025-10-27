"""Quick diagnostic to check data availability"""
import sys
sys.path.append('.')

from app.database.connection import DatabaseConnection
import pandas as pd

print("="*60)
print("Checking Data Availability for Mining")
print("="*60)

db = DatabaseConnection()
if not db.connect():
    print("Failed to connect to database")
    exit(1)

print("✓ Connected to database\n")

# Check order data
print("Checking order data...")
try:
    query = f"""
    SELECT COUNT(*) as total_orders,
           COUNT(DISTINCT ORDER_ID) as unique_orders,
           COUNT(DISTINCT SKU_ID) as unique_skus,
           MIN(INSERTED_TIMESTAMP) as earliest_order,
           MAX(INSERTED_TIMESTAMP) as latest_order
    FROM wms_to_wcs_order_line_request_data
    WHERE INSERTED_TIMESTAMP >= DATE_SUB(NOW(), INTERVAL 90 DAY)
    """
    
    df = pd.read_sql(query, db.connection)
    print(f"Total order lines (last 90 days): {df['total_orders'][0]}")
    print(f"Unique orders: {df['unique_orders'][0]}")
    print(f"Unique SKUs: {df['unique_skus'][0]}")
    print(f"Date range: {df['earliest_order'][0]} to {df['latest_order'][0]}")
    
    # Check sample orders
    print("\nChecking order structure...")
    sample_query = f"""
    SELECT ORDER_ID, SKU_ID, SKU_NAME, INSERTED_TIMESTAMP
    FROM wms_to_wcs_order_line_request_data
    WHERE INSERTED_TIMESTAMP >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    LIMIT 10
    """
    sample_df = pd.read_sql(sample_query, db.connection)
    print(f"\nSample orders:\n{sample_df}")
    
    # Check for NULL values
    print("\nChecking for NULL values in key columns...")
    null_query = f"""
    SELECT 
        SUM(CASE WHEN ORDER_ID IS NULL THEN 1 ELSE 0 END) as null_orders,
        SUM(CASE WHEN SKU_ID IS NULL THEN 1 ELSE 0 END) as null_sku_id,
        SUM(CASE WHEN SKU_NAME IS NULL THEN 1 ELSE 0 END) as null_sku_name
    FROM wms_to_wcs_order_line_request_data
    WHERE INSERTED_TIMESTAMP >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    """
    null_df = pd.read_sql(null_query, db.connection)
    print(f"NULL ORDER_IDs: {null_df['null_orders'][0]}")
    print(f"NULL SKU_IDs: {null_df['null_sku_id'][0]}")
    print(f"NULL SKU_NAMEs: {null_df['null_sku_name'][0]}")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    db.disconnect()

print("\n" + "="*60)
print("Diagnostic Complete")
print("="*60)
