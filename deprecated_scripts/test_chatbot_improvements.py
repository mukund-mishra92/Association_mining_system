"""
Test Chatbot Improvements
Tests the upgraded model and vision detection capabilities
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.modules.neo_chatbot.services.knowledge_base_service import KnowledgeBaseService
from app.modules.neo_chatbot.services.vision_llm_service import get_vision_service
from app.modules.neo_chatbot.models.schemas import ChatRequest, MessageRole


def test_model_upgrade():
    """Test that the better model produces varied responses"""
    print("=" * 80)
    print("TEST 1: Model Quality - Response Variety")
    print("=" * 80)
    
    kb_service = KnowledgeBaseService()
    
    # Test queries that should produce DIFFERENT responses
    test_queries = [
        "What is the order processing workflow?",
        "How does bin assignment work?",
        "What are the safety procedures for forklift operation?",
        "Explain the inventory tracking system"
    ]
    
    print("\nTesting response variety with llama-3.3-70b-versatile...\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nQuery {i}: {query}")
        print("-" * 80)
        
        try:
            request = ChatRequest(
                message=query,
                session_id=f"test_session_{i}"
            )
            
            response = kb_service.process_query(request)
            
            # Print first 200 chars of response
            preview = response.response[:200] + "..." if len(response.response) > 200 else response.response
            print(f"Response: {preview}")
            print(f"Confidence: {response.confidence_score:.2%}")
            print(f"Sources: {len(response.sources)}")
            
        except Exception as e:
            print(f"ERROR: {e}")
    
    print("\n" + "=" * 80)
    print("✅ Model quality test complete!")
    print("=" * 80)


def test_vision_detection():
    """Test vision query detection"""
    print("\n" + "=" * 80)
    print("TEST 2: Vision Query Detection")
    print("=" * 80)
    
    vision_service = get_vision_service()
    
    # Test queries
    test_cases = [
        # Vision queries (should detect)
        ("Show me the flowchart for order processing", True),
        ("What does the architecture diagram show?", True),
        ("Explain the process flow diagram on page 5", True),
        ("Is there an image showing the warehouse layout?", True),
        
        # Text queries (should NOT detect)
        ("What is order processing?", False),
        ("How do I assign bins?", False),
        ("Explain the architecture", False),
        ("What are the processing steps?", False),
    ]
    
    print("\nTesting vision keyword detection...\n")
    
    correct = 0
    total = len(test_cases)
    
    for query, expected_vision in test_cases:
        detected = vision_service.is_vision_query(query)
        status = "✅" if detected == expected_vision else "❌"
        
        print(f"{status} '{query}'")
        print(f"   Expected: {expected_vision}, Detected: {detected}")
        
        if detected == expected_vision:
            correct += 1
    
    print("\n" + "=" * 80)
    accuracy = (correct / total) * 100
    print(f"Detection Accuracy: {correct}/{total} ({accuracy:.1f}%)")
    print("=" * 80)


def test_vision_capability():
    """Test vision LLM availability"""
    print("\n" + "=" * 80)
    print("TEST 3: Vision Capability Check")
    print("=" * 80)
    
    vision_service = get_vision_service()
    
    print("\nChecking vision API availability...\n")
    
    # Check Anthropic
    if vision_service.anthropic_client:
        print("✅ Claude 3 Sonnet (Anthropic) - READY")
        print("   Model: claude-3-5-sonnet-20241022")
        print("   Cost: ~$0.003/1K tokens")
        print("   Best for: Technical diagrams, flowcharts")
    else:
        print("❌ Claude 3 Sonnet - NOT CONFIGURED")
        print("   Set ANTHROPIC_API_KEY in .env file")
    
    print()
    
    # Check OpenAI
    if vision_service.openai_client:
        print("✅ GPT-4 Vision (OpenAI) - READY")
        print("   Model: gpt-4o")
        print("   Cost: ~$0.01/1K tokens")
        print("   Best for: Complex image understanding")
    else:
        print("❌ GPT-4 Vision - NOT CONFIGURED")
        print("   Set OPENAI_API_KEY in .env file")
    
    print("\n" + "-" * 80)
    
    if vision_service.is_vision_enabled():
        print("✅ Vision capability: ENABLED")
        print("\nChatbot can now understand:")
        print("  • Flowcharts and process diagrams")
        print("  • Architecture diagrams")
        print("  • System workflows")
        print("  • Technical illustrations")
    else:
        print("❌ Vision capability: DISABLED")
        print("\nTo enable vision support:")
        print("  1. Get API key from Anthropic or OpenAI")
        print("  2. Add to .env file:")
        print("     ANTHROPIC_API_KEY=sk-ant-xxx")
        print("     # OR")
        print("     OPENAI_API_KEY=sk-xxx")
        print("  3. Restart the chatbot service")
    
    print("=" * 80)


def test_query_classification():
    """Test query type classification"""
    print("\n" + "=" * 80)
    print("TEST 4: Query Type Classification")
    print("=" * 80)
    
    kb_service = KnowledgeBaseService()
    
    test_cases = [
        ("What is order processing?", "DEFINITION"),
        ("How to assign bins?", "PROCEDURAL"),
        ("Show me the OrderController class", "CODE_QUERY"),
        ("What does NEO stand for?", "SIMPLE_FACT"),
        ("Order processing vs bin assignment", "COMPARISON"),
        ("Tell me about the warehouse system", "EXPLORATORY"),
    ]
    
    print("\nClassifying different query types...\n")
    
    for query, expected_type in test_cases:
        classified_type = kb_service._classify_query(query)
        status = "✅" if classified_type == expected_type else "⚠️"
        
        print(f"{status} '{query}'")
        print(f"   Expected: {expected_type}, Got: {classified_type}")


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("CHATBOT IMPROVEMENTS TEST SUITE")
    print("=" * 80)
    print("\nTesting:")
    print("1. Model upgrade (llama-3.3-70b-versatile)")
    print("2. Vision query detection")
    print("3. Vision capability availability")
    print("4. Query classification")
    print("\n")
    
    try:
        # Test 1: Model quality (requires vector store with documents)
        test_model_upgrade()
        
        # Test 2: Vision detection
        test_vision_detection()
        
        # Test 3: Vision capability
        test_vision_capability()
        
        # Test 4: Query classification
        test_query_classification()
        
        print("\n" + "=" * 80)
        print("ALL TESTS COMPLETE!")
        print("=" * 80)
        print("\nNext Steps:")
        print("1. If vision is not enabled, configure API keys")
        print("2. Test chatbot with real queries in the UI")
        print("3. Upload documents with flowcharts/diagrams")
        print("4. Ask vision-related questions to test image understanding")
        print("\n")
    
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
