"""Check Vector Store Statistics"""
from app.modules.neo_chatbot.services.vector_store_service import VectorStoreService

vs = VectorStoreService()
stats = vs.get_stats()

print("\n" + "="*60)
print("📊 VECTOR STORE STATUS")
print("="*60)
print(f"\nTotal documents: {stats.get('total_documents', 0)}")
print(f"\nDocuments by category:")
for cat, count in sorted(stats.get('by_category', {}).items()):
    print(f"  • {cat}: {count}")
print("\n" + "="*60 + "\n")
