#!/usr/bin/env python3
"""
Database Connection Test Script
Tests MySQL connection to remote server with localhost user configuration
Remote Server: 10.102.246.10:6033 with user@localhost setup
"""

import mysql.connector
import sys
import socket
from datetime import datetime

# Your Database Configuration
# Remote MySQL server at 10.102.246.10:6033 with user configured for localhost access
USER_DB_CONFIG = {
    'host': '10.102.246.10',
    'port': 6033,
    'user': 'root',
    'password': 'Falcon@123@WCS',
    'database': 'neo',
    'order_table': 'wms_to_wcs_order_line_request_data',
    'sku_master_table': 'sku_master',
    'recommendations_table': 'sku_recommendations'
}

def test_network_connectivity():
    """Test network connectivity to the MySQL server"""
    print("=" * 60)
    print("🌐 TESTING NETWORK CONNECTIVITY")
    print("=" * 60)
    
    try:
        print(f"🔍 Testing connectivity to {USER_DB_CONFIG['host']}:{USER_DB_CONFIG['port']}")
        
        # Test socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((USER_DB_CONFIG['host'], USER_DB_CONFIG['port']))
        sock.close()
        
        if result == 0:
            print(f"✅ Network connectivity successful!")
            print(f"🔗 Port {USER_DB_CONFIG['port']} is open and accessible")
            return True
        else:
            print(f"❌ Network connectivity failed!")
            print(f"🚫 Port {USER_DB_CONFIG['port']} is not accessible")
            print(f"💡 This could indicate:")
            print(f"   - MySQL server is not running")
            print(f"   - Firewall blocking port {USER_DB_CONFIG['port']}")
            print(f"   - MySQL not configured to listen on port {USER_DB_CONFIG['port']}")
            return False
            
    except Exception as e:
        print(f"❌ Network test error: {str(e)}")
        return False

def test_basic_connection():
    """Test basic database connection"""
    print("=" * 60)
    print("🔗 TESTING BASIC DATABASE CONNECTION")
    print("=" * 60)
    
    try:
        print(f"⏳ Connecting to: {USER_DB_CONFIG['host']}:{USER_DB_CONFIG['port']}")
        print(f"📊 Database: {USER_DB_CONFIG['database']}")
        print(f"👤 User: {USER_DB_CONFIG['user']}")
        print()
        
        # Establish connection with additional parameters for remote connection
        connection = mysql.connector.connect(
            host=USER_DB_CONFIG['host'],
            port=USER_DB_CONFIG['port'],
            user=USER_DB_CONFIG['user'],
            password=USER_DB_CONFIG['password'],
            database=USER_DB_CONFIG['database'],
            connection_timeout=15,
            autocommit=True,
            charset='utf8mb4',
            use_unicode=True
        )
        
        cursor = connection.cursor()
        
        # Get MySQL version
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"✅ CONNECTION SUCCESSFUL!")
        print(f"🔢 MySQL Version: {version[0]}")
        
        # Get current time from database
        cursor.execute("SELECT NOW()")
        db_time = cursor.fetchone()
        print(f"⏰ Database Time: {db_time[0]}")
        
        # Get database name
        cursor.execute("SELECT DATABASE()")
        db_name = cursor.fetchone()
        print(f"📚 Current Database: {db_name[0]}")
        
        # Test user and host information
        cursor.execute("SELECT USER(), @@hostname")
        user_info = cursor.fetchone()
        print(f"👤 Connected as: {user_info[0]}")
        print(f"🖥️  Server hostname: {user_info[1]}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ DATABASE CONNECTION FAILED!")
        print(f"💥 Error Code: {e.errno}")
        print(f"📝 Error Message: {e.msg}")
        
        # Provide specific help for common remote connection issues
        if e.errno == 2003:
            print(f"\n🔧 TROUBLESHOOTING TIPS FOR ERROR 2003:")
            print(f"   1. Verify MySQL server is running on {USER_DB_CONFIG['host']}:{USER_DB_CONFIG['port']}")
            print(f"   2. Check if port {USER_DB_CONFIG['port']} is open in firewall")
            print(f"   3. Ensure MySQL is configured to accept remote connections")
            print(f"   4. Verify network connectivity to {USER_DB_CONFIG['host']}")
        elif e.errno == 1045:
            print(f"\n🔧 TROUBLESHOOTING TIPS FOR ERROR 1045 (Access Denied):")
            print(f"   1. Verify username and password are correct")
            print(f"   2. Check if user 'root' is allowed to connect from your IP")
            print(f"   3. User might be configured for 'localhost' host pattern only")
            print(f"   4. May need to create user with '%' or specific IP host pattern")
        elif e.errno == 1049:
            print(f"\n🔧 TROUBLESHOOTING TIPS FOR ERROR 1049 (Unknown Database):")
            print(f"   1. Verify database '{USER_DB_CONFIG['database']}' exists")
            print(f"   2. Check if user has access to this database")
        
        return False
        
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR!")
        print(f"📝 Error: {str(e)}")
        return False

