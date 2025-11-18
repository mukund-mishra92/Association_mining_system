"""Check Vector Store Statistics"""
from app.modules.neo_chatbot.services.vector_store_service import VectorStoreService

vs = VectorStoreService()
stats = vs.get_statistics()

print("\n" + "="*60)
print("📊 VECTOR STORE STATUS")
print("="*60)
print(f"\nTotal documents: {stats.get('total_documents', 0)}")
print(f"\nDocuments by category:")
for cat, count in sorted(stats.get('categories', {}).items()):
    print(f"  • {cat}: {count}")

# Show storage info
storage_size = stats.get('storage_size_bytes', 0)
if storage_size > 0:
    size_mb = storage_size / (1024 * 1024)
    print(f"\nStorage size: {size_mb:.2f} MB")

print(f"Storage path: {stats.get('storage_path', 'N/A')}")
print("\n" + "="*60 + "\n")
