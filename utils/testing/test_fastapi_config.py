"""Test FastAPI database configuration"""
import sys
sys.path.append('.')

from app.shared.config.config import config
from app.shared.database.connection import DatabaseConnection

print("="*60)
print("Testing FastAPI Database Configuration")
print("="*60)
print(f"DB_HOST: {config.DB_HOST}")
print(f"DB_PORT: {config.DB_PORT}")
print(f"DB_USER: {config.DB_USER}")
print(f"DB_NAME: {config.DB_NAME}")
print("="*60)

print("\nTesting DatabaseConnection...")
db = DatabaseConnection()
print(f"Connection host: {db.db_host}")
print(f"Connection port: {db.db_port}")
print(f"Connection user: {db.db_user}")
print(f"Connection database: {db.db_name}")
print("="*60)

print("\nAttempting connection...")
if db.connect():
    print("✓ Connection successful!")
    db.disconnect()
else:
    print("✗ Connection failed - check logs above")
