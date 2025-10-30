#!/usr/bin/env python3
"""
Test script to verify the scheduler database connection fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, time
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_scheduler_connection_fix():
    """Test the new database connection handling in the scheduler"""
    try:
        from app.modules.association_mining.services.scheduler_service import SchedulerService
        
        # Create scheduler service
        scheduler = SchedulerService()
        
        logger.info("✅ Successfully imported SchedulerService")
        
        # Try to start the scheduler
        result = scheduler.start_scheduler()
        logger.info(f"Scheduler start result: {result}")
        
        # Get status
        status = scheduler.get_status()
        logger.info(f"Scheduler status: {status}")
        
        # Get existing schedules
        schedules = scheduler.get_schedules()
        logger.info(f"Found {len(schedules)} existing schedules")
        
        if schedules:
            # Get logs for testing
            logs = scheduler.get_job_logs(limit=5)
            logger.info(f"Found {len(logs)} recent job logs")
            
            for log in logs[:3]:
                logger.info(f"  Log {log['id']}: {log['job_name']} - {log['execution_status']}")
        
        logger.info("✅ Scheduler service appears to be working correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing scheduler: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("🧪 Testing scheduler database connection fix...")
    success = test_scheduler_connection_fix()
    
    if success:
        logger.info("🎉 Test completed successfully!")
    else:
        logger.error("💥 Test failed!")
        sys.exit(1)