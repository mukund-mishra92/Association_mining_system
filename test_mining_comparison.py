#!/usr/bin/env python3
"""
Test script to compare API-based mining vs Scheduled mining
to identify why scheduled mining times out while API mining completes quickly
"""
import time
from datetime import datetime
from app.modules.association_mining.api.endpoints import run_mining_task
from app.shared.utils.task_manager import TaskManager

def test_api_mining():
    """Test API-based mining directly"""
    print("\n" + "="*80)
    print("TEST 1: API-BASED MINING (Direct call to run_mining_task)")
    print("="*80)
    
    # Create task manager
    task_manager = TaskManager()
    
    # Use the same parameters as the schedule
    task_id = f"test_api_{int(time.time())}"
    
    # Custom config for article_proximity_score table
    custom_db_config = {
        'recommendations_table': 'article_proximity_score'
    }
    
    start_time = time.time()
    print(f"Start time: {datetime.now()}")
    print(f"Task ID: {task_id}")
    print(f"Output table: article_proximity_score")
    
    try:
        # Call run_mining_task with the same parameters
        run_mining_task(
            task_id=task_id,
            days_back=365,
            min_support=0.01,
            min_confidence=0.3,
            min_lift=1.0,
            max_recommendations=10,
            decay_rate=0.05,
            use_enhanced_mining=True,
            time_weighting_method='exponential_decay',
            time_segmentation='weekly',
            db_config=custom_db_config
        )
        
        duration = time.time() - start_time
        print(f"\n✅ API mining completed successfully!")
        print(f"Duration: {duration:.1f} seconds")
        
        # Check task status
        task = task_manager.get_task(task_id)
        if task:
            print(f"Task status: {task.status}")
            if task.result:
                print(f"Rules generated: {task.result.get('recommendations_count', 0)}")
                print(f"Records processed: {task.result.get('stats', {}).get('total_orders', 0)}")
        
        return True
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"\n❌ API mining failed after {duration:.1f} seconds")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_scheduled_mining_simulation():
    """Test scheduled mining by simulating what the scheduler does"""
    print("\n" + "="*80)
    print("TEST 2: SCHEDULED MINING SIMULATION (Mimics scheduler execution)")
    print("="*80)
    
    import threading
    from app.modules.association_mining.api.endpoints import run_mining_task
    import app.modules.association_mining.api.endpoints as endpoints_module
    
    task_id = f"test_scheduled_{int(time.time())}"
    
    # Custom config
    custom_db_config = {
        'recommendations_table': 'article_proximity_score'
    }
    
    # Create a minimal task manager (same as scheduler does)
    class SchedulerTaskManager:
        def __init__(self):
            self.result = None
            self.error = None
        
        def start_task(self, task_id, message):
            print(f"📋 {message}")
        
        def update_progress(self, task_id, progress, message):
            print(f"⏳ Progress {int(progress*100)}%: {message}")
        
        def complete_task(self, task_id, result=None, message=""):
            print(f"✅ {message}")
            self.result = result
        
        def fail_task(self, task_id, error_msg):
            print(f"❌ {error_msg}")
            self.error = error_msg
    
    task_manager = SchedulerTaskManager()
    
    # Replace the global task_manager (same as scheduler does)
    original_task_manager = endpoints_module.task_manager
    endpoints_module.task_manager = task_manager
    
    start_time = time.time()
    print(f"Start time: {datetime.now()}")
    print(f"Task ID: {task_id}")
    print(f"Output table: article_proximity_score")
    print(f"Timeout: 600 seconds")
    
    mining_completed = threading.Event()
    mining_error = {'error': None}
    
    def run_mining_with_timeout():
        try:
            run_mining_task(
                task_id=task_id,
                days_back=365,
                min_support=0.01,
                min_confidence=0.3,
                min_lift=1.0,
                max_recommendations=10,
                decay_rate=0.05,
                use_enhanced_mining=True,
                time_weighting_method='exponential_decay',
                time_segmentation='weekly',
                db_config=custom_db_config
            )
            mining_completed.set()
        except Exception as e:
            mining_error['error'] = e
            mining_completed.set()
    
    try:
        # Run in thread (same as scheduler)
        mining_thread = threading.Thread(target=run_mining_with_timeout, daemon=True)
        mining_thread.start()
        
        # Wait with timeout
        timeout = 600
        if not mining_completed.wait(timeout=timeout):
            duration = time.time() - start_time
            print(f"\n❌ Scheduled mining timed out after {duration:.1f} seconds")
            endpoints_module.task_manager = original_task_manager
            return False
        
        if mining_error['error']:
            duration = time.time() - start_time
            print(f"\n❌ Scheduled mining failed after {duration:.1f} seconds")
            print(f"Error: {str(mining_error['error'])}")
            import traceback
            traceback.print_exception(type(mining_error['error']), mining_error['error'], mining_error['error'].__traceback__)
            endpoints_module.task_manager = original_task_manager
            return False
        
        duration = time.time() - start_time
        print(f"\n✅ Scheduled mining completed successfully!")
        print(f"Duration: {duration:.1f} seconds")
        
        if task_manager.result:
            print(f"Rules generated: {task_manager.result.get('recommendations_count', 0)}")
            print(f"Records processed: {task_manager.result.get('stats', {}).get('total_orders', 0)}")
        
        endpoints_module.task_manager = original_task_manager
        return True
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"\n❌ Scheduled mining simulation failed after {duration:.1f} seconds")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        endpoints_module.task_manager = original_task_manager
        return False

if __name__ == "__main__":
    print("\n" + "="*80)
    print("MINING COMPARISON TEST")
    print("Testing why scheduled mining times out while API mining completes quickly")
    print("="*80)
    
    # Test 1: API-based mining
    api_success = test_api_mining()
    
    # Wait a bit between tests
    print("\n\nWaiting 5 seconds before next test...")
    time.sleep(5)
    
    # Test 2: Scheduled mining simulation
    scheduled_success = test_scheduled_mining_simulation()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"API Mining: {'✅ PASSED' if api_success else '❌ FAILED'}")
    print(f"Scheduled Mining: {'✅ PASSED' if scheduled_success else '❌ FAILED'}")
    
    if api_success and not scheduled_success:
        print("\n⚠️  ISSUE CONFIRMED: Scheduled mining is slower/different than API mining!")
        print("Check the logs above to identify the difference.")
    elif api_success and scheduled_success:
        print("\n✅ Both methods work - issue may be environment-specific")
    else:
        print("\n⚠️  Both methods have issues - check database/configuration")
