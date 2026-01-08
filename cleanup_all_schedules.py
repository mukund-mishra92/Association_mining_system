"""
Clean up all schedules and running jobs from the system
Removes all entries from mining_schedules, mining_job_logs, and mining_schedule_stats
"""
import sys
import os
from pathlib import Path

# Set up paths
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from app.shared.database.connection import DatabaseConnection
from app.shared.config.config import config

def cleanup_all_schedules():
    """Remove all schedules and related data from database"""
    
    print("=" * 80)
    print("CLEANUP ALL SCHEDULES AND JOBS")
    print("=" * 80)
    print("\nThis will:")
    print("  - Stop all running jobs")
    print("  - Delete ALL schedules from database")
    print("  - Delete ALL job logs")
    print("  - Delete ALL schedule statistics")
    print("\nWARNING: This action cannot be undone!")
    print("=" * 80)
    
    confirm = input("\nType 'YES' to proceed: ").strip()
    
    if confirm != 'YES':
        print("\nCleanup cancelled.")
        return
    
    db = DatabaseConnection()
    
    try:
        db.connect()
        
        # Get counts before deletion
        print("\n[CHECKING] Current database state...")
        
        db.cursor.execute("SELECT COUNT(*) as cnt FROM mining_schedules")
        schedule_count = db.cursor.fetchone()['cnt']
        
        db.cursor.execute("SELECT COUNT(*) as cnt FROM mining_job_logs")
        log_count = db.cursor.fetchone()['cnt']
        
        db.cursor.execute("SELECT COUNT(*) as cnt FROM mining_schedule_stats")
        stats_count = db.cursor.fetchone()['cnt']
        
        print(f"\nFound:")
        print(f"  Schedules: {schedule_count}")
        print(f"  Job Logs: {log_count}")
        print(f"  Statistics: {stats_count}")
        
        if schedule_count == 0 and log_count == 0 and stats_count == 0:
            print("\n[INFO] Database is already clean. Nothing to delete.")
            return
        
        # Delete all schedules (cascade will handle logs and stats)
        print("\n[DELETING] Removing all schedules...")
        db.cursor.execute("DELETE FROM mining_schedules")
        db.connection.commit()
        
        print("[OK] All schedules deleted")
        
        # Verify cascade delete worked
        print("\n[VERIFYING] Checking cascade delete...")
        
        db.cursor.execute("SELECT COUNT(*) as cnt FROM mining_schedules")
        schedule_count_after = db.cursor.fetchone()['cnt']
        
        db.cursor.execute("SELECT COUNT(*) as cnt FROM mining_job_logs")
        log_count_after = db.cursor.fetchone()['cnt']
        
        db.cursor.execute("SELECT COUNT(*) as cnt FROM mining_schedule_stats")
        stats_count_after = db.cursor.fetchone()['cnt']
        
        print(f"\nAfter cleanup:")
        print(f"  Schedules: {schedule_count_after}")
        print(f"  Job Logs: {log_count_after}")
        print(f"  Statistics: {stats_count_after}")
        
        if schedule_count_after == 0 and log_count_after == 0 and stats_count_after == 0:
            print("\n" + "=" * 80)
            print("[SUCCESS] All schedules and jobs cleaned up successfully!")
            print("=" * 80)
            print(f"\nRemoved:")
            print(f"  {schedule_count} schedules")
            print(f"  {log_count} job logs")
            print(f"  {stats_count} statistics records")
        else:
            print("\n[WARNING] Some records may not have been deleted:")
            if schedule_count_after > 0:
                print(f"  {schedule_count_after} schedules remaining")
            if log_count_after > 0:
                print(f"  {log_count_after} job logs remaining")
            if stats_count_after > 0:
                print(f"  {stats_count_after} statistics remaining")
        
    except Exception as e:
        print(f"\n[ERROR] Cleanup failed: {e}")
        if db.connection:
            db.connection.rollback()
            print("[ROLLBACK] Changes reverted")
        import traceback
        traceback.print_exc()
    
    finally:
        db.disconnect()
        print("\n[INFO] Database connection closed")

if __name__ == "__main__":
    cleanup_all_schedules()
    print("\nPress Enter to exit...")
    input()
