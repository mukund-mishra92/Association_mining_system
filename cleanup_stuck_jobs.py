"""Clean up stuck jobs"""
import pymysql

conn = pymysql.connect(host='localhost', port=3306, user='root', password='root', database='neo')
c = conn.cursor()
c.execute("UPDATE mining_job_logs SET execution_status='failed', error_message='Cleaned up before restart', completed_at=NOW() WHERE execution_status='running'")
conn.commit()
print(f"✅ Cleaned up {c.rowcount} stuck jobs")
conn.close()
