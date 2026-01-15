#!/usr/bin/env python3
"""
Test script to verify mining logging improvements
Shows output table name and exact insert counts
"""

import requests
import json
import time

def test_mining():
    """Test mining and check logging"""
    print("=" * 80)
    print("TESTING MINING WITH ENHANCED LOGGING")
    print("=" * 80)
    
    # Mining parameters
    payload = {
        "days_back": 600,
        "top_skus": 20,
        "min_support": 0.01,
        "min_confidence": 0.3,
        "min_lift": 1.0,
        "max_recommendations": 10,
        "decay_rate": 0.05
    }
    
    print("\n📊 Starting mining with parameters:")
    print(json.dumps(payload, indent=2))
    
    try:
        # Start mining
        print("\n🚀 Sending mining request...")
        response = requests.post(
            "http://localhost:5000/api/mine-direct",
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print("\n✅ Mining completed successfully!")
                print(f"\n📋 Job ID: {result.get('job_id')}")
                
                # Display stats
                stats = result.get('stats', {})
                print(f"\n📊 MINING STATISTICS:")
                print(f"   Total Rules Generated: {stats.get('total_rules')}")
                print(f"   Top SKUs Analyzed: {stats.get('top_n_skus')}")
                print(f"   Total Orders: {stats.get('total_orders')}")
                print(f"   Mining Duration: {stats.get('mining_duration')}")
                print(f"   CSV File: {stats.get('csv_filename')}")
                
                # Display database statistics (NEW!)
                db_stats = stats.get('database_stats', {})
                if db_stats:
                    print(f"\n💾 DATABASE STATISTICS:")
                    print(f"   ✨ Output Table: {db_stats.get('output_table')}")
                    print(f"   📝 Rules Generated: {db_stats.get('total_generated')}")
                    print(f"   ✓ Valid After Filtering: {db_stats.get('valid_after_filtering')}")
                    print(f"   💾 Total Written to DB: {db_stats.get('total_written')}")
                    print(f"   ➕ New Inserts: {db_stats.get('new_inserts')}")
                    print(f"   🔄 Updated Existing: {db_stats.get('updated_existing')}")
                else:
                    print(f"\n⚠️  Database stats not available (check if code is updated)")
                
                # Check logs
                print(f"\n📋 Checking logs at http://localhost:5000/logs")
                print(f"   The logs should now show:")
                print(f"   1. Output table name: {db_stats.get('output_table', 'N/A')}")
                print(f"   2. Exact insert count: {db_stats.get('total_written', 'N/A')}")
                
            else:
                print(f"\n❌ Mining failed: {result.get('error')}")
        else:
            print(f"\n❌ HTTP Error {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error: Server not running")
        print("   Please start the server with: .\\quick_start.py")
    except requests.exceptions.Timeout:
        print("\n⏱️  Timeout: Mining took too long")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_mining()