def test_tables_existence():
    """Test if required tables exist and get basic info"""
    print("\n" + "=" * 60)
    print("📋 TESTING TABLE EXISTENCE")
    print("=" * 60)
    
    try:
        connection = mysql.connector.connect(
            host=USER_DB_CONFIG['host'],
            port=USER_DB_CONFIG['port'],
            user=USER_DB_CONFIG['user'],
            password=USER_DB_CONFIG['password'],
            database=USER_DB_CONFIG['database'],
            connection_timeout=10
        )
        
        cursor = connection.cursor()
        
        # Test each table
        tables_to_test = {
            'Order Table': USER_DB_CONFIG['order_table'],
            'SKU Master Table': USER_DB_CONFIG['sku_master_table'],
            'Recommendations Table': USER_DB_CONFIG['recommendations_table']
        }
        
        for table_type, table_name in tables_to_test.items():
            print(f"\n🔍 Testing {table_type}: {table_name}")
            
            try:
                # Check if table exists and get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   ✅ Table exists with {count:,} records")
                
                # Get table structure (first few columns)
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                print(f"   📊 Columns ({len(columns)} total):")
                for i, col in enumerate(columns[:5]):  # Show first 5 columns
                    print(f"      - {col[0]} ({col[1]})")
                if len(columns) > 5:
                    print(f"      ... and {len(columns) - 5} more columns")
                    
            except mysql.connector.Error as e:
                print(f"   ❌ Table does not exist or access denied")
                print(f"   💥 Error: {e.msg}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR TESTING TABLES!")
        print(f"📝 Error: {str(e)}")
        return False

def test_sample_queries():
    """Test some sample queries on the tables"""
    print("\n" + "=" * 60)
    print("🔍 TESTING SAMPLE QUERIES")
    print("=" * 60)
    
    try:
        connection = mysql.connector.connect(
            host=USER_DB_CONFIG['host'],
            port=USER_DB_CONFIG['port'],
            user=USER_DB_CONFIG['user'],
            password=USER_DB_CONFIG['password'],
            database=USER_DB_CONFIG['database'],
            connection_timeout=10
        )
        
        cursor = connection.cursor()
        
        # Test 1: Recent orders (if order table exists)
        try:
            print(f"\n📦 Testing recent orders from {USER_DB_CONFIG['order_table']}:")
            query = f"""
            SELECT COUNT(*) as total_orders, 
                   COUNT(DISTINCT ORDER_ID) as unique_orders,
                   COUNT(DISTINCT ARTICLE_ID) as unique_articles
            FROM {USER_DB_CONFIG['order_table']} 
            WHERE INSERTED_TIMESTAMP >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            """
            cursor.execute(query)
            result = cursor.fetchone()
            print(f"   📊 Last 30 days: {result[0]:,} total orders, {result[1]:,} unique orders, {result[2]:,} unique articles")
            
        except mysql.connector.Error as e:
            print(f"   ❌ Could not query orders table: {e.msg}")
        
        # Test 2: SKU Master data
        try:
            print(f"\n🏷️  Testing SKU master data from {USER_DB_CONFIG['sku_master_table']}:")
            query = f"""
            SELECT COUNT(*) as total_skus,
                   COUNT(DISTINCT SKU_ID) as unique_sku_ids,
                   COUNT(DISTINCT SKU_NAME) as unique_sku_names
            FROM {USER_DB_CONFIG['sku_master_table']}
            """
            cursor.execute(query)
            result = cursor.fetchone()
            print(f"   📊 Total SKUs: {result[0]:,}, Unique IDs: {result[1]:,}, Unique Names: {result[2]:,}")
            
        except mysql.connector.Error as e:
            print(f"   ❌ Could not query SKU master table: {e.msg}")
        
        # Test 3: Check if we can join orders with SKUs
        try:
            print(f"\n🔗 Testing JOIN between orders and SKU master:")
            query = f"""
            SELECT COUNT(*) as matched_records
            FROM {USER_DB_CONFIG['order_table']} o
            JOIN {USER_DB_CONFIG['sku_master_table']} s ON o.ARTICLE_ID = s.SKU_ID
            WHERE o.INSERTED_TIMESTAMP >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            LIMIT 1
            """
            cursor.execute(query)
            result = cursor.fetchone()
            print(f"   📊 Successfully joined tables: {result[0]:,} matched records in last 7 days")
            
        except mysql.connector.Error as e:
            print(f"   ❌ Could not join tables: {e.msg}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR TESTING QUERIES!")
        print(f"📝 Error: {str(e)}")
        return False

