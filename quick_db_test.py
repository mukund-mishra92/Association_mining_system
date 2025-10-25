#!/usr/bin/env python3
"""
Quick Database Connection Test
Simple script to quickly test remote MySQL connection
Remote Server: 10.102.246.10:6033 with user@localhost setup
"""

import mysql.connector
import sys
import socket

# Your Database Configuration
# Remote MySQL server at 10.102.246.10:6033 with user configured for localhost access
DB_CONFIG = {
    'host': '10.102.246.10',
    'port': 6033,
    'user': 'root',
    'password': 'Falcon@123@WCS',
    'database': 'neo'
}

def quick_test():
    """Quick connection test"""
    print("🔗 Testing Remote MySQL Connection...")
    print(f"📍 Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"📊 Database: {DB_CONFIG['database']}")
    print(f"👤 User: {DB_CONFIG['user']}")
    print("🌐 Remote server with user@localhost configuration")
    print()
    
    # First test network connectivity
    print("⏳ Step 1: Testing network connectivity...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((DB_CONFIG['host'], DB_CONFIG['port']))
        sock.close()
        
        if result == 0:
            print("✅ Network connectivity successful!")
        else:
            print("❌ Network connectivity failed!")
            print(f"🚫 Cannot reach {DB_CONFIG['host']}:{DB_CONFIG['port']}")
            return False
    except Exception as e:
        print(f"❌ Network test error: {e}")
        return False
    
    # Test MySQL connection
    print("⏳ Step 2: Testing MySQL connection...")
    try:
        # Test connection with enhanced parameters for remote connection
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            connection_timeout=10,
            autocommit=True,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Get basic info
        cursor.execute("SELECT VERSION(), NOW(), DATABASE(), USER(), @@hostname")
        result = cursor.fetchone()
        
        print("✅ CONNECTION SUCCESSFUL!")
        print(f"🔢 MySQL Version: {result[0]}")
        print(f"⏰ Server Time: {result[1]}")
        print(f"📚 Database: {result[2]}")
        print(f"👤 Connected as: {result[3]}")
        print(f"🖥️  Server hostname: {result[4]}")
        
        # Quick table check
        tables = ['wms_to_wcs_order_line_request_data', 'sku_master', 'sku_recommendations']
        print(f"\n📋 Checking tables:")
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   ✅ {table}: {count:,} rows")
            except mysql.connector.Error as e:
                print(f"   ❌ {table}: Not accessible ({e.msg})")
        
        cursor.close()
        connection.close()
        
        print(f"\n🎉 Remote MySQL connection test completed successfully!")
        print(f"🚀 Ready for association mining operations!")
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ CONNECTION FAILED!")
        print(f"Error Code: {e.errno}")
        print(f"Error: {e.msg}")
        
        # Provide specific help
        if e.errno == 1045:
            print(f"\n💡 Access Denied - This usually means:")
            print(f"   - User 'root' might be configured for localhost access only")
            print(f"   - Password might be incorrect")
            print(f"   - User might not have permission to access database 'neo'")
        elif e.errno == 2003:
            print(f"\n💡 Connection Failed - This usually means:")
            print(f"   - MySQL server not running on {DB_CONFIG['host']}:{DB_CONFIG['port']}")
            print(f"   - Firewall blocking port {DB_CONFIG['port']}")
            print(f"   - MySQL not configured to listen on port {DB_CONFIG['port']}")
        
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)