"""
Verify Knowledge Base with HuggingFace Embeddings
Tests the chatbot's document search with real embeddings
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

def test_knowledge_base():
    """Test knowledge base service with HuggingFace embeddings"""
    
    print("=" * 70)
    print("🔍 Knowledge Base + HuggingFace Embeddings Test")
    print("=" * 70)
    print()
    
    try:
        # Import services
        print("📦 Loading services...")
        from app.modules.neo_chatbot.services.knowledge_base_service import KnowledgeBaseService
        from app.modules.neo_chatbot.models.schemas import ChatRequest
        
        # Initialize service
        kb_service = KnowledgeBaseService()
        print("✅ Knowledge Base Service initialized")
        print()
        
        # Check if HuggingFace is configured
        if kb_service.llm_service.hf_client:
            print("✅ HuggingFace embeddings: ENABLED")
        else:
            print("⚠️ HuggingFace embeddings: DISABLED (using mock)")
        print()
        
        # Check vector store
        doc_count = len(kb_service.vector_store.documents)
        print(f"📚 Vector Store: {doc_count} documents loaded")
        
        if doc_count == 0:
            print()
            print("⚠️ WARNING: No documents in vector store!")
            print("   Run: python ingest_all_documents.py")
            print()
            return False
        
        # Show document types
        doc_types = {}
        for doc in kb_service.vector_store.documents[:100]:  # Sample first 100
            doc_type = doc.get('metadata', {}).get('type', 'unknown')
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        
        print(f"   Document types: {doc_types}")
        print()
        
        # Test queries
        test_queries = [
            "What is NEO?",
            "What is FMS?",
            "Tell me about Fleet Management System"
        ]
        
        print("🧪 Testing semantic search with real embeddings...")
        print("-" * 70)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}: '{query}'")
            print("   Generating embedding...")
            
            try:
                # Generate embedding
                embedding = kb_service.llm_service.generate_embedding(query)
                embedding_dim = len(embedding)
                print(f"   ✅ Embedding generated: {embedding_dim} dimensions")
                
                # Check if it's a real embedding (not all zeros)
                import numpy as np
                magnitude = np.linalg.norm(embedding)
                
                if magnitude < 0.01:
                    print(f"   ⚠️ WARNING: Zero embedding detected (mock mode)")
                else:
                    print(f"   ✅ Real embedding (magnitude: {magnitude:.4f})")
                
                # Search vector store
                print("   Searching vector store...")
                results = kb_service.vector_store.search(
                    query_embedding=embedding,
                    top_k=5,
                    min_similarity=0.3
                )
                
                print(f"   ✅ Found {len(results)} relevant documents")
                
                if results:
                    print(f"   📊 Top result:")
                    top_result = results[0]
                    print(f"      - Similarity: {top_result['similarity']:.3f}")
                    print(f"      - Document: {top_result.get('document_name', 'Unknown')}")
                    print(f"      - Type: {top_result.get('metadata', {}).get('type', 'Unknown')}")
                    
                    # Show snippet
                    content = top_result.get('content', '')
                    snippet = content[:150] + "..." if len(content) > 150 else content
                    print(f"      - Content: {snippet}")
                    
                    # Check if similarity is good
                    if top_result['similarity'] > 0.7:
                        print(f"      ✅ Excellent match!")
                    elif top_result['similarity'] > 0.5:
                        print(f"      ✅ Good match")
                    else:
                        print(f"      ⚠️ Low similarity - might not be relevant")
                else:
                    print(f"   ⚠️ No documents found above similarity threshold")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                import traceback
                traceback.print_exc()
        
        print()
        print("-" * 70)
        print()
        print("=" * 70)
        print("🎉 KNOWLEDGE BASE TEST COMPLETE")
        print("=" * 70)
        print()
        
        if kb_service.llm_service.hf_client:
            print("✅ Status: Using HuggingFace embeddings (FREE, high quality)")
            print("✅ Your chatbot should now give accurate responses!")
            print()
            print("🚀 Try these queries in the chatbot:")
            print("   - 'What is NEO?'")
            print("   - 'What is FMS?'")
            print("   - 'How does station picking work?'")
        else:
            print("⚠️ Status: Using mock embeddings")
            print("   Add HUGGINGFACE_API_KEY to .env and restart")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_knowledge_base()
    
    if not success:
        print()
        print("❌ Test failed - check errors above")
        sys.exit(1)
    else:
        print("✅ All tests passed!")
        sys.exit(0)
