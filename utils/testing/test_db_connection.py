#!/usr/bin/env python3
"""
Quick database connection test using current configuration
"""

import sys
import os
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

def test_database_connection():
    """Test database connection using current config"""
    print("🔧 Testing Database Connection")
    print("=" * 40)
    
    try:
        import pymysql
        from app.shared.config.config import config
        
        print("📋 Configuration loaded:")
        print(f"   Host: {config.DB_HOST}")
        print(f"   Port: {config.DB_PORT}")
        print(f"   User: {config.DB_USER}")
        print(f"   Database: {config.DB_NAME}")
        print(f"   Order Table: {config.ORDER_TABLE}")
        print(f"   SKU Table: {config.SKU_MASTER_TABLE}")
        print()
        
        print("🔌 Attempting connection...")
        connection = pymysql.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Test basic connection
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"✅ Connected successfully!")
        print(f"   MySQL Version: {version[0]}")
        
        # Test if tables exist
        print("\n📊 Checking tables...")
        
        # Check order table
        cursor.execute(f"SHOW TABLES LIKE '{config.ORDER_TABLE}'")
        order_table_exists = cursor.fetchone() is not None
        print(f"   Order Table ({config.ORDER_TABLE}): {'✅ Found' if order_table_exists else '❌ Not Found'}")
        
        # Check SKU table
        cursor.execute(f"SHOW TABLES LIKE '{config.SKU_MASTER_TABLE}'")
        sku_table_exists = cursor.fetchone() is not None
        print(f"   SKU Table ({config.SKU_MASTER_TABLE}): {'✅ Found' if sku_table_exists else '❌ Not Found'}")
        
        if order_table_exists:
            cursor.execute(f"SELECT COUNT(*) FROM {config.ORDER_TABLE}")
            order_count = cursor.fetchone()[0]
            print(f"   Order Records: {order_count:,}")
        
        if sku_table_exists:
            cursor.execute(f"SELECT COUNT(*) FROM {config.SKU_MASTER_TABLE}")
            sku_count = cursor.fetchone()[0]
            print(f"   SKU Records: {sku_count:,}")
        
        connection.close()
        
        if order_table_exists and sku_table_exists:
            print("\n🎉 Database connection and tables are working correctly!")
            return True
        else:
            print("\n⚠️  Database connected but required tables are missing!")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're using the virtual environment")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("   1. Check if MySQL server is running")
        print("   2. Verify credentials in .env file")
        print("   3. Ensure database exists")
        print("   4. Check network connectivity")
        return False

if __name__ == "__main__":
    test_database_connection()