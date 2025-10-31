#!/usr/bin/env python3
"""
Check Recommendations Table - Verify what data is in the recommendations table
"""

from app.shared.database.connection import DatabaseConnection
import pandas as pd
from datetime import datetime

def check_recommendations_table():
    """Check what's in the recommendations table"""
    print("🔍 Checking Recommendations Table")
    print("=" * 60)
    
    db = DatabaseConnection()
    
    try:
        if not db.connect():
            print("❌ Failed to connect to database")
            return
        
        # Get table name from config
        from app.shared.config.config import config
        table_name = config.RECOMMENDATIONS_TABLE
        
        print(f"📋 Table: {table_name}")
        print()
        
        # Check if table exists
        db.cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        if not db.cursor.fetchone():
            print(f"❌ Table '{table_name}' does not exist!")
            return
        
        # Get table info
        db.cursor.execute(f"DESCRIBE {table_name}")
        columns = db.cursor.fetchall()
        print("📊 Table Structure:")
        for col in columns:
            print(f"   {col[0]} - {col[1]}")
        print()
        
        # Count total records
        db.cursor.execute(f"SELECT COUNT(*) as total FROM {table_name}")
        total_count = db.cursor.fetchone()[0]
        print(f"📈 Total Records: {total_count:,}")
        
        if total_count == 0:
            print("⚠️  Table is empty - no recommendations found!")
            return
        
        # Get latest records
        db.cursor.execute(f"""
            SELECT main_item, recommended_item, confidence_score, lift_score, 
                   composite_score, created_at 
            FROM {table_name} 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        recent_records = db.cursor.fetchall()
        
        if recent_records:
            print("\n🕐 Most Recent Recommendations:")
            print("-" * 60)
            for i, record in enumerate(recent_records, 1):
                main_item, rec_item, conf, lift, comp, created = record
                created_str = created.strftime('%Y-%m-%d %H:%M:%S') if created else 'Unknown'
                print(f"{i:2d}. {main_item} → {rec_item}")
                print(f"    Confidence: {conf:.3f}, Lift: {lift:.3f}, Score: {comp:.3f}")
                print(f"    Created: {created_str}")
                print()
        
        # Check for recent data (last 24 hours)
        db.cursor.execute(f"""
            SELECT COUNT(*) as recent_count 
            FROM {table_name} 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """)
        
        recent_count = db.cursor.fetchone()[0]
        print(f"🕐 Records from last 24 hours: {recent_count:,}")
        
        # Get unique items count
        db.cursor.execute(f"""
            SELECT COUNT(DISTINCT main_item) as unique_items 
            FROM {table_name}
        """)
        
        unique_items = db.cursor.fetchone()[0]
        print(f"📦 Unique items with recommendations: {unique_items:,}")
        
        # Sample a few items for testing
        db.cursor.execute(f"""
            SELECT DISTINCT main_item 
            FROM {table_name} 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        sample_items = [row[0] for row in db.cursor.fetchall()]
        
        if sample_items:
            print(f"\n🧪 Sample Items for Testing UI:")
            for i, item in enumerate(sample_items, 1):
                print(f"   {i}. {item}")
            
            print(f"\n💡 Try searching for one of these items in the UI:")
            print(f"   - Go to the recommendations section")
            print(f"   - Enter: {sample_items[0]}")
            print(f"   - Click 'Get Recommendations'")
        
    except Exception as e:
        print(f"❌ Error checking recommendations table: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.disconnect()

def test_api_endpoint():
    """Test the API endpoint directly"""
    print("\n🔧 Testing API Endpoint")
    print("=" * 40)
    
    try:
        import requests
        
        # Test health endpoint first
        health_response = requests.get("http://127.0.0.1:8080/api/v1/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ API server is running")
        else:
            print(f"⚠️  API server responding with status: {health_response.status_code}")
            return
        
        # Get a sample item from database
        db = DatabaseConnection()
        if not db.connect():
            print("❌ Cannot connect to database for testing")
            return
        
        from app.shared.config.config import config
        table_name = config.RECOMMENDATIONS_TABLE
        
        db.cursor.execute(f"""
            SELECT DISTINCT main_item 
            FROM {table_name} 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        
        result = db.cursor.fetchone()
        if not result:
            print("❌ No items found in recommendations table")
            return
        
        test_item = result[0]
        print(f"🧪 Testing with item: {test_item}")
        
        # Test the API endpoint
        api_url = f"http://127.0.0.1:8080/api/v1/recommendations/{test_item}"
        api_response = requests.get(api_url, timeout=10)
        
        print(f"📡 API Response Status: {api_response.status_code}")
        
        if api_response.status_code == 200:
            data = api_response.json()
            recs = data.get('recommendations', [])
            print(f"✅ API returned {len(recs)} recommendations")
            
            if recs:
                print("   Sample recommendations:")
                for i, rec in enumerate(recs[:3], 1):
                    print(f"     {i}. {rec.get('recommended_item')} (score: {rec.get('score', 0):.3f})")
            else:
                print("   ⚠️  No recommendations in API response")
        else:
            print(f"❌ API Error: {api_response.text}")
        
        db.disconnect()
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server - make sure it's running on port 8080")
    except Exception as e:
        print(f"❌ Error testing API: {e}")

if __name__ == "__main__":
    check_recommendations_table()
    test_api_endpoint()
    
    print(f"\n📋 Summary:")
    print(f"   1. Check if recommendations table has recent data")
    print(f"   2. Test the API endpoint directly")
    print(f"   3. If data exists but UI doesn't show it:")
    print(f"      - Clear browser cache and refresh")
    print(f"      - Check browser developer console for errors")
    print(f"      - Verify the correct table name in UI configuration")