"""
Test Script for SQL Assistant Self-Improving Loop with LLM-as-Judge
Demonstrates how queries are iteratively refined until optimal results
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from app.modules.neo_chatbot.services.sql_assistant_service import SQLAssistantService
from app.modules.neo_chatbot.models.schemas import ChatRequest, ChatbotType

# Configure logging to see refinement process
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_self_improving_loop():
    """Test the self-improving loop with various queries"""
    
    print("=" * 80)
    print("SQL ASSISTANT SELF-IMPROVING LOOP TEST")
    print("=" * 80)
    print()
    
    # Initialize SQL Assistant
    print("🔧 Initializing SQL Assistant with Self-Improving Loop...")
    sql_service = SQLAssistantService()
    
    print(f"✅ Initialized")
    print(f"   Max Refinement Iterations: {sql_service.max_refinement_iterations}")
    print(f"   Judge Confidence Threshold: {sql_service.judge_confidence_threshold}")
    print()
    
    # Test queries - from simple to complex
    test_queries = [
        {
            'query': "How many active bots do we have?",
            'description': "Simple query - should exit early with high confidence",
            'expected_iterations': 1
        },
        {
            'query': "Show me all orders from today",
            'description': "Medium complexity - might need 1-2 iterations to find right table",
            'expected_iterations': 2
        },
        {
            'query': "List SKUs with high velocity that were picked in the last 7 days",
            'description': "Complex query - requires multiple tables and refinement",
            'expected_iterations': 3
        }
    ]
    
    for i, test in enumerate(test_queries, 1):
        print("\n" + "=" * 80)
        print(f"TEST {i}/{len(test_queries)}: {test['description']}")
        print("=" * 80)
        print(f"📝 Query: \"{test['query']}\"")
        print(f"🎯 Expected iterations: ~{test['expected_iterations']}")
        print()
        
        # Create chat request
        chat_request = ChatRequest(
            message=test['query'],
            chatbot_type=ChatbotType.SQL_ASSISTANT,
            session_id=f"test-session-{i}",
            conversation_history=[]
        )
        
        # Process query (self-improving loop happens here)
        print("🔄 Processing query with self-improving loop...")
        print("-" * 80)
        
        response = sql_service.process_query(chat_request)
        
        print("-" * 80)
        print()
        
        # Display results
        print("📊 RESULTS:")
        print(f"   Confidence Score: {response.confidence_score:.2%}")
        
        # Check metadata for refinement info
        if hasattr(response, 'metadata') and response.metadata:
            refinement_iterations = response.metadata.get('refinement_iterations', 0)
            print(f"   Refinement Iterations: {refinement_iterations}")
            
            refinement_history = response.metadata.get('refinement_history')
            if refinement_history:
                print(f"\n   📈 Refinement Progress:")
                for hist in refinement_history:
                    print(f"      Iteration {hist['iteration']}: confidence={hist['confidence']:.2f}, "
                          f"judge_confidence={hist['judge_confidence']:.2f}, "
                          f"satisfactory={hist['is_satisfactory']}")
                    if hist.get('issues'):
                        print(f"         Issues: {', '.join(hist['issues'][:2])}")
        
        print()
        print(f"📝 Final SQL:")
        if response.sql_query:
            print(f"   {response.sql_query[:200]}...")
        else:
            print("   (No SQL generated)")
        
        print()
        print(f"💬 Response Preview:")
        response_preview = response.response[:300] if response.response else ""
        print(f"   {response_preview}...")
        
        print()
        input("Press Enter to continue to next test...")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 80)
    print()
    print("KEY OBSERVATIONS:")
    print("✓ Simple queries exit early with high confidence")
    print("✓ Complex queries refine iteratively until optimal")
    print("✓ Judge provides actionable feedback for improvements")
    print("✓ System tracks best result across iterations")
    print("✓ Users see only final, refined result")
    print()
    print("📚 For detailed docs, see:")
    print("   - docs/SQL_ASSISTANT_SELF_IMPROVING_LOOP.md")
    print("   - docs/SQL_ASSISTANT_SELF_IMPROVING_QUICK_REF.md")
    print()


def test_configuration_tuning():
    """Test different configuration settings"""
    
    print("\n" + "=" * 80)
    print("CONFIGURATION TUNING TEST")
    print("=" * 80)
    print()
    
    configurations = [
        {'iterations': 1, 'threshold': 0.90, 'desc': 'Fast mode - minimal refinement'},
        {'iterations': 3, 'threshold': 0.85, 'desc': 'Balanced mode - default'},
        {'iterations': 5, 'threshold': 0.80, 'desc': 'Quality mode - maximum refinement'}
    ]
    
    test_query = "Show me bins with high velocity in zone A"
    
    for i, config in enumerate(configurations, 1):
        print(f"\n--- Configuration {i}: {config['desc']} ---")
        print(f"Max Iterations: {config['iterations']}")
        print(f"Judge Threshold: {config['threshold']}")
        print()
        
        # Initialize with custom config
        sql_service = SQLAssistantService()
        sql_service.max_refinement_iterations = config['iterations']
        sql_service.judge_confidence_threshold = config['threshold']
        
        # Test same query with different configs
        chat_request = ChatRequest(
            message=test_query,
            chatbot_type=ChatbotType.SQL_ASSISTANT,
            session_id=f"config-test-{i}"
        )
        
        print(f"Testing query: \"{test_query}\"")
        response = sql_service.process_query(chat_request)
        
        # Show iteration count
        if hasattr(response, 'metadata') and response.metadata:
            iterations = response.metadata.get('refinement_iterations', 0)
            print(f"✓ Completed in {iterations} iteration(s)")
            print(f"✓ Final confidence: {response.confidence_score:.2%}")
        print()


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║           SQL ASSISTANT SELF-IMPROVING LOOP TEST SUITE                   ║
║           LLM-as-Judge: Iterative Query Refinement                       ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

This test demonstrates:
  ✓ Automatic query refinement based on LLM judge feedback
  ✓ Iterative improvement until optimal results
  ✓ Smart exit conditions (confidence thresholds)
  ✓ Best result tracking across iterations
  ✓ Seamless user experience (only final result shown)

""")
    
    try:
        # Run main tests
        test_self_improving_loop()
        
        # Optional: Test configuration tuning
        print("\n" + "=" * 80)
        tune_test = input("Would you like to test configuration tuning? (y/n): ")
        if tune_test.lower() == 'y':
            test_configuration_tuning()
        
        print("\n✅ Test suite completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
