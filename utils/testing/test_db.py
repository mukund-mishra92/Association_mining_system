# Test MySQL Connection - Direct Configuration
import pymysql

def test_db_connection():
    """Test connection to remote MySQL server with hardcoded values"""
    
    # Database configuration - HARDCODED
    # Current machine: 10.102.246.2
    # MySQL server: 10.102.246.10
    DB_HOST = "10.102.246.10"
    DB_PORT = 6033
    DB_USER = "appuser"
    DB_PASSWORD = "Falcon@123@WCS"
    DB_NAME = "neo"
    
    print("="*60)
    print("Testing MySQL Connection")
    print("="*60)
    print(f"Host: {DB_HOST}")
    print(f"Port: {DB_PORT}")
    print(f"User: {DB_USER}")
    print(f"Database: {DB_NAME}")
    print(f"DB_PASSWORD: {DB_PASSWORD}")
    print("="*60)
    
    try:
        print("\nAttempting connection...")
        print("Using PyMySQL for better caching_sha2_password support...")
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connect_timeout=10,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"✓ Database connection successful!")
        print(f"✓ MySQL Version: {version[0]}")
        
        # Get current database
        cursor.execute("SELECT DATABASE()")
        db = cursor.fetchone()
        print(f"✓ Connected to database: {db[0]}")
        
        # Get current user
        cursor.execute("SELECT USER()")
        user = cursor.fetchone()
        print(f"✓ Connected as: {user[0]}")
        
        cursor.close()
        conn.close()
        print("\n✓✓✓ Connection test PASSED! ✓✓✓")
            
    except pymysql.MySQLError as err:
        print(f"\n✗ MySQL Error!")
        print(f"Error Code: {err.args[0]}")
        if len(err.args) > 1:
            print(f"Error Message: {err.args[1]}")
        
        if err.args[0] == 1045:
            print("\n[DIAGNOSIS] Access Denied")
            print("  - Wrong password, OR")
            print("  - User doesn't have remote access")
        elif err.args[0] == 2003:
            print("\n[DIAGNOSIS] Can't connect to server")
            print("  - MySQL not running on remote server")
            print("  - Firewall blocking port")
            print("  - Wrong host IP")
            
    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")

# Run the test
test_db_connection()