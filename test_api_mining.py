#!/usr/bin/env python3
"""
Test script for API-based mining
Tests the fixed API mining endpoint
"""

import requests
import json
import time

def test_api_mining():
    """Test the API-based mining endpoint"""
    
    print("🔍 API-Based Mining Test")
    print("=" * 50)
    
    # Test configuration - using the same low thresholds that should find rules
    test_config = {
        "days_back": 60,
        "top_skus": 20,
        "min_support": 0.01,  # Very low - should find many rules
        "min_confidence": 0.30,
        "min_lift": 1.0,
        "max_recommendations": 10,
        "decay_rate": 0.05,
        "enhanced": True,
        "time_method": "exponential_decay"
    }
    
    print(f"🧪 Testing API Mining with config:")
    print(f"   Days Back: {test_config['days_back']}")
    print(f"   Top SKUs: {test_config['top_skus']}")
    print(f"   Min Support: {test_config['min_support']}")
    print(f"   Min Confidence: {test_config['min_confidence']}")
    print(f"   Enhanced: {test_config['enhanced']}")
    print(f"   Time Method: {test_config['time_method']}")
    
    try:
        print("\n📊 Sending mining request...")
        
        # Send mining request
        response = requests.post(
            "http://localhost:5000/api/mine-api",
            json=test_config,
            timeout=60
        )
        
        print(f"📈 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response:")
            print(json.dumps(data, indent=2, default=str)[:1000] + "...")
            
            if data.get('success'):
                print(f"\n✅ API Mining successful!")
                
                stats = data.get('stats', {})
                rules = data.get('rules', [])
                enhanced_features = data.get('enhanced_features', {})
                
                print(f"\n📋 Mining Results:")
                print(f"  Rules Found: {len(rules)}")
                if stats:
                    print(f"  Mining Duration: {stats.get('mining_duration', 'N/A')}")
                    print(f"  Total Orders: {stats.get('total_orders', 'N/A')}")
                    print(f"  Top SKUs: {stats.get('top_n_skus', 'N/A')}")
                
                if enhanced_features:
                    print(f"\n🚀 Enhanced Features:")
                    print(f"  Temporal Weighting: {enhanced_features.get('temporal_weighting', 'N/A')}")
                    print(f"  Time Method: {enhanced_features.get('time_method', 'N/A')}")
                    print(f"  Decay Rate: {enhanced_features.get('decay_rate', 'N/A')}")
                
                if rules:
                    print(f"\n🎯 Sample Rules (first 3):")
                    for i, rule in enumerate(rules[:3]):
                        print(f"  {i+1}. {rule.get('sku1', 'N/A')} → {rule.get('sku2', 'N/A')}")
                        print(f"     Confidence: {rule.get('confidence', 0):.3f}, Support: {rule.get('support', 0):.3f}, Lift: {rule.get('lift', 0):.3f}")
                
                # Test progress tracking
                print(f"\n📊 Testing progress tracking...")
                task_id = data.get('task_id')
                if task_id:
                    progress_response = requests.get("http://localhost:5000/api/mining-progress")
                    if progress_response.status_code == 200:
                        progress_data = progress_response.json()
                        print(f"  Progress Status: {progress_data.get('status', 'Unknown')}")
                        print(f"  Progress: {progress_data.get('progress', 0)}%")
                        print(f"  Message: {progress_data.get('message', 'N/A')}")
                
            else:
                print(f"❌ API Mining failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - mining may be taking longer than expected")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Test completed!")

if __name__ == "__main__":
    test_api_mining()