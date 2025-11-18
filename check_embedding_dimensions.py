"""
Check Embedding Dimensions in Vector Store
Verifies consistency of embedding dimensions across all stored documents
"""

import json
from pathlib import Path
import sys

def main():
    print("\n" + "="*80)
    print("📊 EMBEDDING DIMENSION CHECKER")
    print("="*80)
    
    vector_store_path = Path("app/modules/neo_chatbot/data/vector_store.json")
    
    if not vector_store_path.exists():
        print("\n⚠️  No vector store found!")
        print(f"   Expected at: {vector_store_path}")
        print("\n💡 Run ingestion first: python ingest_all_documents.py")
        print("="*80 + "\n")
        return
    
    # Load vector store
    with open(vector_store_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not data:
        print("\n⚠️  Vector store is empty!")
        print("\n💡 Run ingestion: python ingest_all_documents.py")
        print("="*80 + "\n")
        return
    
    print(f"\n📄 Total documents: {len(data)}")
    
    # Check dimensions
    dimension_counts = {}
    files_by_dimension = {}
    
    for doc in data:
        embedding = doc.get('embedding', [])
        dim = len(embedding)
        
        # Count dimensions
        dimension_counts[dim] = dimension_counts.get(dim, 0) + 1
        
        # Track files
        filename = doc.get('metadata', {}).get('filename', 'unknown')
        if dim not in files_by_dimension:
            files_by_dimension[dim] = set()
        files_by_dimension[dim].add(filename)
    
    # Display results
    print(f"\n📏 Embedding Dimensions Found:")
    for dim, count in sorted(dimension_counts.items()):
        percentage = (count / len(data)) * 100
        print(f"   {dim} dimensions: {count} documents ({percentage:.1f}%)")
    
    # Check for inconsistency
    if len(dimension_counts) > 1:
        print(f"\n❌ INCONSISTENT DIMENSIONS DETECTED!")
        print(f"   Found {len(dimension_counts)} different embedding sizes")
        print(f"\n⚠️  This will cause errors when querying!")
        
        print(f"\n📋 Files by Dimension:")
        for dim, files in sorted(files_by_dimension.items()):
            print(f"\n   {dim} dimensions ({len(files)} unique files):")
            for filename in sorted(files)[:5]:  # Show first 5
                print(f"      - {filename}")
            if len(files) > 5:
                print(f"      ... and {len(files) - 5} more")
        
        print(f"\n🔧 Recommended Actions:")
        print(f"   1. Fix ingest_documents.py to use consistent dimensions")
        print(f"   2. Re-ingest all documents")
        print(f"   3. Or convert existing embeddings")
        print(f"\n   See: docs/EMBEDDING_SIZE_MISMATCH_GUIDE.md")
        
    else:
        dim = list(dimension_counts.keys())[0]
        print(f"\n✅ CONSISTENT DIMENSIONS!")
        print(f"   All documents use {dim} dimensions")
        
        # Check if it matches expected
        expected = 1536  # OpenAI text-embedding-3-small
        if dim == expected:
            print(f"   ✅ Matches OpenAI standard ({expected} dimensions)")
        else:
            print(f"   ⚠️  Non-standard dimension (expected {expected})")
            print(f"   💡 Consider re-ingesting with OpenAI embeddings")
    
    # Sample embedding values
    print(f"\n📊 Sample Embedding (first 10 values):")
    sample_embedding = data[0]['embedding'][:10]
    print(f"   {sample_embedding}")
    
    # Check if all zeros
    if all(v == 0.0 for v in data[0]['embedding']):
        print(f"\n   ⚠️  WARNING: Embedding is all zeros!")
        print(f"   This suggests mock/fallback embeddings are being used")
        print(f"   💡 Set OPENAI_API_KEY for better quality embeddings")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
