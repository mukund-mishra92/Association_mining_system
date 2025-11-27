"""
Test Natural ChatGPT-style Responses
Tests the improved format detection and natural response generation
"""

import asyncio
import os
from dotenv import load_dotenv
from app.modules.neo_chatbot.models.schemas import ChatRequest
from app.modules.neo_chatbot.services.agentic_service import AgenticService

# Load environment variables
load_dotenv()

async def test_queries():
    """Test various query types for natural responses"""
    
    # Initialize the agentic service
    print("🔧 Initializing Agentic Service...")
    service = AgenticService()
    
    # Test queries covering different scenarios
    test_cases = [
        {
            "query": "What is a sorter?",
            "expect": "Brief, direct definition without rigid structure"
        },
        {
            "query": "How does the NEO system work?",
            "expect": "Natural explanation with appropriate detail"
        },
        {
            "query": "What are the different types of conveyors?",
            "expect": "List if types exist in docs, otherwise natural answer"
        },
        {
            "query": "Explain the sorting system in detail",
            "expect": "Comprehensive response with natural structure"
        },
        {
            "query": "What is the throughput of the cross-belt sorter?",
            "expect": "Direct, specific answer with number"
        }
    ]
    
    print("\n" + "="*80)
    print("TESTING NATURAL RESPONSE GENERATION (ChatGPT-style)")
    print("="*80 + "\n")
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─'*80}")
        print(f"TEST {i}: {test['query']}")
        print(f"EXPECT: {test['expect']}")
        print(f"{'─'*80}")
        
        # Create chat request
        chat_request = ChatRequest(
            message=test['query'],
            session_id="test_natural_responses",
            chatbot_type="neo_general"
        )
        
        try:
            # Process query
            print("\n⏳ Processing...\n")
            response = service.process_query(chat_request)
            
            # Display results
            print("📝 RESPONSE:")
            print("-" * 80)
            print(response.response)
            print("-" * 80)
            
            # Show metadata
            if response.metadata:
                print(f"\n📊 Metadata:")
                print(f"   Format Decision: {response.metadata.get('format_decision', 'N/A')}")
                print(f"   Length: {response.metadata.get('user_constraints', {}).get('length', 'N/A')}")
                print(f"   Tone: {response.metadata.get('user_constraints', {}).get('tone', 'N/A')}")
                print(f"   Verification: {'✅ Passed' if response.metadata.get('verification_passed') else '⚠️ Issues found'}")
                print(f"   Iterations: {response.metadata.get('iterations_used', 0)}")
                print(f"   Confidence: {response.confidence_score:.2f}")
            
            # Quality checks
            print(f"\n🔍 Quality Checks:")
            response_text = response.response.lower()
            
            issues = []
            if "implementation:" in response_text:
                issues.append("❌ Contains 'Implementation:' label")
            if "```markdown" in response_text or "```python" in response_text:
                issues.append("❌ Contains markdown artifacts")
            if response_text.count("•") > 10 and "list" not in test['query'].lower():
                issues.append("⚠️ Overuse of bullet points")
            if not any(char.isupper() for char in response.response[:50]):
                issues.append("❌ Doesn't start with capital letter")
            if response.response.endswith("..."):
                issues.append("⚠️ Ends with ellipsis")
                
            if issues:
                for issue in issues:
                    print(f"   {issue}")
            else:
                print("   ✅ All quality checks passed")
            
            # Check for natural writing
            natural_indicators = [
                ("sources cited" if any(x in response_text for x in ["document", "page", "according to"]) else None),
                ("specific details" if any(c.isdigit() for c in response.response) else None),
                ("clean formatting" if "```" not in response_text else None)
            ]
            
            print(f"\n✨ Natural Writing:")
            for indicator in natural_indicators:
                if indicator:
                    print(f"   ✅ {indicator.capitalize()}")
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80 + "\n")
    
    print("📋 Summary:")
    print("   The responses should be:")
    print("   ✓ Natural and conversational (not templated)")
    print("   ✓ Appropriately brief or detailed based on query")
    print("   ✓ Free of meta-text and markdown artifacts")
    print("   ✓ Specific and accurate (from documents)")
    print("   ✓ Well-cited with natural source references")

if __name__ == "__main__":
    asyncio.run(test_queries())
