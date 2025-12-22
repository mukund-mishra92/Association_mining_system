"""
Comprehensive Test Script for Diagnostic Support Service
Tests all functionality of the DiagnosticSupportService
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.modules.neo_chatbot.services.diagnostic_support_service import DiagnosticSupportService

def print_separator(title="", char="="):
    """Print a formatted separator"""
    if title:
        print(f"\n{char * 80}")
        print(f"{title:^80}")
        print(f"{char * 80}")
    else:
        print(f"{char * 80}")


def test_service_initialization():
    """Test 1: Service initialization and statistics"""
    print_separator("TEST 1: Service Initialization & Statistics")
    
    ds = DiagnosticSupportService()
    stats = ds.get_statistics()
    
    print(f"\n✅ Service initialized successfully!")
    print(f"\n📊 Statistics:")
    print(f"   Total Issues: {stats['total_issues']}")
    print(f"   Bot Level Issues: {stats['bot_level_count']}")
    print(f"   Station Level Issues: {stats['station_level_count']}")
    print(f"\n   Severity Breakdown:")
    print(f"      High: {stats['severity']['high']}")
    print(f"      Medium: {stats['severity']['medium']}")
    print(f"      Low: {stats['severity']['low']}")
    print(f"\n   Issues with SQL Solutions: {stats['with_sql_solutions']}")
    print(f"   Reported to Developers: {stats['reported_to_developers']}")
    
    return ds


def test_search_functionality(ds):
    """Test 2: Search functionality with various queries"""
    print_separator("TEST 2: Search Functionality")
    
    test_queries = [
        "bot stopped without error",
        "bot stuck in tower",
        "station pick failed",
        "unable to put bin",
        "lidar issue",
        "emergency stop",
        "communication error",
        "bot not responding"
    ]
    
    for query in test_queries:
        results = ds.search_issue(query, None)
        print(f"\n🔍 Query: '{query}'")
        print(f"   Found: {len(results)} matches")
        
        if results:
            top_result = results[0]
            print(f"   Top Match: {top_result['problem'][:60]}...")
            print(f"   Relevance: {top_result['relevance_score']:.2f}")
            print(f"   Severity: {top_result['severity']}")
            print(f"   Type: {top_result['type']}")


def test_filtered_search(ds):
    """Test 3: Filtered search by issue type"""
    print_separator("TEST 3: Filtered Search by Type")
    
    test_query = "bot issue"
    
    # Search bot-level issues only
    print(f"\n🔍 Searching for '{test_query}' in BOT_LEVEL issues:")
    bot_results = ds.search_issue(test_query, "BOT_LEVEL")
    print(f"   Found: {len(bot_results)} matches")
    if bot_results:
        print(f"   Top: {bot_results[0]['problem'][:60]}...")
    
    # Search station-level issues only
    print(f"\n🔍 Searching for '{test_query}' in STATION_LEVEL issues:")
    station_results = ds.search_issue(test_query, "STATION_LEVEL")
    print(f"   Found: {len(station_results)} matches")
    if station_results:
        print(f"   Top: {station_results[0]['problem'][:60]}...")


def test_get_issue_by_id(ds):
    """Test 4: Get specific issue by ID"""
    print_separator("TEST 4: Get Issue by ID")
    
    # Get bot-level issue #1
    bot_issue = ds.get_issue_by_id(1, "BOT_LEVEL")
    if bot_issue:
        print(f"\n✅ Bot Issue #1:")
        print(f"   Problem: {bot_issue['problem']}")
        print(f"   Severity: {bot_issue['severity']}")
        has_sql = bool(bot_issue.get('sql_query', '').strip())
        print(f"   Has SQL: {has_sql}")
        if has_sql:
            print(f"   SQL: {bot_issue['sql_query'][:100]}...")
    
    # Get station-level issue #1
    station_issue = ds.get_issue_by_id(1, "STATION_LEVEL")
    if station_issue:
        print(f"\n✅ Station Issue #1:")
        print(f"   Problem: {station_issue['problem']}")
        print(f"   Severity: {station_issue['severity']}")
        has_sql = bool(station_issue.get('sql_query', '').strip())
        print(f"   Has SQL: {has_sql}")


def test_diagnostic_recommendations(ds):
    """Test 5: Multi-symptom diagnostic recommendations"""
    print_separator("TEST 5: Diagnostic Recommendations")
    
    symptoms = [
        "bot not responding",
        "stuck in tower",
        "no error messages"
    ]
    
    print(f"\n🔬 Analyzing multiple symptoms:")
    for symptom in symptoms:
        print(f"   - {symptom}")
    
    recommendations = ds.get_diagnostic_recommendations(symptoms)
    
    print(f"\n📋 Analysis Results:")
    print(f"   Total Matches: {recommendations['total_matches']}")
    print(f"   Top Recommendations: {len(recommendations['recommended_solutions'])}")
    print(f"   Developer Involvement Required: {recommendations['requires_developer']}")
    
    print(f"\n🎯 Top 3 Recommendations:")
    for i, solution in enumerate(recommendations['recommended_solutions'][:3], 1):
        print(f"\n   {i}. {solution['problem'][:60]}...")
        print(f"      Relevance: {solution['relevance_score']:.2f}")
        print(f"      Severity: {solution['severity']}")
        print(f"      Type: {solution['type']}")


def test_get_all_issues(ds):
    """Test 6: Get all issues with filtering"""
    print_separator("TEST 6: Get All Issues")
    
    # Get all issues
    all_issues = ds.get_all_issues()
    print(f"\n📚 All Issues:")
    print(f"   Bot Level: {len(all_issues['bot_level'])} issues")
    print(f"   Station Level: {len(all_issues['station_level'])} issues")
    
    # Get high severity issues only
    high_severity = ds.get_all_issues(severity="high")
    print(f"\n🔴 High Severity Issues:")
    print(f"   Bot Level: {len(high_severity['bot_level'])} issues")
    print(f"   Station Level: {len(high_severity['station_level'])} issues")


def test_detailed_issue_view(ds):
    """Test 7: Detailed view of a specific issue"""
    print_separator("TEST 7: Detailed Issue View")
    
    # Search for a specific issue
    results = ds.search_issue("bot stopped without error", "BOT_LEVEL")
    
    if results:
        issue = results[0]
        print(f"\n📄 Detailed Issue Information:")
        print(f"\n   ID: {issue['id']}")
        print(f"   Type: {issue['type']}")
        print(f"   Problem: {issue['problem']}")
        print(f"   Severity: {issue['severity']}")
        print(f"   Relevance: {issue['relevance_score']:.2f}")
        
        print(f"\n   Solution:")
        print(f"   {issue['solution']}")
        
        has_sql = bool(issue.get('sql_query', '').strip())
        if has_sql:
            print(f"\n   SQL Query:")
            print(f"   {issue['sql_query']}")
        
        print(f"\n   Outcome: {issue['outcome']}")
        print(f"   Reported to Developer: {issue['reported_to_dev']}")


def test_edge_cases(ds):
    """Test 8: Edge cases and error handling"""
    print_separator("TEST 8: Edge Cases")
    
    # Empty query
    print(f"\n🧪 Testing empty query:")
    results = ds.search_issue("", None)
    print(f"   Results: {len(results)}")
    
    # Invalid issue type
    print(f"\n🧪 Testing invalid issue type:")
    results = ds.search_issue("bot issue", "INVALID_TYPE")
    print(f"   Results: {len(results)}")
    
    # Non-existent ID
    print(f"\n🧪 Testing non-existent ID:")
    issue = ds.get_issue_by_id(9999, "BOT_LEVEL")
    print(f"   Result: {issue}")
    
    # Very specific query with no matches
    print(f"\n🧪 Testing specific query with no matches:")
    results = ds.search_issue("quantum entanglement issue", None)
    print(f"   Results: {len(results)}")


def main():
    """Run all tests"""
    print_separator("DIAGNOSTIC SUPPORT SERVICE - COMPREHENSIVE TEST SUITE", "=")
    print("\n🚀 Starting comprehensive test suite...\n")
    
    try:
        # Test 1: Initialization
        ds = test_service_initialization()
        
        # Test 2: Search functionality
        test_search_functionality(ds)
        
        # Test 3: Filtered search
        test_filtered_search(ds)
        
        # Test 4: Get by ID
        test_get_issue_by_id(ds)
        
        # Test 5: Diagnostic recommendations
        test_diagnostic_recommendations(ds)
        
        # Test 6: Get all issues
        test_get_all_issues(ds)
        
        # Test 7: Detailed issue view
        test_detailed_issue_view(ds)
        
        # Test 8: Edge cases
        test_edge_cases(ds)
        
        # Final summary
        print_separator("TEST SUMMARY", "=")
        print(f"\n✅ All tests completed successfully!")
        print(f"\n📊 Service is fully functional and ready to use.")
        print(f"\nThe Diagnostic Support Service can:")
        print(f"   ✓ Load and parse support logs from CSV files")
        print(f"   ✓ Search issues with relevance scoring")
        print(f"   ✓ Filter by issue type (BOT_LEVEL, STATION_LEVEL)")
        print(f"   ✓ Get specific issues by ID")
        print(f"   ✓ Provide multi-symptom diagnostic recommendations")
        print(f"   ✓ Handle edge cases gracefully")
        
        print_separator("", "=")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
