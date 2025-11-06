#!/usr/bin/env python3
"""
Test script to verify database connection API endpoint
"""
import requests
import json

def test_database_connection():
    """Test the database connection API endpoint"""
    
    # Test data matching the form fields
    test_config = {
        "host": "localhost",
        "port": 3306,
        "user": "root", 
        "password": "root",  # Correct password from .env file
        "database": "neo",
        "order_table": "wms_to_wcs_order_line_request_data",
        "sku_master_table": "sku_master",
        "rules_table": "sku_recommendations",
        "history_table": "mining_history", 
        "stats_table": "mining_statistics"
    }
    
    print("🧪 Testing Database Connection API...")
    print(f"📊 Config: {test_config['host']}:{test_config['port']}/{test_config['database']}")
    
    try:
        # Test the API endpoint
        response = requests.post(
            'http://localhost:5000/api/test-db-connection',
            json=test_config,
            timeout=10
        )
        
        print(f"📈 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response:")
            print(json.dumps(data, indent=2))
            
            if data.get('success'):
                print("\n✅ Database connection successful!")
                
                if data.get('tables'):
                    print("\n📋 Table Status:")
                    for table_name, info in data['tables'].items():
                        status = "✅ Exists" if info.get('exists') else "❌ Missing"
                        count = info.get('count', 0)
                        print(f"  {table_name}: {status} ({count:,} records)")
                        
                return True
            else:
                print(f"❌ Database connection failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Database Connection Test")
    print("=" * 50)
    
    success = test_database_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Test completed successfully!")
    else:
        print("💥 Test failed - check configuration and database access")