"""Add max_items and min_item_frequency columns to mining_schedules table"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.shared.database.connection import DatabaseConnection

db = DatabaseConnection()
db.connect()

print("Adding max_items and min_item_frequency columns...")

try:
    # Add max_items column
    db.cursor.execute("""
        ALTER TABLE mining_schedules 
        ADD COLUMN max_items INT DEFAULT 200 
        COMMENT 'Maximum number of top SKUs to analyze'
    """)
    print("✓ Added max_items column")
except Exception as e:
    if "Duplicate column name" in str(e):
        print("  max_items column already exists")
    else:
        print(f"  Error adding max_items: {e}")

try:
    # Add min_item_frequency column
    db.cursor.execute("""
        ALTER TABLE mining_schedules 
        ADD COLUMN min_item_frequency INT DEFAULT 5 
        COMMENT 'Minimum SKU frequency threshold'
    """)
    print("✓ Added min_item_frequency column")
except Exception as e:
    if "Duplicate column name" in str(e):
        print("  min_item_frequency column already exists")
    else:
        print(f"  Error adding min_item_frequency: {e}")

db.connection.commit()
db.disconnect()

print("\nDone! Schema updated successfully.")
