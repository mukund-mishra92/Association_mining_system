import pymysql

print("Testing localhost:3306...")
try:
    conn = pymysql.connect(
        host='localhost', 
        port=3306, 
        user='root', 
        password='', 
        database='neo', 
        connect_timeout=5
    )
    print("localhost:3306 - SUCCESS")
    conn.close()
except Exception as e:
    print(f"localhost:3306 - FAILED: {e}")

print("\nTesting localhost:3306 with password 'root'...")
try:
    conn = pymysql.connect(
        host='localhost', 
        port=3306, 
        user='root', 
        password='root', 
        database='neo', 
        connect_timeout=5
    )
    print("localhost:3306 (password='root') - SUCCESS")
    conn.close()
except Exception as e:
    print(f"localhost:3306 (password='root') - FAILED: {e}")

print("\nTesting remote MySQL 10.102.246.10:6033...")
try:
    conn = pymysql.connect(
        host='10.102.246.10', 
        port=6033, 
        user='root', 
        password='Falcon@123@WCS', 
        database='neo', 
        connect_timeout=5
    )
    print("10.102.246.10:6033 - SUCCESS")
    conn.close()
except Exception as e:
    print(f"10.102.246.10:6033 - FAILED: {e}")