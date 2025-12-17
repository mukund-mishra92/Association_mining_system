"""
Check Vector Store Status - Diagnose Document Retrieval Issues
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.modules.neo_chatbot.services.vector_store_service import VectorStoreService
from app.modules.neo_chatbot.services.llm_service import LLMService


def check_vector_store():
    """Check vector store contents and search capability"""
    
    print("\n" + "=" * 80)
    print("VECTOR STORE DIAGNOSTIC REPORT")
    print("=" * 80)
    
    # Initialize services
    vs = VectorStoreService()
    llm = LLMService()
    
    # 1. Check total documents
    print(f"\n📊 DOCUMENT STATISTICS:")
    print(f"   Total documents: {len(vs.documents)}")
    
    if len(vs.documents) == 0:
        print("\n❌ NO DOCUMENTS FOUND!")
        print("   Run: venv\\Scripts\\python.exe ingest_all_proposals.py")
        return
    
    # 2. Check categories
    categories = {}
    for doc in vs.documents:
        cat = doc.get('metadata', {}).get('category', 'uncategorized')
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n📁 BY CATEGORY:")
    for cat, count in sorted(categories.items()):
        print(f"   {cat}: {count} documents")
    
    # 3. Check filenames
    print(f"\n📄 DOCUMENT FILES:")
    filenames = set()
    for doc in vs.documents:
        filename = doc.get('metadata', {}).get('filename', 'unknown')
        filenames.add(filename)
    
    for i, filename in enumerate(sorted(filenames), 1):
        # Count chunks per file
        chunks_count = sum(1 for d in vs.documents if d.get('metadata', {}).get('filename') == filename)
        print(f"   {i}. {filename} ({chunks_count} chunks)")
    
    # 4. Test search with CBS query
    print(f"\n" + "=" * 80)
    print("🔍 TEST SEARCH: 'Cross Belt Sorter flow'")
    print("=" * 80)
    
    test_query = "Cross Belt Sorter flow components and process"
    print(f"\nQuery: {test_query}")
    print(f"Generating embedding...")
    
    try:
        query_embedding = llm.generate_embedding(test_query)
        print(f"✅ Embedding generated ({len(query_embedding)} dimensions)")
        
        print(f"\nSearching vector store (top_k=10, min_similarity=0.20)...")
        results = vs.search(
            query_embedding=query_embedding,
            top_k=10,
            min_similarity=0.20
        )
        
        print(f"\n📊 SEARCH RESULTS: {len(results)} documents found")
        print("=" * 80)
        
        if len(results) == 0:
            print("\n❌ NO RESULTS FOUND!")
            print("\nPossible issues:")
            print("1. Documents don't contain CBS/Cross Belt Sorter content")
            print("2. Embedding model mismatch")
            print("3. Similarity threshold too high")
            print("\nRe-ingest documents: venv\\Scripts\\python.exe ingest_all_proposals.py")
        else:
            for i, result in enumerate(results, 1):
                doc = result['document']
                similarity = result['similarity']
                filename = doc['metadata'].get('filename', 'unknown')
                page = doc['metadata'].get('page_number', 'N/A')
                category = doc['metadata'].get('category', 'unknown')
                content_preview = doc['content'][:200] + "..."
                
                print(f"\n[RESULT {i}]")
                print(f"   File: {filename} | Page: {page}")
                print(f"   Category: {category} | Similarity: {similarity:.1%}")
                print(f"   Content preview:")
                print(f"   {content_preview}")
                print(f"   {'-' * 78}")
        
        # 5. Check if specific keywords exist
        print(f"\n" + "=" * 80)
        print("🔍 KEYWORD SEARCH IN DOCUMENTS")
        print("=" * 80)
        
        keywords = [
            "Cross Belt Sorter",
            "CBS",
            "infeed conveyor",
            "barcode scanner",
            "sortation",
            "Falcon"
        ]
        
        print(f"\nSearching for keywords in document content...")
        
        for keyword in keywords:
            count = 0
            for doc in vs.documents:
                if keyword.lower() in doc['content'].lower():
                    count += 1
            print(f"   '{keyword}': {count} chunks")
        
        # 6. Sample a document
        print(f"\n" + "=" * 80)
        print("📄 SAMPLE DOCUMENT CONTENT")
        print("=" * 80)
        
        sample_doc = vs.documents[0]
        print(f"\nFile: {sample_doc['metadata'].get('filename', 'unknown')}")
        print(f"Page: {sample_doc['metadata'].get('page_number', 'N/A')}")
        print(f"Category: {sample_doc['metadata'].get('category', 'unknown')}")
        print(f"Content length: {len(sample_doc['content'])} chars")
        print(f"\nFirst 500 characters:")
        print(f"{sample_doc['content'][:500]}...")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    check_vector_store()