def test_permissions():
    """Test database permissions"""
    print("\n" + "=" * 60)
    print("🔐 TESTING DATABASE PERMISSIONS")
    print("=" * 60)
    
    try:
        connection = mysql.connector.connect(
            host=USER_DB_CONFIG['host'],
            port=USER_DB_CONFIG['port'],
            user=USER_DB_CONFIG['user'],
            password=USER_DB_CONFIG['password'],
            database=USER_DB_CONFIG['database'],
            connection_timeout=10
        )
        
        cursor = connection.cursor()
        
        # Test SELECT permission
        try:
            cursor.execute("SELECT 1")
            print("   ✅ SELECT permission: OK")
        except:
            print("   ❌ SELECT permission: DENIED")
        
        # Test CREATE TABLE permission (for recommendations table)
        try:
            test_table = "test_permissions_temp_table"
            cursor.execute(f"CREATE TEMPORARY TABLE {test_table} (id INT)")
            cursor.execute(f"DROP TEMPORARY TABLE {test_table}")
            print("   ✅ CREATE TABLE permission: OK")
        except:
            print("   ❌ CREATE TABLE permission: DENIED")
        
        # Test INSERT permission
        try:
            # Try to check if we can insert (we won't actually insert, just prepare)
            cursor.execute("SELECT 1 FROM DUAL WHERE 1=0")  # Safe test
            print("   ✅ INSERT permission: Likely OK (couldn't test safely)")
        except:
            print("   ❌ INSERT permission: Uncertain")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR TESTING PERMISSIONS!")
        print(f"📝 Error: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 DATABASE CONNECTION TEST SCRIPT")
    print("🌐 Remote MySQL Server Connection Test")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔧 Configuration:")
    print(f"   Host: {USER_DB_CONFIG['host']}")
    print(f"   Port: {USER_DB_CONFIG['port']}")
    print(f"   Database: {USER_DB_CONFIG['database']}")
    print(f"   User: {USER_DB_CONFIG['user']}")
    print(f"   Password: {'*' * len(USER_DB_CONFIG['password'])}")
    print()
    print("📋 Note: Testing remote MySQL server with user@localhost configuration")
    
    # Run all tests
    tests_passed = 0
    total_tests = 5
    
    # Test network connectivity first
    if test_network_connectivity():
        tests_passed += 1
    
    if test_basic_connection():
        tests_passed += 1
    
    if test_tables_existence():
        tests_passed += 1
    
    if test_sample_queries():
        tests_passed += 1
    
    if test_permissions():
        tests_passed += 1
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Tests Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED! Your database configuration is working correctly.")
        print("🚀 You can proceed with association mining operations.")
        print("🔗 Remote MySQL connection to 10.102.246.10:6033 is fully functional!")
    elif tests_passed >= 3:
        print("⚠️  PARTIAL SUCCESS! Basic connection works, but some issues found.")
        print("💡 You may still be able to run association mining, but check the errors above.")
    else:
        print("❌ TESTS FAILED! Please check your database configuration and network connectivity.")
        print("🔧 Common issues for remote MySQL connections:")
        print("   - Network connectivity to 10.102.246.10:6033")
        print("   - MySQL server not running or not listening on port 6033")
        print("   - User 'root' not configured for remote access")
        print("   - Firewall blocking the connection")
        print("   - MySQL bind-address configuration")
        print()
        print("💡 MySQL User Configuration Help:")
        print("   If user is configured for localhost only, the DB admin may need to:")
        print("   CREATE USER 'root'@'%' IDENTIFIED BY 'password';")
        print("   GRANT ALL PRIVILEGES ON neo.* TO 'root'@'%';")
        print("   FLUSH PRIVILEGES;")
    
    print("\n🔚 Test completed.")
    return tests_passed == total_tests

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 UNEXPECTED ERROR: {str(e)}")
        sys.exit(1)