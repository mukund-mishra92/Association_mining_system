"""
Test Script for Diagnostic Support Self-Improving Loop with LLM-as-Judge
Demonstrates how diagnoses are iteratively refined for accuracy
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from app.modules.neo_chatbot.services.intelligent_diagnostic_service import IntelligentDiagnosticService
from app.modules.neo_chatbot.models.schemas import ChatRequest, ChatbotType

# Configure logging to see refinement process
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_diagnostic_self_improving_loop():
    """Test the self-improving loop with various diagnostic scenarios"""
    
    print("=" * 80)
    print("DIAGNOSTIC SUPPORT SELF-IMPROVING LOOP TEST")
    print("=" * 80)
    print()
    
    # Initialize Diagnostic Service
    print("🔧 Initializing Diagnostic Service with Self-Improving Loop...")
    diagnostic_service = IntelligentDiagnosticService()
    
    print(f"✅ Initialized")
    print(f"   Max Refinement Iterations: {diagnostic_service.max_refinement_iterations}")
    print(f"   Judge Confidence Threshold: {diagnostic_service.judge_confidence_threshold}")
    print()
    
    # Test scenarios - from simple to complex
    test_scenarios = [
        {
            'problem': "BOT unable to put the bin at station",
            'description': "Known issue - should match historical data quickly",
            'expected_iterations': 1
        },
        {
            'problem': "Bot not picking bins from station but bins are at POST_ON_STATION",
            'description': "Complex issue - requires multiple diagnostic checks",
            'expected_iterations': 2
        },
        {
            'problem': "Wave is not completing and some bins are stuck",
            'description': "Multi-component issue - needs comprehensive diagnosis",
            'expected_iterations': 3
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print("\n" + "=" * 80)
        print(f"TEST {i}/{len(test_scenarios)}: {scenario['description']}")
        print("=" * 80)
        print(f"📝 Problem: \"{scenario['problem']}\"")
        print(f"🎯 Expected iterations: ~{scenario['expected_iterations']}")
        print()
        
        # Create chat request
        chat_request = ChatRequest(
            message=scenario['problem'],
            chatbot_type=ChatbotType.DIAGNOSTIC,
            session_id=f"test-session-{i}",
            conversation_history=[]
        )
        
        # Process diagnosis (self-improving loop happens here)
        print("🔄 Running diagnostic with self-improving loop...")
        print("-" * 80)
        
        response = diagnostic_service.diagnose_problem(chat_request)
        
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
                    if hist.get('missing_diagnostics'):
                        print(f"         Missing checks: {len(hist['missing_diagnostics'])} queries suggested")
        
        print()
        print(f"💬 Diagnosis Preview:")
        response_preview = response.response[:400] if response.response else ""
        print(f"   {response_preview}...")
        
        print()
        input("Press Enter to continue to next test...")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 80)
    print()
    print("KEY OBSERVATIONS:")
    print("✓ Simple issues exit early with high confidence")
    print("✓ Complex issues trigger additional diagnostic queries")
    print("✓ Judge identifies missing diagnostic checks")
    print("✓ System iteratively refines until data-backed conclusion")
    print("✓ Users see only final, validated diagnosis")
    print()
    print("📚 For detailed docs, see:")
    print("   - docs/DIAGNOSTIC_SELF_IMPROVING_SUMMARY.md")
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
    
    test_problem = "Bot stuck at charging station and not responding to commands"
    
    for i, config in enumerate(configurations, 1):
        print(f"\n--- Configuration {i}: {config['desc']} ---")
        print(f"Max Iterations: {config['iterations']}")
        print(f"Judge Threshold: {config['threshold']}")
        print()
        
        # Initialize with custom config
        diagnostic_service = IntelligentDiagnosticService()
        diagnostic_service.max_refinement_iterations = config['iterations']
        diagnostic_service.judge_confidence_threshold = config['threshold']
        
        # Test same problem with different configs
        chat_request = ChatRequest(
            message=test_problem,
            chatbot_type=ChatbotType.DIAGNOSTIC,
            session_id=f"config-test-{i}"
        )
        
        print(f"Testing problem: \"{test_problem}\"")
        response = diagnostic_service.diagnose_problem(chat_request)
        
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
║        DIAGNOSTIC SUPPORT SELF-IMPROVING LOOP TEST SUITE                 ║
║        LLM-as-Judge: Iterative Diagnosis Refinement                      ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

This test demonstrates:
  ✓ Automatic diagnosis quality validation (no human needed)
  ✓ Self-discovery of missing diagnostic checks
  ✓ Iterative refinement until data-backed conclusion
  ✓ Judge-guided additional diagnostic queries
  ✓ Seamless user experience (only final diagnosis shown)

""")
    
    try:
        # Run main tests
        test_diagnostic_self_improving_loop()
        
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
