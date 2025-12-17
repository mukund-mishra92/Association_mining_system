"""Discover actual database schema for NEO system"""
from app.shared.database.connection import get_db_connection

def discover_schema():
    """Discover the actual table schemas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tables = [
        'bot_master',
        'task_master', 
        'order_bin_mapping',
        'station_master',
        'pick_wave_master',
        'pick_wave_order_master',
        'put_wave_order_master'
    ]
    
    print("=" * 80)
    print("NEO DATABASE SCHEMA DISCOVERY")
    print("=" * 80)
    
    for table in tables:
        try:
            cursor.execute(f"DESCRIBE {table};")
            columns = cursor.fetchall()
            
            print(f"\n{table.upper()}:")
            print("-" * 80)
            print(f"{'Column Name':<30} {'Type':<20} {'Null':<8} {'Key':<8}")
            print("-" * 80)
            
            for col in columns:
                col_name = col[0]
                col_type = col[1]
                col_null = col[2]
                col_key = col[3]
                print(f"{col_name:<30} {col_type:<20} {col_null:<8} {col_key:<8}")
                
        except Exception as e:
            print(f"\n{table.upper()}: ❌ Table not found or error: {e}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("Schema discovery complete!")
    print("=" * 80)

if __name__ == "__main__":
    discover_schema()
