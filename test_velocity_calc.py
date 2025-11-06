import requests
import json
from datetime import date

def test_velocity_calculation():
    """Test the velocity calculation API endpoint"""
    
    # API endpoint
    url = "http://localhost:5000/api/velocity/calculate-sku-velocities"
    
    # Database configuration
    db_config = {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "root",
        "database": "neo"
    }
    
    # Request payload
    payload = {
        "db_config": db_config,
        "analysis_date": str(date.today()),
        "parameters": {
            "analysis_period_days": 90,
            "time_decay_rate": 0.05,
            "min_orders_for_calculation": 5,
            "high_velocity_threshold": 0.80,
            "medium_velocity_threshold": 0.50
        }
    }
    
    print("🧪 Testing Velocity Calculation API...")
    print(f"📡 Endpoint: {url}")
    print(f"📅 Analysis Date: {payload['analysis_date']}")
    print(f"⚙️ Parameters: {payload['parameters']}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API call successful!")
            
            if result.get('success'):
                print("🎉 Velocity calculation completed!")
                
                stats = result.get('statistics', {})
                print(f"\n📈 Results Summary:")
                print(f"   🏃 High Velocity SKUs: {stats.get('high_velocity', 0)}")
                print(f"   🚶 Medium Velocity SKUs: {stats.get('medium_velocity', 0)}")
                print(f"   🐌 Low Velocity SKUs: {stats.get('low_velocity', 0)}")
                print(f"   📦 Total SKUs Updated: {stats.get('total_skus_updated', 0)}")
                print(f"   🔢 Total SKUs Analyzed: {stats.get('total_skus_analyzed', 0)}")
                
                calculation_info = result.get('calculation_info', {})
                print(f"\n⚙️ Calculation Details:")
                print(f"   📊 Analysis Period: {calculation_info.get('analysis_period_days', 'N/A')} days")
                print(f"   ⏰ Processing Time: {calculation_info.get('processing_time_seconds', 'N/A')} seconds")
                print(f"   📅 Analysis Date: {calculation_info.get('analysis_date', 'N/A')}")
                
            else:
                print(f"❌ Velocity calculation failed: {result.get('message', 'Unknown error')}")
                
        else:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_velocity_calculation()