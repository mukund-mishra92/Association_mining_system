#!/usr/bin/env python3
"""
Check Recommendations Data - Show actual items for UI testing
"""

from app.shared.database.connection import DatabaseConnection
import requests

def check_actual_data():
    """Check what items are actually in the recommendations table"""
    print("🔍 Checking Actual Recommendations Data")
    print("=" * 60)
    
    db = DatabaseConnection()
    
    try:
        if not db.connect():
            print("❌ Failed to connect to database")
            return
        
        from app.shared.config.config import config
        table_name = config.RECOMMENDATIONS_TABLE
        
        # Get count
        db.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total = db.cursor.fetchone()[0]
        print(f"📊 Total recommendations: {total:,}")
        
        if total == 0:
            print("❌ No recommendations found!")
            return
        
        # Get sample items (parent items that have recommendations)
        db.cursor.execute(f"""
            SELECT PARENT_ARTICLE_ID, COUNT(*) as rec_count,
                   AVG(PROXIMITY_SCORE) as avg_score,
                   MAX(PROXIMITY_SCORE) as max_score
            FROM {table_name} 
            GROUP BY PARENT_ARTICLE_ID 
            ORDER BY rec_count DESC, max_score DESC
            LIMIT 10
        """)
        
        parent_items = db.cursor.fetchall()
        
        print("\n📦 Items with recommendations (for UI testing):")
        print("-" * 60)
        
        test_items = []
        for i, (parent_id, count, avg_score, max_score) in enumerate(parent_items, 1):
            print(f"{i:2d}. Item: {parent_id}")
            print(f"    Recommendations: {count}")
            print(f"    Score range: avg={avg_score:.3f}, max={max_score:.3f}")
            
            # Get sample recommendations for this item
            db.cursor.execute(f"""
                SELECT CHILD_ARTICLE_ID, PROXIMITY_SCORE
                FROM {table_name}
                WHERE PARENT_ARTICLE_ID = %s
                ORDER BY PROXIMITY_SCORE DESC
                LIMIT 3
            """, (parent_id,))
            
            recommendations = db.cursor.fetchall()
            print(f"    Top recommendations:")
            for j, (child_id, score) in enumerate(recommendations, 1):
                print(f"      {j}. {child_id} (score: {score:.3f})")
            
            print()
            test_items.append(parent_id)
        
        # Test API directly
        if test_items:
            print("🧪 Testing API Endpoints:")
            print("-" * 40)
            
            test_item = test_items[0]
            print(f"Testing with: {test_item}")
            
            try:
                # Test FastAPI endpoint
                api_url = f"http://127.0.0.1:8080/api/v1/recommendations/{test_item}"
                print(f"📡 FastAPI URL: {api_url}")
                
                response = requests.get(api_url, timeout=10)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    recs = data.get('recommendations', [])
                    print(f"   ✅ FastAPI returned {len(recs)} recommendations")
                    
                    for i, rec in enumerate(recs[:3], 1):
                        print(f"      {i}. {rec['recommended_item']} (score: {rec['score']:.3f})")
                else:
                    print(f"   ❌ FastAPI Error: {response.text}")
                
                # Test Flask web endpoint
                web_url = f"http://127.0.0.1:5000/api/recommendations/{test_item}"
                print(f"\n🌐 Flask Web URL: {web_url}")
                
                web_response = requests.get(web_url, timeout=10)
                print(f"   Status: {web_response.status_code}")
                
                if web_response.status_code == 200:
                    web_data = web_response.json()
                    if web_data.get('success'):
                        web_recs = web_data['data'].get('recommendations', [])
                        print(f"   ✅ Flask Web returned {len(web_recs)} recommendations")
                    else:
                        print(f"   ❌ Flask Web Error: {web_data.get('error')}")
                else:
                    print(f"   ❌ Flask Web Error: {web_response.text}")
                
            except requests.exceptions.ConnectionError as e:
                if "8080" in str(e):
                    print("   ❌ FastAPI server not running on port 8080")
                if "5000" in str(e):
                    print("   ❌ Flask web server not running on port 5000")
            except Exception as e:
                print(f"   ❌ Error testing APIs: {e}")
        
        # Instructions for UI testing
        print(f"\n💡 How to test in the UI:")
        print(f"   1. Open your web application")
        print(f"   2. Go to the 'Recommendations' section")
        print(f"   3. Enter one of these Item IDs (not names!):")
        
        for i, item in enumerate(test_items[:5], 1):
            print(f"      {i}. {item}")
        
        print(f"   4. Click 'Get Recommendations'")
        print(f"   5. You should see the recommendations listed above")
        
        print(f"\n🔧 If UI still doesn't work:")
        print(f"   - Clear browser cache (Ctrl+F5)")
        print(f"   - Check browser console for JavaScript errors")
        print(f"   - Verify both servers are running:")
        print(f"     • FastAPI on port 8080")
        print(f"     • Flask Web on port 5000")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.disconnect()

if __name__ == "__main__":
    check_actual_data()