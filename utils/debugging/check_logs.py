#!/usr/bin/env python3
"""
Check recent job logs to identify stuck or long-running jobs
"""

from app.modules.association_mining.services.scheduler_service import SchedulerService

def main():
    scheduler = SchedulerService()
    logs = scheduler.get_job_logs(limit=10)
    
    print("Recent Job Status:")
    print("=" * 80)
    
    for log in logs:
        duration = log.get("execution_time_seconds", "Still running")
        if duration != "Still running":
            duration = f"{duration}s"
        
        print(f'Job {log["id"]}: {log["job_name"]}')
        print(f'  Status: {log["execution_status"]}')
        print(f'  Started: {log["started_at"]}')
        print(f'  Duration: {duration}')
        
        # Check for long running or stuck jobs
        if log["execution_status"] == "running":
            print(f'  ⚠️  Job is currently running')
            
        if log.get("execution_time_seconds") and log["execution_time_seconds"] > 300:  # 5+ minutes
            print(f'  ⚠️  Long execution time detected')
            
        if log.get("error_message"):
            print(f'  ❌ Error: {log["error_message"]}')
            
        print()

if __name__ == "__main__":
    main()