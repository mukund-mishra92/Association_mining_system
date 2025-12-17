"""Test intelligent diagnostic service"""
import sys
import traceback

try:
    print("Testing Intelligent Diagnostic Service...")
    print("=" * 60)
    
    # Test import
    print("\n1. Testing imports...")
    from app.modules.neo_chatbot.services.intelligent_diagnostic_service import IntelligentDiagnosticService
    from app.modules.neo_chatbot.models.schemas import ChatRequest
    print("   OK - Imports successful")
    
    # Test initialization
    print("\n2. Testing service initialization...")
    service = IntelligentDiagnosticService()
    print("   OK - Service initialized")
    
    # Test problem analysis
    print("\n3. Testing problem analysis...")
    problem = "bot not responding to commands"
    analysis = service._analyze_problem_description(problem)
    print(f"   Analysis: {analysis}")
    print("   OK - Problem analysis works")
    
    # Test diagnostic query generation
    print("\n4. Testing query generation...")
    queries = service._generate_diagnostic_queries(analysis, [])
    print(f"   Generated {len(queries)} queries")
    print("   OK - Query generation works")
    
    # Test full diagnosis
    print("\n5. Testing full diagnosis...")
    chat_request = ChatRequest(
        message="bot not responding to commands",
        chatbot_type="diagnostic",  # Fixed: use 'diagnostic' not 'diagnostic_support'
        session_id="test-session"
    )
    
    response = service.diagnose_problem(chat_request)
    print(f"   Response length: {len(response.response)} chars")
    print(f"   Confidence: {response.confidence_score}")
    print("   OK - Full diagnosis works")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
    
    # Save response to file (avoid emoji encoding issues)
    with open("diagnostic_test_response.txt", "w", encoding="utf-8") as f:
        f.write(response.response)
    
    print("\nResponse saved to: diagnostic_test_response.txt")
    print(f"Response length: {len(response.response)} characters")
    print(f"Confidence: {response.confidence_score}")

except Exception as e:
    print(f"\nERROR: {e}")
    print("\nFull Traceback:")
    traceback.print_exc()
    sys.exit(1)
