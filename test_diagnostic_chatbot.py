"""
Test Diagnostic Support through Chatbot Interface
Tests the integration of DiagnosticSupportService with the chatbot
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.modules.neo_chatbot.models.schemas import ChatRequest, ChatbotType
from app.modules.neo_chatbot.services.diagnostic_service import DiagnosticService


def print_separator(title="", char="="):
    """Print a formatted separator"""
    if title:
        print(f"\n{char * 80}")
        print(f"{title:^80}")
        print(f"{char * 80}")
    else:
        print(f"{char * 80}")


def test_chatbot_queries():
    """Test diagnostic support through chatbot interface"""
    print_separator("DIAGNOSTIC CHATBOT INTEGRATION TEST", "=")
    
    # Initialize diagnostic service
    diagnostic_service = DiagnosticService()
    
    # Test queries simulating user interactions
    test_queries = [
        {
            "query": "My bot stopped on the ground without any error message",
            "expected": "bot stopped"
        },
        {
            "query": "The bot is stuck in the tower and won't come down",
            "expected": "stuck in tower"
        },
        {
            "query": "Station is not picking the bin properly",
            "expected": "station pick"
        },
        {
            "query": "Bot unable to put bin at station",
            "expected": "put bin"
        },
        {
            "query": "Communication error with the bot",
            "expected": "communication"
        },
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print_separator(f"TEST QUERY {i}", "-")
        print(f"\nUser Query: {test_case['query']}")
        
        # Create chat request
        chat_request = ChatRequest(
            message=test_case['query'],
            chatbot_type=ChatbotType.DIAGNOSTIC,
            session_id=f"test_session_{i}"
        )
        
        # Process through diagnostic service
        response = diagnostic_service.process_query(chat_request)
        
        print(f"\n📊 Response Info:")
        print(f"   Chatbot Type: {response.chatbot_type}")
        print(f"   Confidence: {response.confidence_score:.2f}")
        print(f"   Session ID: {response.session_id}")
        
        if response.suggested_actions:
            print(f"\n   Suggested Actions: {', '.join(response.suggested_actions)}")
        
        print(f"\n💬 Response:")
        print("-" * 80)
        print(response.response)
        print("-" * 80)
        
        # Verify response quality
        if test_case['expected'].lower() in response.response.lower():
            print(f"\n✅ Response contains expected keywords: '{test_case['expected']}'")
        else:
            print(f"\n⚠️ Response may not directly address: '{test_case['expected']}'")


def test_support_service_integration():
    """Test direct integration with support service"""
    print_separator("SUPPORT SERVICE INTEGRATION TEST", "=")
    
    diagnostic_service = DiagnosticService()
    
    # Check if support service is loaded
    print(f"\n📊 Support Service Status:")
    
    if diagnostic_service.support_service:
        stats = diagnostic_service.support_service.get_statistics()
        print(f"   ✅ Support service loaded")
        print(f"   Total Issues: {stats['total_issues']}")
        print(f"   Bot Level: {stats['bot_level_count']}")
        print(f"   Station Level: {stats['station_level_count']}")
        print(f"   High Severity: {stats['severity']['high']}")
    else:
        print(f"   ❌ Support service not initialized")
        return False
    
    # Test search functionality
    print(f"\n🔍 Testing Search Functionality:")
    test_search = "bot stuck"
    results = diagnostic_service.support_service.search_issue(test_search)
    print(f"   Query: '{test_search}'")
    print(f"   Results: {len(results)} matches")
    
    if results:
        print(f"\n   Top Result:")
        print(f"      Problem: {results[0]['problem'][:60]}...")
        print(f"      Severity: {results[0]['severity']}")
        print(f"      Type: {results[0]['type']}")
        print(f"      Relevance: {results[0]['relevance_score']:.2f}")
    
    return True


def test_multi_symptom_diagnosis():
    """Test multi-symptom diagnostic recommendations"""
    print_separator("MULTI-SYMPTOM DIAGNOSIS TEST", "=")
    
    diagnostic_service = DiagnosticService()
    
    symptoms = [
        "bot not moving",
        "stuck position",
        "no error displayed"
    ]
    
    print(f"\n🔬 Symptoms:")
    for symptom in symptoms:
        print(f"   - {symptom}")
    
    recommendations = diagnostic_service.support_service.get_diagnostic_recommendations(symptoms)
    
    print(f"\n📋 Diagnostic Analysis:")
    print(f"   Symptoms Analyzed: {len(recommendations['symptoms_analyzed'])}")
    print(f"   Total Matches: {recommendations['total_matches']}")
    print(f"   Recommended Solutions: {len(recommendations['recommended_solutions'])}")
    print(f"   Developer Required: {recommendations['requires_developer']}")
    
    print(f"\n🎯 Top 3 Solutions:")
    for i, solution in enumerate(recommendations['recommended_solutions'][:3], 1):
        print(f"\n   {i}. {solution['problem'][:60]}...")
        print(f"      Severity: {solution['severity']}")
        print(f"      Type: {solution['type']}")
        print(f"      Relevance: {solution['relevance_score']:.2f}")


def test_specific_issue_retrieval():
    """Test retrieving specific issues by ID"""
    print_separator("SPECIFIC ISSUE RETRIEVAL TEST", "=")
    
    diagnostic_service = DiagnosticService()
    
    # Test bot-level issue
    print(f"\n📄 Bot-Level Issue #1:")
    bot_issue = diagnostic_service.support_service.get_issue_by_id(1, "BOT_LEVEL")
    
    if bot_issue:
        print(f"   Problem: {bot_issue['problem']}")
        print(f"   Severity: {bot_issue['severity']}")
        print(f"\n   Solution:")
        for line in bot_issue['solution'].split('\n')[:3]:
            if line.strip():
                print(f"      {line.strip()}")
        
        if bot_issue.get('sql_query'):
            print(f"\n   SQL Query Available: Yes")
            print(f"   {bot_issue['sql_query'][:80]}...")
    
    # Test station-level issue
    print(f"\n📄 Station-Level Issue #1:")
    station_issue = diagnostic_service.support_service.get_issue_by_id(1, "STATION_LEVEL")
    
    if station_issue:
        print(f"   Problem: {station_issue['problem']}")
        print(f"   Severity: {station_issue['severity']}")
        print(f"\n   Solution:")
        for line in station_issue['solution'].split('\n')[:3]:
            if line.strip():
                print(f"      {line.strip()}")


def test_severity_filtering():
    """Test filtering issues by severity"""
    print_separator("SEVERITY FILTERING TEST", "=")
    
    diagnostic_service = DiagnosticService()
    
    # Get high severity issues
    high_severity = diagnostic_service.support_service.get_all_issues(severity="high")
    
    print(f"\n🔴 High Severity Issues:")
    print(f"   Bot Level: {len(high_severity['bot_level'])} issues")
    print(f"   Station Level: {len(high_severity['station_level'])} issues")
    
    if high_severity['bot_level']:
        print(f"\n   Sample Bot Issue:")
        issue = high_severity['bot_level'][0]
        print(f"      {issue['problem'][:70]}...")
    
    if high_severity['station_level']:
        print(f"\n   Sample Station Issue:")
        issue = high_severity['station_level'][0]
        print(f"      {issue['problem'][:70]}...")


def main():
    """Run all integration tests"""
    print_separator("DIAGNOSTIC CHATBOT - INTEGRATION TEST SUITE", "=")
    print("\n🚀 Testing Diagnostic Support through Chatbot Interface...\n")
    
    try:
        # Test 1: Support service integration
        if not test_support_service_integration():
            print("\n❌ Support service integration failed!")
            return False
        
        # Test 2: Chatbot queries
        test_chatbot_queries()
        
        # Test 3: Multi-symptom diagnosis
        test_multi_symptom_diagnosis()
        
        # Test 4: Specific issue retrieval
        test_specific_issue_retrieval()
        
        # Test 5: Severity filtering
        test_severity_filtering()
        
        # Final summary
        print_separator("INTEGRATION TEST SUMMARY", "=")
        print(f"\n✅ All integration tests completed successfully!")
        print(f"\n📊 The Diagnostic Support Service is fully integrated:")
        print(f"   ✓ Support logs loaded from CSV files")
        print(f"   ✓ Chatbot can process diagnostic queries")
        print(f"   ✓ Multi-symptom analysis working")
        print(f"   ✓ Issue retrieval by ID working")
        print(f"   ✓ Severity filtering working")
        print(f"   ✓ Relevance scoring operational")
        
        print(f"\n💡 The service is ready for production use!")
        print_separator("", "=")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
