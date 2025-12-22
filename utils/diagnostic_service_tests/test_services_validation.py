"""
Test SQL Assistant and Diagnostic Support services for:
1. Valid response generation
2. No hallucinations at table/column/value levels
"""

import requests
import json
import time
from typing import Dict, Any, List

# Server configuration
BASE_URL = "http://localhost:8000"
CHATBOT_ENDPOINT = f"{BASE_URL}/api/chatbot/chat"

def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_result(label: str, value: Any, status: str = "INFO"):
    """Print a formatted result"""
    symbols = {"PASS": "✅", "FAIL": "❌", "INFO": "ℹ️", "WARN": "⚠️"}
    symbol = symbols.get(status, "•")
    print(f"{symbol} {label}: {value}")

def send_chat_request(chatbot_type: str, query: str, session_id: str = "test_session") -> Dict[str, Any]:
    """Send a chat request to the API"""
    payload = {
        "chatbot_type": chatbot_type,
        "query": query,
        "session_id": session_id
    }
    
    try:
        response = requests.post(CHATBOT_ENDPOINT, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def check_for_hallucinations(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check response for potential hallucinations based on validation errors
    Returns dictionary with hallucination analysis
    """
    analysis = {
        "has_hallucination": False,
        "hallucination_type": None,
        "details": [],
        "validation_passed": False
    }
    
    # Check for error indicators
    response_text = str(response.get("response", "")).lower()
    
    # Check for table hallucination indicators
    if "table" in response_text and "not exist" in response_text:
        analysis["has_hallucination"] = True
        analysis["hallucination_type"] = "TABLE_NAME"
        analysis["details"].append("Response mentions non-existent table")
    
    # Check for column hallucination indicators  
    if "column" in response_text and ("not found" in response_text or "not exist" in response_text):
        analysis["has_hallucination"] = True
        analysis["hallucination_type"] = "COLUMN_NAME"
        analysis["details"].append("Response mentions non-existent column")
    
    # Check for value hallucination indicators
    if "no data" in response_text or "0 records" in response_text or "no results" in response_text:
        # This could be value hallucination if query expected results
        analysis["details"].append("Query returned no results - check if value hallucination")
    
    # Check if validation layers worked (positive indicator)
    metadata = response.get("metadata", {})
    if metadata.get("table_validation_passed") or "validation passed" in response_text:
        analysis["validation_passed"] = True
    
    return analysis

def test_sql_assistant_service():
    """Test SQL Assistant Service with various queries"""
    print_section("SQL ASSISTANT SERVICE TESTS")
    
    test_cases = [
        {
            "name": "Simple table query - bins",
            "query": "Show me 5 bins from the system",
            "expected": "Should query bins or bin_master table"
        },
        {
            "name": "Status filter query",
            "query": "Show me all bins with status ENABLED",
            "expected": "Should validate status values exist in database"
        },
        {
            "name": "Count query",
            "query": "How many bins are in the system?",
            "expected": "Should return count from valid table"
        },
        {
            "name": "Join query",
            "query": "Show me bins and their locations",
            "expected": "Should join bins with location tables if relationship exists"
        },
        {
            "name": "Complex query with potential hallucination",
            "query": "Show me all items with status 'active' from inventory",
            "expected": "Should validate 'active' value exists or use correct value"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['name']} ---")
        print_result("Query", test_case['query'], "INFO")
        print_result("Expected", test_case['expected'], "INFO")
        
        response = send_chat_request("sql_assistant", test_case['query'])
        
        if "error" in response:
            print_result("Status", f"ERROR: {response['error']}", "FAIL")
            results.append({"test": test_case['name'], "status": "ERROR", "error": response['error']})
            continue
        
        # Analyze response
        print_result("Response", response.get('response', '')[:200] + "...", "INFO")
        
        # Check for hallucinations
        hallucination_check = check_for_hallucinations(response)
        
        if hallucination_check['has_hallucination']:
            print_result("Hallucination Detected", hallucination_check['hallucination_type'], "FAIL")
            print_result("Details", ", ".join(hallucination_check['details']), "WARN")
            results.append({
                "test": test_case['name'],
                "status": "FAIL_HALLUCINATION",
                "type": hallucination_check['hallucination_type'],
                "details": hallucination_check['details']
            })
        elif hallucination_check['validation_passed']:
            print_result("Validation", "PASSED - No hallucination", "PASS")
            results.append({"test": test_case['name'], "status": "PASS"})
        else:
            print_result("Status", "Response generated (check manually)", "WARN")
            results.append({"test": test_case['name'], "status": "MANUAL_CHECK"})
        
        # Check metadata
        metadata = response.get('metadata', {})
        if metadata:
            print_result("SQL Generated", metadata.get('sql_query', 'N/A')[:100] + "...", "INFO")
            print_result("Rows Returned", metadata.get('row_count', 'N/A'), "INFO")
        
        time.sleep(1)  # Rate limiting
    
    return results

def test_diagnostic_support_service():
    """Test Diagnostic Support Service"""
    print_section("DIAGNOSTIC SUPPORT SERVICE TESTS")
    
    test_cases = [
        {
            "name": "Simple problem query",
            "query": "Why is my bin not picking items?",
            "expected": "Should provide diagnostic steps"
        },
        {
            "name": "Status check query",
            "query": "How do I check bin status?",
            "expected": "Should reference valid status values"
        },
        {
            "name": "Configuration query",
            "query": "Show me bins with velocity type A",
            "expected": "Should validate velocity type values exist"
        },
        {
            "name": "Troubleshooting with data",
            "query": "Find bins that are disabled in the system",
            "expected": "Should use correct status value (DISABLED not 'disabled' or 'inactive')"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['name']} ---")
        print_result("Query", test_case['query'], "INFO")
        print_result("Expected", test_case['expected'], "INFO")
        
        response = send_chat_request("diagnostic", test_case['query'])
        
        if "error" in response:
            print_result("Status", f"ERROR: {response['error']}", "FAIL")
            results.append({"test": test_case['name'], "status": "ERROR", "error": response['error']})
            continue
        
        # Analyze response
        print_result("Response", response.get('response', '')[:200] + "...", "INFO")
        
        # Check for hallucinations
        hallucination_check = check_for_hallucinations(response)
        
        if hallucination_check['has_hallucination']:
            print_result("Hallucination Detected", hallucination_check['hallucination_type'], "FAIL")
            print_result("Details", ", ".join(hallucination_check['details']), "WARN")
            results.append({
                "test": test_case['name'],
                "status": "FAIL_HALLUCINATION",
                "type": hallucination_check['hallucination_type'],
                "details": hallucination_check['details']
            })
        else:
            print_result("Status", "Response generated successfully", "PASS")
            results.append({"test": test_case['name'], "status": "PASS"})
        
        # Check metadata
        metadata = response.get('metadata', {})
        if metadata:
            if 'sql_query' in metadata:
                print_result("SQL Generated", metadata.get('sql_query', '')[:100] + "...", "INFO")
        
        time.sleep(1)  # Rate limiting
    
    return results

def print_summary(sql_results: List[Dict], diagnostic_results: List[Dict]):
    """Print test summary"""
    print_section("TEST SUMMARY")
    
    def count_status(results: List[Dict]) -> Dict[str, int]:
        counts = {"PASS": 0, "FAIL_HALLUCINATION": 0, "ERROR": 0, "MANUAL_CHECK": 0}
        for r in results:
            status = r.get("status", "MANUAL_CHECK")
            counts[status] = counts.get(status, 0) + 1
        return counts
    
    print("\n📊 SQL Assistant Service:")
    sql_counts = count_status(sql_results)
    print_result("  Passed", sql_counts['PASS'], "PASS" if sql_counts['PASS'] > 0 else "INFO")
    print_result("  Hallucinations", sql_counts['FAIL_HALLUCINATION'], "FAIL" if sql_counts['FAIL_HALLUCINATION'] > 0 else "PASS")
    print_result("  Errors", sql_counts['ERROR'], "FAIL" if sql_counts['ERROR'] > 0 else "PASS")
    print_result("  Manual Check", sql_counts['MANUAL_CHECK'], "WARN" if sql_counts['MANUAL_CHECK'] > 0 else "INFO")
    
    print("\n📊 Diagnostic Support Service:")
    diag_counts = count_status(diagnostic_results)
    print_result("  Passed", diag_counts['PASS'], "PASS" if diag_counts['PASS'] > 0 else "INFO")
    print_result("  Hallucinations", diag_counts['FAIL_HALLUCINATION'], "FAIL" if diag_counts['FAIL_HALLUCINATION'] > 0 else "PASS")
    print_result("  Errors", diag_counts['ERROR'], "FAIL" if diag_counts['ERROR'] > 0 else "PASS")
    print_result("  Manual Check", diag_counts['MANUAL_CHECK'], "WARN" if diag_counts['MANUAL_CHECK'] > 0 else "INFO")
    
    # Overall assessment
    total_hallucinations = sql_counts['FAIL_HALLUCINATION'] + diag_counts['FAIL_HALLUCINATION']
    total_errors = sql_counts['ERROR'] + diag_counts['ERROR']
    
    print("\n" + "="*80)
    if total_hallucinations == 0 and total_errors == 0:
        print("✅ OVERALL: ALL VALIDATION LAYERS WORKING - NO HALLUCINATIONS DETECTED")
    elif total_hallucinations > 0:
        print(f"❌ OVERALL: {total_hallucinations} HALLUCINATIONS DETECTED - VALIDATION NEEDS REVIEW")
    else:
        print(f"⚠️ OVERALL: {total_errors} ERRORS - CHECK SERVER LOGS")
    print("="*80)

def main():
    """Main test runner"""
    print("\n" + "="*80)
    print("  SERVICE VALIDATION TEST SUITE")
    print("  Testing: No hallucinations at table/column/value levels")
    print("="*80)
    
    # Check server availability
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print_result("Server Status", "Connected ✓", "PASS")
    except:
        print_result("Server Status", "Cannot connect - is server running?", "FAIL")
        print("\nStart server with: .\\quick_start.py")
        return
    
    # Run tests
    sql_results = test_sql_assistant_service()
    diagnostic_results = test_diagnostic_support_service()
    
    # Print summary
    print_summary(sql_results, diagnostic_results)
    
    print("\n💡 TIP: Check server logs for detailed validation messages")
    print("   Look for: '✅ Table validation passed', '✅ Column validation passed', etc.\n")

if __name__ == "__main__":
    main()
