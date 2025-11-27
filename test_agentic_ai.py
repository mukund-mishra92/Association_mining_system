"""
Test Agentic AI System
Quick test to verify the multi-agent workflow is working
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.modules.neo_chatbot.services.agentic_service import get_agentic_service
from app.modules.neo_chatbot.models.schemas import ChatRequest, ChatbotType

def test_agentic_system():
    """Test the agentic AI with a sample query"""
    
    print("=" * 60)
    print("🤖 Testing Agentic AI System")
    print("=" * 60)
    
    # Initialize agentic service
    print("\n1️⃣ Initializing Agentic Service...")
    try:
        agentic_service = get_agentic_service()
        print("   ✅ Agentic Service initialized")
    except Exception as e:
        print(f"   ❌ Failed to initialize: {e}")
        return
    
    # Create test request
    print("\n2️⃣ Creating test query...")
    test_query = "What is the Sorter Service in NEO?"
    print(f"   Query: '{test_query}'")
    
    request = ChatRequest(
        message=test_query,
        chatbot_type=ChatbotType.KNOWLEDGE_BASE,
        session_id="test_session_001"
    )
    
    # Process with agents
    print("\n3️⃣ Processing with multi-agent workflow...")
    print("   (This may take a few seconds...)\n")
    
    try:
        response = agentic_service.process_query(request)
        
        print("=" * 60)
        print("✅ RESPONSE GENERATED")
        print("=" * 60)
        
        print(f"\n📝 Response:\n{response.response}\n")
        
        print("=" * 60)
        print("📊 METADATA")
        print("=" * 60)
        print(f"Confidence Score: {response.confidence_score:.2f}")
        
        # Check if response has metadata as attribute or dict
        if hasattr(response, 'metadata') and response.metadata:
            metadata = response.metadata if isinstance(response.metadata, dict) else {}
            print(f"Agent Workflow: {metadata.get('agent_workflow', 'N/A')}")
            print(f"Verification Performed: {metadata.get('verification_performed', 'N/A')}")
            print(f"Verification Notes: {metadata.get('verification_notes', 'N/A')}")
            print(f"Initial Response Length: {metadata.get('initial_response_length', 0)} chars")
            print(f"Final Response Length: {metadata.get('final_response_length', 0)} chars")
        else:
            print("(Metadata not available in response)")
        
        # Check for source documents
        sources = getattr(response, 'source_documents', None) or []
        if sources:
            print(f"\n📚 Source Documents: {len(sources)}")
            for i, doc in enumerate(sources[:3], 1):
                print(f"   {i}. {doc.source_file} (relevance: {doc.relevance_score:.2f})")
        else:
            print("\n📚 No source documents available (vector store may be empty)")
        
        print("\n" + "=" * 60)
        print("🎉 TEST COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR during processing:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agentic_system()
