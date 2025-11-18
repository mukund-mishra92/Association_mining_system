"""
Test Vector Store Service Methods
Quick test to ensure all methods work correctly
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.modules.neo_chatbot.services.vector_store_service import VectorStoreService

print("\n" + "="*80)
print("🧪 TESTING VECTOR STORE SERVICE")
print("="*80)

# Initialize
print("\n[1/5] Initializing Vector Store Service...")
vs = VectorStoreService()
print(f"✅ Loaded {len(vs.documents)} existing documents")

# Test get_statistics
print("\n[2/5] Testing get_statistics()...")
try:
    stats = vs.get_statistics()
    print(f"✅ get_statistics() works")
    print(f"   Total documents: {stats['total_documents']}")
    print(f"   Categories: {list(stats['categories'].keys())}")
except Exception as e:
    print(f"❌ ERROR: {e}")

# Test save_store
print("\n[3/5] Testing save_store()...")
try:
    vs.save_store()
    print(f"✅ save_store() works")
except Exception as e:
    print(f"❌ ERROR: {e}")

# Test get_all_documents
print("\n[4/5] Testing get_all_documents()...")
try:
    docs = vs.get_all_documents()
    print(f"✅ get_all_documents() works")
    print(f"   Retrieved {len(docs)} documents")
except Exception as e:
    print(f"❌ ERROR: {e}")

# Test search (if documents exist)
print("\n[5/5] Testing search()...")
if len(vs.documents) > 0:
    try:
        # Get first document's embedding
        test_embedding = vs.documents[0]['embedding']
        results = vs.search(test_embedding, top_k=3)
        print(f"✅ search() works")
        print(f"   Found {len(results)} results")
    except Exception as e:
        print(f"❌ ERROR: {e}")
else:
    print("⏭️  Skipped (no documents in store)")

print("\n" + "="*80)
print("✅ ALL TESTS COMPLETE")
print("="*80 + "\n")
