"""Add max_items and min_item_frequency columns to mining_schedules - FAST VERSION"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.shared.database.connection import DatabaseConnection

db = DatabaseConnection()
db.connect()

print("Checking existing columns...")
db.cursor.execute("SHOW COLUMNS FROM mining_schedules")
existing_columns = [col[0] for col in db.cursor.fetchall()]
print(f"Existing columns: {existing_columns}")

columns_to_add = []

if 'max_items' not in existing_columns:
    columns_to_add.append(('max_items', 'INT DEFAULT 200'))
    
if 'min_item_frequency' not in existing_columns:
    columns_to_add.append(('min_item_frequency', 'INT DEFAULT 5'))

if not columns_to_add:
    print("\n✓ All columns already exist!")
    db.disconnect()
    sys.exit(0)

print(f"\nAdding {len(columns_to_add)} column(s)...")

for col_name, col_def in columns_to_add:
    try:
        print(f"  Adding {col_name}...", end=' ')
        db.cursor.execute(f"ALTER TABLE mining_schedules ADD COLUMN {col_name} {col_def}")
        db.connection.commit()
        print("✓")
    except Exception as e:
        if 'Duplicate column' in str(e):
            print("(already exists)")
        else:
            print(f"ERROR: {e}")
            db.connection.rollback()

db.disconnect()
print("\n✓ Schema update complete!")
