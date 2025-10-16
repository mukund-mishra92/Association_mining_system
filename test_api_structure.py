import requests
import json

# Test the API directly to see the task result structure
def test_api_structure():
    try:
        # First, start a mining task
        print("🔍 Testing API task result structure...")
        
        # Make a simple request to start mining
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
            
            # Wait for mining to complete
            import time
            max_wait = 60  # Wait up to 60 seconds
            wait_time = 0
            
            print("⏳ Waiting for mining to complete...")
            
            while wait_time < max_wait:
                time.sleep(2)
                wait_time += 2
                
                # Check task status
                status_response = requests.get(f"http://127.0.0.1:8001/api/v1/task/{task_id}")
                
                if status_response.status_code == 200:
                    task_data = status_response.json()
                    status = task_data.get('status')
                    print(f"📊 Task status: {status} (waited {wait_time}s)")
                    
                    if status == 'completed':
                        print(f"📊 Task progress: {task_data.get('progress')}")
                        print(f"📊 Task message: {task_data.get('message')}")
                        
                        if task_data.get('result'):
                            result = task_data['result']
                            print(f"\n📋 RESULT STRUCTURE:")
                            print(f"  Result keys: {list(result.keys())}")
                            
                            if 'stats' in result:
                                stats = result['stats']
                                print(f"  Stats keys: {list(stats.keys())}")
                                print(f"  Stats content: {stats}")
                            
                            if 'rules' in result:
                                rules = result['rules']
                                print(f"  Rules count: {len(rules)}")
                                if rules:
                                    print(f"  First rule keys: {list(rules[0].keys())}")
                                    print(f"  First rule sample: {rules[0]}")
                        else:
                            print("❌ No result found in task data")
                            print(f"Task data keys: {list(task_data.keys())}")
                        break
                    elif status == 'failed':
                        print(f"❌ Task failed: {task_data.get('error')}")
                        break
                    else:
                        print(f"⏳ Still running... progress: {task_data.get('progress')}")
                else:
                    print(f"❌ Failed to get task status: {status_response.status_code}")
                    break
            
            if wait_time >= max_wait:
                print("⏰ Timeout waiting for task completion")
        else:
            print(f"❌ Failed to start mining: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")

if __name__ == "__main__":
    test_api_structure()