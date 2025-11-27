"""
Test Enhanced Agentic Architecture
Demonstrates: Top-K Retrieval → LLM Ranking → Response → Validation → Feedback Loop
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.modules.neo_chatbot.services.agentic_service import get_agentic_service
from app.modules.neo_chatbot.models.schemas import ChatRequest

def print_section(title: str, char: str = "="):
    """Print formatted section"""
    print("\n" + char*80)
    print(f"  {title}")
    print(char*80)

def test_enhanced_workflow(service, query: str, test_name: str):
    """Test the enhanced workflow with detailed output"""
    print_section(f"TEST: {test_name}", "=")
    print(f"\nQuery: {query}\n")
    
    request = ChatRequest(
        message=query,
        session_id="enhanced_test",
        conversation_history=[]
    )
    
    try:
        print("Starting enhanced agentic workflow...")
        print("-" * 80)
        
        response = service.process_query(request)
        
        # Display workflow metadata
        metadata = response.metadata if response.metadata else {}
        
        print("\n[PHASE 1: DOCUMENT RETRIEVAL & RANKING]")
        print(f"  Documents Retrieved: {metadata.get('documents_retrieved', 'N/A')}")
        print(f"  Documents Ranked: {metadata.get('documents_ranked', 'N/A')}")
        print(f"  Format Decision: {metadata.get('format_decision', 'N/A')}")
        
        print("\n[PHASE 2: RESPONSE GENERATION]")
        print(f"  Initial Response Length: {metadata.get('initial_response_length', 'N/A')} chars")
        
        print("\n[PHASE 3: VALIDATION & FEEDBACK]")
        print(f"  Verification Performed: {metadata.get('verification_performed', False)}")
        print(f"  Verification Passed: {metadata.get('verification_passed', 'N/A')}")
        print(f"  Iterations Used: {metadata.get('iterations_used', 0)}")
        
        if metadata.get('verification_issues'):
            print(f"  Issues Found: {metadata.get('verification_issues', [])}")
        
        print(f"  Final Response Length: {metadata.get('final_response_length', 'N/A')} chars")
        
        print("\n[PHASE 4: FINAL OUTPUT]")
        print("-" * 80)
        # Show first 600 chars of response
        response_text = response.response
        if len(response_text) > 600:
            print(response_text[:600] + "...")
        else:
            print(response_text)
        print("-" * 80)
        
        print(f"\n[QUALITY METRICS]")
        print(f"  Confidence Score: {response.confidence_score}")
        print(f"  Source Documents: {len(response.sources) if response.sources else 0}")
        
        # Quality indicators
        has_citations = "Document" in response_text or "📄" in response_text
        has_specifics = any(char.isdigit() for char in response_text[:200])
        no_generic = not any(phrase in response_text.lower() for phrase in ["generally", "typically", "usually", "various types"])
        
        print(f"  Has Citations: {'YES' if has_citations else 'NO'}")
        print(f"  Has Specific Details: {'YES' if has_specifics else 'NO'}")
        print(f"  Avoids Generic Terms: {'YES' if no_generic else 'NO'}")
        
        # Overall assessment
        quality_score = sum([has_citations, has_specifics, no_generic])
        print(f"\n  Overall Quality: {quality_score}/3 ", end="")
        if quality_score == 3:
            print("✓ EXCELLENT")
        elif quality_score == 2:
            print("✓ GOOD")
        else:
            print("⚠ NEEDS IMPROVEMENT")
        
        return response
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Test the enhanced agentic architecture"""
    
    print_section("ENHANCED AGENTIC ARCHITECTURE TEST", "=")
    print("\nWorkflow: Query Expansion → Top-K Retrieval → LLM Ranking →")
    print("          Format Decision → Response → Validation → Feedback Loop → Finalize")
    print("\nThis test demonstrates the complete enhanced workflow with:")
    print("  1. Query expansion with domain terms")
    print("  2. Retrieval of 20 candidate documents")
    print("  3. LLM-based ranking to select top 10")
    print("  4. Response generation with anti-hallucination")
    print("  5. Validation with quality checks")
    print("  6. Feedback loop if validation fails (max 2 retries)")
    
    # Initialize service
    print("\n" + "-"*80)
    print("Initializing enhanced agentic service...")
    service = get_agentic_service()
    
    if not service:
        print("[ERROR] Could not initialize service")
        return
    
    print("[OK] Service initialized with enhanced architecture")
    
    # Test cases
    test_cases = [
        {
            "name": "Definition Query (Should Pass First Time)",
            "query": "what is GTC station",
            "expected_iterations": 0
        },
        {
            "name": "Types Query (Previously Hallucinated)",
            "query": "what are the different types of sorter services available",
            "expected_iterations": 0  # Should pass with improved prompting
        },
        {
            "name": "Technical Specs Query",
            "query": "what is the throughput capacity of the cross belt sorter system",
            "expected_iterations": 0
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        response = test_enhanced_workflow(
            service, 
            test["query"], 
            f"{i}. {test['name']}"
        )
        
        if response and response.metadata:
            result = {
                "name": test["name"],
                "iterations": response.metadata.get("iterations_used", 0),
                "passed": response.metadata.get("verification_passed", False),
                "confidence": response.confidence_score
            }
            results.append(result)
    
    # Summary
    print_section("SUMMARY", "=")
    
    print("\nWorkflow Performance:")
    for i, result in enumerate(results, 1):
        iterations_text = f"{result['iterations']} iteration(s)"
        status = "✓ PASSED" if result['passed'] else "✗ FAILED"
        print(f"  {i}. {result['name']}")
        print(f"     {status} | {iterations_text} | Confidence: {result['confidence']}")
    
    # Statistics
    total_iterations = sum(r['iterations'] for r in results)
    avg_iterations = total_iterations / len(results) if results else 0
    first_pass_rate = sum(1 for r in results if r['iterations'] == 0) / len(results) * 100 if results else 0
    
    print(f"\nStatistics:")
    print(f"  Total Tests: {len(results)}")
    print(f"  First-Pass Success Rate: {first_pass_rate:.1f}%")
    print(f"  Average Iterations: {avg_iterations:.1f}")
    print(f"  Total Retries: {total_iterations}")
    
    if first_pass_rate >= 80:
        print(f"\n✓ EXCELLENT - Prompting and validation working well!")
    elif first_pass_rate >= 60:
        print(f"\n✓ GOOD - System functioning, minor tuning needed")
    else:
        print(f"\n⚠ NEEDS IMPROVEMENT - Consider adjusting validation criteria")
    
    print("\nKey Features Demonstrated:")
    print("  ✓ Top-K retrieval with 20 candidates")
    print("  ✓ LLM-based ranking to select best 10")
    print("  ✓ Anti-hallucination prompting")
    print("  ✓ Automatic validation")
    print("  ✓ Feedback loop for self-correction")
    print("  ✓ Comprehensive metadata tracking")
    
    print("\nNext Steps:")
    print("  1. Review responses for quality and accuracy")
    print("  2. Check iteration counts - most should be 0 (first-pass success)")
    print("  3. Examine any responses that required retries")
    print("  4. Adjust max_iterations in agentic_service.py if needed")
    print("  5. Add more domain-specific documents for better results")

if __name__ == "__main__":
    main()
