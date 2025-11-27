"""
Test Accuracy Improvements - Compare Before/After
Tests the anti-hallucination and accuracy improvements
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.modules.neo_chatbot.services.agentic_service import get_agentic_service
from app.modules.neo_chatbot.models.schemas import ChatRequest

def test_query(service, query: str, test_name: str):
    """Test a single query and display results"""
    print("\n" + "="*80)
    print(f"TEST: {test_name}")
    print("="*80)
    print(f"Query: {query}\n")
    
    request = ChatRequest(
        message=query,
        session_id="accuracy_test",
        conversation_history=[]
    )
    
    try:
        response = service.process_query(request)
        
        # Display response
        print("RESPONSE:")
        print("-" * 80)
        print(response.response)
        print("-" * 80)
        
        # Display metadata
        if response.metadata:
            print(f"\nMETADATA:")
            print(f"  Format: {response.metadata.get('format_decision', 'N/A')}")
            print(f"  Workflow: {response.metadata.get('agent_workflow', 'N/A')}")
            print(f"  Verified: {response.metadata.get('verification_performed', False)}")
            print(f"  Confidence: {response.confidence_score}")
        
        # Check for quality indicators
        print(f"\nQUALITY INDICATORS:")
        has_citations = "Document" in response.response or "📄" in response.response
        has_specifics = any(term in response.response for term in ["24,000", "PPH", "Cross-Belt", "Siemens", "TCP/IP"])
        no_generic = not any(phrase in response.response.lower() for phrase in ["generally", "typically includes", "various types"])
        
        print(f"  Has Citations: {'YES' if has_citations else 'NO'}")
        print(f"  Has Specifics: {'YES' if has_specifics else 'NO'}")
        print(f"  Avoids Generic: {'YES' if no_generic else 'NO'}")
        print(f"  Sources: {len(response.sources)} documents")
        
        return response
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Run accuracy improvement tests"""
    
    print("="*80)
    print("NEO CHATBOT - ACCURACY IMPROVEMENT VALIDATION")
    print("="*80)
    print("\nThis test validates the anti-hallucination and accuracy improvements.")
    print("Expected: Specific, citation-backed answers without invented information.")
    
    # Initialize service
    print("\nInitializing agentic service...")
    service = get_agentic_service()
    
    if not service:
        print("ERROR: Could not initialize service")
        return
    
    print("Service initialized successfully\n")
    
    # Test cases that previously had issues
    test_cases = [
        {
            "name": "Types Question (Previously Hallucinated)",
            "query": "what are the different types of sorter services in our system",
            "check_for": ["Cross-Belt", "Document"],
            "check_against": ["Manual Sorter", "Automated Sorter", "Hybrid"]
        },
        {
            "name": "Definition Question",
            "query": "what is telescopic conveyor",
            "check_for": ["extendable", "retractable", "conveyor"],
            "check_against": ["generally", "typically"]
        },
        {
            "name": "Component Question",
            "query": "what sensors are used in sorter",
            "check_for": ["barcode", "scanner", "Document"],
            "check_against": ["various sensors", "generally includes"]
        },
        {
            "name": "Technical Specs Question",
            "query": "what is the throughput capacity of cross belt sorter",
            "check_for": ["24,000", "PPH", "parcels"],
            "check_against": ["depends on", "varies", "generally"]
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        response = test_query(service, test["query"], f"{i}. {test['name']}")
        
        if response:
            # Validate quality
            has_required = all(term.lower() in response.response.lower() for term in test["check_for"])
            has_forbidden = any(term.lower() in response.response.lower() for term in test["check_against"])
            
            result = {
                "name": test["name"],
                "passed": has_required and not has_forbidden,
                "has_required": has_required,
                "has_forbidden": has_forbidden,
                "confidence": response.confidence_score
            }
            results.append(result)
            
            print(f"\nVALIDATION:")
            print(f"  Required terms present: {'PASS' if has_required else 'FAIL'}")
            print(f"  Forbidden terms absent: {'PASS' if not has_forbidden else 'FAIL'}")
            print(f"  Overall: {'✓ PASS' if result['passed'] else '✗ FAIL'}")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    for result in results:
        status = "✓" if result["passed"] else "✗"
        print(f"  {status} {result['name']}")
        if not result["passed"]:
            if not result["has_required"]:
                print(f"      - Missing required terms")
            if result["has_forbidden"]:
                print(f"      - Contains forbidden generic terms")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Accuracy improvements working!")
    else:
        print(f"\n⚠️ {total - passed} tests failed - Further tuning needed")
    
    print("\nRecommendations:")
    print("1. Review failed test responses above")
    print("2. Check document retrieval relevance scores")
    print("3. Ensure all NEO technical documents are ingested")
    print("4. Consider adding more domain terms to query expansion")

if __name__ == "__main__":
    main()
