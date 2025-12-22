"""
Test Temporal Table Classification
Verifies that SQL Assistant correctly routes queries to log tables vs current tables
"""

import requests
import json

BASE_URL = "http://localhost:8000"
CHATBOT_ENDPOINT = f"{BASE_URL}/api/chatbot/chat"

def test_query(query, expected_table_type, description):
    """Test a single query and check which table was used"""
    print(f"\n{'='*80}")
    print(f"TEST: {description}")
    print(f"{'='*80}")
    print(f"Query: {query}")
    print(f"Expected Table Type: {expected_table_type}")
    
    payload = {
        "chatbot_type": "sql_assistant",
        "query": query,
        "session_id": "temporal_test_session"
    }
    
    try:
        response = requests.post(CHATBOT_ENDPOINT, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        # Extract SQL from metadata
        metadata = result.get('metadata', {})
        sql_query = metadata.get('sql_query', '')
        
        print(f"\nGenerated SQL:")
        print(f"{sql_query}")
        
        # Check which table was used
        sql_lower = sql_query.lower()
        
        if expected_table_type == 'LOG':
            # Check for log tables
            if any(log_table in sql_lower for log_table in [
                'task_detail_log', 'bot_master_log', 'bin_info_master_log',
                'order_line_log', 'alarm_log', 'charge_log'
            ]):
                print(f"\n✅ PASS: Correctly used LOG table")
                return True
            elif 'task_detail' in sql_lower and 'task_detail_log' not in sql_lower:
                print(f"\n❌ FAIL: Used current table (task_detail) instead of LOG table")
                print(f"   Should use: task_detail_log for historical queries")
                return False
            else:
                print(f"\n⚠️ UNCERTAIN: Could not determine table type from SQL")
                return False
                
        elif expected_table_type == 'CURRENT':
            # Check for current tables (without _log suffix)
            if any(current_table in sql_lower for current_table in [
                'task_detail', 'bot_master', 'bin_info_master', 'live_inventory'
            ]) and not any(log_table in sql_lower for log_table in [
                'task_detail_log', 'bot_master_log', 'bin_info_master_log'
            ]):
                print(f"\n✅ PASS: Correctly used CURRENT table")
                return True
            elif any(log_table in sql_lower for log_table in [
                'task_detail_log', 'bot_master_log'
            ]):
                print(f"\n❌ FAIL: Used LOG table instead of CURRENT table")
                print(f"   Should use: current state tables for active/ongoing queries")
                return False
            else:
                print(f"\n⚠️ UNCERTAIN: Could not determine table type from SQL")
                return False
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

def main():
    """Run temporal classification tests"""
    print("\n" + "="*80)
    print("  TEMPORAL TABLE CLASSIFICATION TEST SUITE")
    print("  Testing: Historical queries → log tables, Current queries → current tables")
    print("="*80)
    
    # Check server
    try:
        requests.get(f"{BASE_URL}/health", timeout=5)
        print("✅ Server connected")
    except:
        print("❌ Server not available. Start with: .\\quick_start.py")
        return
    
    test_cases = [
        # HISTORICAL queries (should use LOG tables)
        {
            "query": "can you give me all the task BOT-0010 this bot has performed till now",
            "expected": "LOG",
            "description": "Historical - All tasks performed till now"
        },
        {
            "query": "check the log and tell me what tasks bot BOT-0023 have done",
            "expected": "LOG",
            "description": "Historical - Explicit log check"
        },
        {
            "query": "show me all tasks that were completed yesterday",
            "expected": "LOG",
            "description": "Historical - Past tense 'were completed'"
        },
        {
            "query": "how many tasks has bot BOT-0015 completed since last week",
            "expected": "LOG",
            "description": "Historical - Time range with 'has completed'"
        },
        {
            "query": "give me the complete history of tasks for BOT-0020",
            "expected": "LOG",
            "description": "Historical - Explicit 'complete history'"
        },
        
        # CURRENT queries (should use CURRENT tables)
        {
            "query": "what task is BOT-0023 doing now",
            "expected": "CURRENT",
            "description": "Current - What is bot doing NOW"
        },
        {
            "query": "show me current tasks assigned to BOT-0023",
            "expected": "CURRENT",
            "description": "Current - Explicit 'current tasks'"
        },
        {
            "query": "which bots are currently active",
            "expected": "CURRENT",
            "description": "Current - Present tense 'are currently active'"
        },
        {
            "query": "give me all the tasks assigned to BOT-0010 right now",
            "expected": "CURRENT",
            "description": "Current - Explicit 'right now'"
        },
        {
            "query": "what is the latest task for BOT-0025",
            "expected": "CURRENT",
            "description": "Current - 'latest' indicates most recent active"
        }
    ]
    
    results = []
    for test_case in test_cases:
        result = test_query(
            test_case["query"],
            test_case["expected"],
            test_case["description"]
        )
        results.append({
            "description": test_case["description"],
            "expected": test_case["expected"],
            "passed": result
        })
    
    # Print summary
    print("\n" + "="*80)
    print("  TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results if r["passed"])
    failed = len(results) - passed
    
    print(f"\n✅ Passed: {passed}/{len(results)}")
    print(f"❌ Failed: {failed}/{len(results)}")
    
    if failed > 0:
        print("\n❌ Failed Tests:")
        for r in results:
            if not r["passed"]:
                print(f"   • {r['description']} (Expected: {r['expected']})")
    
    if passed == len(results):
        print("\n🎉 ALL TESTS PASSED - Temporal classification working correctly!")
    else:
        print("\n⚠️ Some tests failed - Review temporal classification logic")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
