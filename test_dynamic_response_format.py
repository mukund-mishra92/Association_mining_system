"""
Test Dynamic Response Formatting in Diagnostic Support
Demonstrates how the system adapts response format based on user intent
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.modules.neo_chatbot.services.intelligent_diagnostic_service import IntelligentDiagnosticService
from app.modules.neo_chatbot.models.schemas import ChatRequest, ChatbotType

def test_different_intents():
    """Test various question types to show dynamic formatting"""
    
    service = IntelligentDiagnosticService()
    
    test_cases = [
        {
            "query": "why you are giving only one task. is this only one task assigned to this bot_id till now",
            "expected_intent": "DATA_QUERY",
            "description": "Should show query results in table format, not full diagnostic"
        },
        {
            "query": "what is your criteria to check the active bots",
            "expected_intent": "EXPLAIN_CRITERIA",
            "description": "Should explain the SQL logic and criteria, not diagnose a problem"
        },
        {
            "query": "why bots are not coming to the station",
            "expected_intent": "TROUBLESHOOT",
            "description": "Should provide full diagnostic: Root Cause → What I Found → Solution"
        },
        {
            "query": "show me the SQL query you use to check bot status",
            "expected_intent": "SHOW_QUERY",
            "description": "Should display the actual SQL query with explanation"
        },
        {
            "query": "what should I check to prevent bots getting stuck",
            "expected_intent": "RECOMMENDATION",
            "description": "Should provide recommendations and best practices"
        }
    ]
    
    print("=" * 80)
    print("TESTING DYNAMIC RESPONSE FORMATTING")
    print("=" * 80)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {i}: {test['expected_intent']}")
        print(f"{'=' * 80}")
        print(f"Query: {test['query']}")
        print(f"Expected Behavior: {test['description']}")
        print(f"\n{'-' * 80}")
        
        # Classify intent (without full execution)
        intent = service._classify_user_intent(test['query'])
        
        print(f"\n🎯 INTENT CLASSIFICATION:")
        print(f"   Type: {intent['intent_type']}")
        print(f"   Response Style: {intent['response_style']}")
        print(f"   Show SQL Query: {intent['show_sql_query']}")
        print(f"   Show Data Table: {intent['show_data_table']}")
        print(f"   Show Analysis: {intent['show_analysis']}")
        print(f"   Show Solution: {intent['show_solution']}")
        print(f"   Reasoning: {intent['reasoning']}")
        
        match_status = "✅ CORRECT" if intent['intent_type'] == test['expected_intent'] else "❌ MISMATCH"
        print(f"\n{match_status}")
        
        if intent['intent_type'] != test['expected_intent']:
            print(f"   Expected: {test['expected_intent']}, Got: {intent['intent_type']}")
    
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print("=" * 80)
    print("""
The diagnostic system now:
1. Classifies user intent FIRST before generating response
2. Adapts output format based on what user actually wants:
   - DATA_QUERY: Shows data in table/list format
   - EXPLAIN_CRITERIA: Explains how system checks/determines things
   - SHOW_QUERY: Displays actual SQL queries used
   - RECOMMENDATION: Provides advice and best practices
   - TROUBLESHOOT: Full diagnostic (Root Cause → Solution)
3. No longer forces the same format for every question
4. More natural and contextually appropriate responses
    """)

if __name__ == "__main__":
    test_different_intents()
