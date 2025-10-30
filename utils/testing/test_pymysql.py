import pymysql
import socket

# Configuration
DB_HOST = "10.102.246.10"
DB_PORT = 6033
DB_USER = "root"
DB_PASSWORD = "Falcon@123@WCS"
DB_NAME = "neo"

print("="*60)
print("TESTING MYSQL WITH PYMYSQL")
print("="*60)
print(f"Host: {DB_HOST}")
print(f"Port: {DB_PORT}")
print(f"User: {DB_USER}")
print(f"Database: {DB_NAME}")
print("="*60)

try:
    print("\nAttempting connection with PyMySQL...")
    print("(PyMySQL handles caching_sha2_password better)")
    
    connection = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        connect_timeout=15,
        charset='utf8mb4'
    )
    
    print("\n✓✓✓ CONNECTION SUCCESSFUL! ✓✓✓")
    
    with connection.cursor() as cursor:
        # Test queries
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"✓ MySQL Version: {version[0]}")
        
        cursor.execute("SELECT DATABASE()")
        db = cursor.fetchone()
        print(f"✓ Database: {db[0]}")
        
        cursor.execute("SELECT USER()")
        user = cursor.fetchone()
        print(f"✓ Connected as: {user[0]}")
        
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"✓ Tables in database: {len(tables)}")
        if tables:
            print("  Tables:")
            for table in tables[:5]:  # Show first 5 tables
                print(f"    - {table[0]}")
    
    connection.close()
    print("\n✓✓✓ TEST PASSED! ✓✓✓")
    print("\nYou can now use PyMySQL in your application!")
    
except pymysql.MySQLError as e:
    print(f"\n✗ MySQL Error!")
    print(f"Error Code: {e.args[0]}")
    print(f"Error Message: {e.args[1]}")
    
except socket.timeout:
    print("\n✗ Connection timeout!")
    print("The connection attempt took too long.")
    
except Exception as e:
    print(f"\n✗ Unexpected Error: {type(e).__name__}")
    print(f"Message: {e}")

print("\n" + "="*60)
