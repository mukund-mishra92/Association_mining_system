"""
Test script to verify the maintenance task query fix
Run this to test if the SQL Assistant generates correct queries for maintenance tasks
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.modules.neo_chatbot.services.sql_assistant_service import SQLAssistantService
from app.modules.neo_chatbot.models.schemas import ChatRequest, ChatbotType
import json
import uuid

def test_maintenance_task_query():
    """Test if SQL Assistant generates correct maintenance task query"""
    
    print("=" * 80)
    print("Testing Maintenance Task Query Fix")
    print("=" * 80)
    print()
    
    # Initialize service
    print("1. Initializing SQL Assistant Service...")
    service = SQLAssistantService()
    print(f"   ✓ Service initialized (DB available: {service.db_available})")
    print()
    
    # Test query
    user_question = "I need to find out the bots involved and task id for which the bots have assigned the task but not able to complete it. need to add the date as well"
    
    print("2. User Question:")
    print(f"   '{user_question}'")
    print()
    
    print("3. Generating SQL query...")
    request = ChatRequest(
        message=user_question,
        chatbot_type=ChatbotType.SQL_ASSISTANT,
        session_id=str(uuid.uuid4())
    )
    response = service.process_query(request)
    
    print()
    print("4. Generated SQL Query:")
    print("-" * 80)
    print(response.sql_query)
    print("-" * 80)
    print()
    
    # Check if query is correct
    print("5. Validation:")
    
    checks = {
        "Uses correct table": "dashboard_log_maintenance_task_master" in response.sql_query,
        "Uses MAINTENANCE_POINT_BOT_ID (not BOT_ID)": "MAINTENANCE_POINT_BOT_ID" in response.sql_query,
        "Does NOT use BOT_ID": "BOT_ID" not in response.sql_query or "MAINTENANCE_POINT_BOT_ID" in response.sql_query,
        "Includes MAINTENANCE_TASK_ID": "MAINTENANCE_TASK_ID" in response.sql_query,
        "Includes date field": "INSERTED_TIMESTAMP" in response.sql_query or "UPDATED_TIMESTAMP" in response.sql_query,
        "Filters incomplete tasks": "TASK_DONE" in response.sql_query and "= 0" in response.sql_query,
        "Has LIMIT clause": "LIMIT" in response.sql_query
    }
    
    all_passed = True
    for check_name, result in checks.items():
        status = "✓" if result else "✗"
        print(f"   {status} {check_name}")
        if not result:
            all_passed = False
    
    print()
    
    # Show execution result
    print("6. Query Execution:")
    if response.query_results is not None:
        print(f"   ✓ Query executed successfully")
        print(f"   Rows returned: {len(response.query_results)}")
        print(f"   Confidence: {response.confidence_score:.1%}" if response.confidence_score else "   Confidence: N/A")
        
        if response.query_results and len(response.query_results) > 0:
            print()
            print("   Sample results (first 3 rows):")
            for i, row in enumerate(response.query_results[:3], 1):
                print(f"   {i}. {row}")
        else:
            print("   (No incomplete tasks found - this is OK, means all tasks are complete)")
    elif "error" in response.response.lower() or "failed" in response.response.lower():
        print(f"   ✗ Query failed: {response.response}")
        all_passed = False
    else:
        print(f"   Response: {response.response[:200]}")
        if response.query_results == []:
            print("   (No incomplete tasks found - this is OK)")
    
    print()
    print("=" * 80)
    
    if all_passed:
        print("✅ TEST PASSED - SQL Assistant generates correct query!")
    else:
        print("❌ TEST FAILED - Some checks did not pass")
    
    print("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    try:
        success = test_maintenance_task_query()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
