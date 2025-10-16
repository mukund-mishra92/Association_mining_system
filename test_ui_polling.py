import requests
import json

# Test what the UI actually sees when polling task status
def test_ui_polling():
    try:
        print("🔍 Testing what UI sees when polling task status...")
        
        # Start a mining task
        response = requests.post(
            "http://127.0.0.1:8001/api/v1/mine-rules", 
            json={
                "days_back": 30,
                "use_enhanced_mining": True,
                "time_weighting_method": "exponential_decay"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✅ Mining started, task_id: {task_id}")
            
            # Wait for completion and check what UI would see
            import time
            max_wait = 60
            wait_time = 0
            
            print("⏳ Monitoring task status (UI perspective)...")
            
            while wait_time < max_wait:
                time.sleep(2)
                wait_time += 2
                
                # This is the same call the UI makes
                status_response = requests.get(f"http://127.0.0.1:8001/api/v1/task/{task_id}")
                
                if status_response.status_code == 200:
                    task_data = status_response.json()
                    status = task_data.get('status')
                    
                    print(f"📊 UI sees - Status: {status}, Progress: {task_data.get('progress')}")
                    
                    if status == 'completed':
                        print(f"\n🎯 TASK COMPLETED - UI DATA ANALYSIS:")
                        print(f"  All task keys: {list(task_data.keys())}")
                        
                        # Check if result exists
                        if 'result' in task_data and task_data['result']:
                            result = task_data['result']
                            print(f"  ✅ Result exists: {list(result.keys())}")
                            
                            if 'rules' in result:
                                rules = result['rules']
                                print(f"  ✅ Rules found: {len(rules)} rules")
                                if rules:
                                    print(f"  ✅ Sample rule: {rules[0]}")
                            else:
                                print(f"  ❌ No 'rules' key in result")
                                
                            if 'stats' in result:
                                stats = result['stats']
                                print(f"  ✅ Stats found: {stats}")
                            else:
                                print(f"  ❌ No 'stats' key in result")
                        else:
                            print(f"  ❌ No result field or result is empty")
                            print(f"  Task data: {json.dumps(task_data, indent=2)}")
                        break
                    elif status == 'failed':
                        print(f"❌ Task failed: {task_data.get('error')}")
                        break
                else:
                    print(f"❌ Failed to get task status: {status_response.status_code}")
                    break
            
            if wait_time >= max_wait:
                print("⏰ Timeout waiting for task completion")
        else:
            print(f"❌ Failed to start mining: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing UI polling: {e}")

if __name__ == "__main__":
    test_ui_polling()