"""Check table structure"""
import sys
sys.path.append('.')

from app.database.connection import DatabaseConnection

print("="*60)
print("Checking Table Structure")
print("="*60)

db = DatabaseConnection()
if not db.connect():
    print("Failed to connect to database")
    exit(1)

print("✓ Connected to database\n")

# Check table structure
try:
    cursor = db.cursor
    
    print("Columns in wms_to_wcs_order_line_request_data:")
    cursor.execute("DESCRIBE wms_to_wcs_order_line_request_data")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  - {col[0]} ({col[1]})")
    
    print("\nSample data:")
    cursor.execute("SELECT * FROM wms_to_wcs_order_line_request_data LIMIT 3")
    rows = cursor.fetchall()
    
    # Get column names
    cursor.execute("SELECT * FROM wms_to_wcs_order_line_request_data LIMIT 0")
    col_names = [desc[0] for desc in cursor.description]
    
    print(f"\nColumn names: {col_names}")
    print(f"\nFirst 3 rows:")
    for row in rows:
        print(row)
    
except Exception as e:
    print(f"Error: {e}")
finally:
    db.disconnect()

print("\n" + "="*60)
