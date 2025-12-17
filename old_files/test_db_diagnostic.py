"""
Test database connectivity and diagnostic queries
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.modules.neo_chatbot.services.sql_assistant_service import SQLAssistantService

def test_database_queries():
    """Test various diagnostic queries"""
    print("=" * 80)
    print("Testing Database Connectivity and Diagnostic Queries")
    print("=" * 80)
    
    sql_service = SQLAssistantService()
    
    if not sql_service.db_available:
        print("❌ Database is NOT available!")
        return
    
    print("✅ Database is available\n")
    
    # Test queries
    test_queries = [
        ("Database connection test", "SELECT 1 as test;"),
        ("Check bot_master", "SELECT * FROM bot_master LIMIT 5;"),
        ("Check task_master", "SELECT * FROM task_master LIMIT 5;"),
        ("Check station_master", "SELECT * FROM station_master LIMIT 5;"),
        ("Check order_bin_mapping", "SELECT * FROM order_bin_mapping LIMIT 5;"),
        ("Check station_pick_task_master", "SELECT * FROM station_pick_task_master LIMIT 5;"),
        ("Check hw_conveyer_master", "SELECT * FROM hw_conveyer_master LIMIT 5;"),
        ("Check active tasks", "SELECT STATUS, COUNT(*) as count FROM task_master GROUP BY STATUS;"),
        ("Check pending bins", "SELECT * FROM order_bin_mapping WHERE STATUS = 'PENDING' LIMIT 5;"),
    ]
    
    for name, query in test_queries:
        print(f"\n{'=' * 60}")
        print(f"Testing: {name}")
        print(f"Query: {query}")
        print("-" * 60)
        
        results, error = sql_service._execute_query_safe(query)
        
        if error:
            print(f"❌ ERROR: {error}")
        else:
            print(f"✅ SUCCESS: Found {len(results)} records")
            if results:
                print(f"Sample data: {results[0]}")
        
    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)

if __name__ == "__main__":
    test_database_queries()
