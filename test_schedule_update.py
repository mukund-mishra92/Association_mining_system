"""
Test script to manually trigger schedule execution and verify next_run_at updates
"""
import sys
import pymysql
from datetime import datetime, timedelta
from app.shared.config.config import Config

def calculate_next_run(schedule_type, schedule_time, day_of_week=None):
    """Calculate next run time"""
    now = datetime.now()
    time_parts = schedule_time.split(':')
    hour = int(time_parts[0])
    minute = int(time_parts[1])
    
    if schedule_type == 'daily':
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
    elif schedule_type == 'weekly':
        if day_of_week is None:
            day_of_week = 0
        days_ahead = day_of_week - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_run = (now + timedelta(days=days_ahead)).replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )
    else:
        raise ValueError(f"Unsupported schedule type: {schedule_type}")
    
    return next_run


def show_schedule_status(conn, schedule_id):
    """Display current schedule status"""
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute(
        """
        SELECT id, job_name, schedule_type, schedule_time, schedule_day_of_week,
               is_active, next_run_at, last_run_at
        FROM mining_schedules
        WHERE id = %s
        """,
        (schedule_id,)
    )
    schedule = cursor.fetchone()
    cursor.close()
    
    if not schedule:
        print(f"❌ Schedule {schedule_id} not found")
        return None
    
    print(f"\n{'='*70}")
    print(f"Schedule: {schedule['job_name']} (ID: {schedule['id']})")
    print(f"{'='*70}")
    print(f"Type: {schedule['schedule_type']}")
    print(f"Time: {schedule['schedule_time']}")
    if schedule['schedule_day_of_week'] is not None:
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        print(f"Day of Week: {days[schedule['schedule_day_of_week']]}")
    print(f"Active: {schedule['is_active']}")
    print(f"Last Run: {schedule['last_run_at']}")
    print(f"Next Run: {schedule['next_run_at']}")
    print(f"{'='*70}\n")
    
    return schedule


def simulate_job_execution(conn, schedule_id):
    """Simulate a job execution and update next_run_at"""
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # Get schedule details
    cursor.execute(
        """
        SELECT schedule_type, schedule_time, schedule_day_of_week
        FROM mining_schedules
        WHERE id = %s
        """,
        (schedule_id,)
    )
    schedule = cursor.fetchone()
    
    if not schedule:
        print(f"❌ Schedule {schedule_id} not found")
        cursor.close()
        return False
    
    # Calculate next run time
    next_run = calculate_next_run(
        schedule['schedule_type'],
        schedule['schedule_time'],
        schedule['schedule_day_of_week']
    )
    
    # Update last_run_at and next_run_at
    now = datetime.now()
    cursor.execute(
        """
        UPDATE mining_schedules
        SET last_run_at = %s,
            next_run_at = %s
        WHERE id = %s
        """,
        (now, next_run, schedule_id)
    )
    
    conn.commit()
    cursor.close()
    
    print(f"✅ Updated schedule {schedule_id}:")
    print(f"   Last Run: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Next Run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    return True


def main():
    print("\n" + "="*70)
    print("Schedule Next Run Time Test Script")
    print("="*70)
    
    # Load config
    config = Config()
    
    # Connect to database
    try:
        conn = pymysql.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            charset='utf8mb4'
        )
        print(f"✅ Connected to database: {config.DB_NAME}\n")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)
    
    try:
        # List all active schedules
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            """
            SELECT id, job_name, schedule_type, schedule_time, is_active, next_run_at
            FROM mining_schedules
            WHERE is_active = 1
            ORDER BY id
            """
        )
        schedules = cursor.fetchall()
        cursor.close()
        
        if not schedules:
            print("❌ No active schedules found")
            return
        
        print("Active Schedules:")
        print("-" * 70)
        for s in schedules:
            print(f"{s['id']:3d}. {s['job_name']:30s} | {s['schedule_type']:8s} | Next: {s['next_run_at']}")
        print("-" * 70)
        
        # Get schedule ID from user
        schedule_id = input("\nEnter schedule ID to test (or press Enter to exit): ").strip()
        
        if not schedule_id:
            print("Exiting...")
            return
        
        schedule_id = int(schedule_id)
        
        # Show current status
        print("\n📊 BEFORE UPDATE:")
        schedule = show_schedule_status(conn, schedule_id)
        
        if not schedule:
            return
        
        # Confirm action
        confirm = input("Simulate job execution and update next_run_at? (y/n): ").strip().lower()
        
        if confirm != 'y':
            print("Cancelled.")
            return
        
        # Simulate execution
        print("\n⚙️  SIMULATING JOB EXECUTION...")
        if simulate_job_execution(conn, schedule_id):
            # Show updated status
            print("\n📊 AFTER UPDATE:")
            show_schedule_status(conn, schedule_id)
            print("✅ Test completed successfully!")
        else:
            print("❌ Test failed")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
        print("\n" + "="*70)
        print("Database connection closed")
        print("="*70 + "\n")


if __name__ == "__main__":
    main()
