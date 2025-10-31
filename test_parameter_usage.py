#!/usr/bin/env python3
"""
Test script to verify that scheduler uses exact user-provided algorithm parameters
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

def test_parameter_usage():
    """Test that user-provided parameters are used correctly"""
    try:
        from app.modules.association_mining.services.scheduler_service import SchedulerService
        
        # Create scheduler service
        scheduler = SchedulerService()
        
        logger.info("✅ Successfully created SchedulerService")
        
        # Test parameters that would have been overridden before our fix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_params = {
            'job_name': f'parameter_test_job_{timestamp}',  # Unique name each time
            'job_description': 'Testing that low thresholds are respected',
            'schedule_type': 'daily',
            'schedule_time': '23:59',  # Late time to avoid immediate execution
            'min_support': 0.01,        # 1% - would have been forced to 5% before fix
            'min_confidence': 0.05,     # 5% - would have been forced to 10% before fix
            'min_lift': 1.0,
            'max_recommendations': 50,   # Higher number to get more results
            'decay_rate': 0.05,
            'output_table': 'sku_recommendations_test',
            'is_active': False  # Don't actually schedule it
        }
        
        logger.info(f"🧪 Testing with low thresholds:")
        logger.info(f"   min_support: {test_params['min_support']} (1%)")
        logger.info(f"   min_confidence: {test_params['min_confidence']} (5%)")
        logger.info(f"   max_recommendations: {test_params['max_recommendations']}")
        
        # Create the schedule (but inactive)
        result = scheduler.create_schedule(test_params)
        schedule_id = result['schedule_id']  # Correct key name
        
        logger.info(f"✅ Created test schedule with ID: {schedule_id}")
        
        # Get the schedule back to verify parameters are stored correctly
        schedules = scheduler.get_schedules()
        test_schedule = None
        for schedule in schedules:
            if schedule['id'] == schedule_id:
                test_schedule = schedule
                break
        
        if test_schedule:
            logger.info(f"📋 Stored parameters verification:")
            logger.info(f"   min_support: {test_schedule['min_support']} (should be 0.01)")
            logger.info(f"   min_confidence: {test_schedule['min_confidence']} (should be 0.05)")
            logger.info(f"   max_recommendations: {test_schedule['max_recommendations']} (should be 50)")
            
            # Verify the parameters match what we set
            if (test_schedule['min_support'] == 0.01 and 
                test_schedule['min_confidence'] == 0.05 and
                test_schedule['max_recommendations'] == 50):
                logger.info("✅ Parameters stored correctly!")
            else:
                logger.error("❌ Parameters were modified during storage!")
                return False
        else:
            logger.error("❌ Could not find created test schedule!")
            return False
        
        # Clean up the test schedule
        scheduler.delete_schedule(schedule_id)
        logger.info(f"🧹 Cleaned up test schedule {schedule_id}")
        
        logger.info("🎉 Parameter usage test completed successfully!")
        logger.info("💡 With the fix, low threshold values should now generate more recommendations")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing parameter usage: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("🧪 Testing algorithm parameter usage in scheduler...")
    success = test_parameter_usage()
    
    if success:
        logger.info("🎉 Test completed successfully!")
        logger.info("📊 Lower thresholds should now generate more association rules!")
    else:
        logger.error("💥 Test failed!")
        sys.exit(1)