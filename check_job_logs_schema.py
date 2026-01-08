"""Check mining_job_logs table structure"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.shared.database.connection import DatabaseConnection

db = DatabaseConnection()
db.connect()

print("mining_job_logs table structure:")
db.cursor.execute("DESCRIBE mining_job_logs")
columns = db.cursor.fetchall()
for col in columns:
    print(f"  {col}")

db.disconnect()
