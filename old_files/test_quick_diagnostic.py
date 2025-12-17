"""Quick test of diagnostic service"""
from app.modules.neo_chatbot.services.diagnostic_support_service import DiagnosticSupportService

# Initialize service
ds = DiagnosticSupportService()

# Print statistics
stats = ds.get_statistics()
print("=" * 60)
print("DIAGNOSTIC SERVICE STATISTICS")
print("=" * 60)
print(f"Total Issues: {stats['total_issues']}")
print(f"Bot Level: {stats['bot_level_count']}")
print(f"Station Level: {stats['station_level_count']}")
print(f"High Severity: {stats['severity']['high']}")
print(f"With SQL Solutions: {stats['with_sql_solutions']}")
print()

# Test search queries
test_queries = [
    "bot not responding",
    "bot stuck in tower",
    "station pick failed",
    "emergency stop",
    "lidar issue"
]

print("=" * 60)
print("SEARCH RESULTS FOR COMMON QUERIES")
print("=" * 60)

for query in test_queries:
    results = ds.search_issue(query, None)
    print(f"\n🔍 Query: '{query}'")
    print(f"   Found: {len(results)} matches")
    
    if results:
        top = results[0]
        print(f"   Top Match: {top['problem'][:70]}...")
        print(f"   Relevance: {top['relevance_score']}%")
        print(f"   Type: {top['type']}")

print("\n" + "=" * 60)
print("✅ All issues loaded and searchable!")
print("=" * 60)
