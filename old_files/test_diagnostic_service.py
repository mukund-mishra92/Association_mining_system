"""
Test script for Diagnostic Support Service
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.modules.neo_chatbot.services.diagnostic_support_service import DiagnosticSupportService

def main():
    print("\n" + "="*80)
    print("DIAGNOSTIC SUPPORT SERVICE - TEST")
    print("="*80 + "\n")
    
    # Initialize service
    print("Initializing Diagnostic Support Service...")
    diagnostic = DiagnosticSupportService()
    
    # Get statistics
    print("\n📊 STATISTICS:")
    print("-" * 80)
    stats = diagnostic.get_statistics()
    print(f"Total Issues: {stats['total_issues']}")
    print(f"Bot Level: {stats['bot_level_count']}")
    print(f"Station Level: {stats['station_level_count']}")
    print(f"High Severity: {stats['severity']['high']}")
    print(f"Medium Severity: {stats['severity']['medium']}")
    print(f"With SQL Solutions: {stats['with_sql_solutions']}")
    print(f"Reported to Developers: {stats['reported_to_developers']}")
    
    # Test search
    print("\n\n🔍 TEST SEARCH: 'bot stuck'")
    print("-" * 80)
    results = diagnostic.search_issue("bot stuck")
    print(f"Found {len(results)} matches:\n")
    
    for i, result in enumerate(results[:3], 1):
        print(f"{i}. {result['problem']}")
        print(f"   Severity: {result['severity']}")
        print(f"   Type: {result['type']}")
        print(f"   Relevance: {result['relevance_score']}")
        print()
    
    # Test formatted report
    if results:
        print("\n\n📋 FORMATTED DIAGNOSTIC REPORT:")
        print("=" * 80)
        report = diagnostic.format_diagnostic_report(results[0])
        print(report)
    
    # Test SQL solutions
    print("\n\n💻 TEST: SQL SOLUTIONS for 'bot'")
    print("-" * 80)
    sql_solutions = diagnostic.get_sql_solutions("bot")
    print(f"Found {len(sql_solutions)} issues with SQL solutions:\n")
    
    for i, solution in enumerate(sql_solutions[:2], 1):
        print(f"{i}. {solution['problem']}")
        print(f"   SQL: {solution['sql_query'][:100]}...")
        print()
    
    # Test multi-symptom analysis
    print("\n\n🔧 TEST: MULTI-SYMPTOM ANALYSIS")
    print("-" * 80)
    symptoms = ["bot stuck in tower", "slider position"]
    recommendations = diagnostic.get_diagnostic_recommendations(symptoms)
    
    print(f"Analyzed symptoms: {recommendations['symptoms_analyzed']}")
    print(f"Total matches: {recommendations['total_matches']}")
    print(f"Requires developer: {recommendations['requires_developer']}")
    print(f"\nTop {len(recommendations['recommended_solutions'])} recommendations:")
    
    for i, rec in enumerate(recommendations['recommended_solutions'], 1):
        print(f"\n{i}. {rec['problem']}")
        print(f"   Severity: {rec['severity']}")
        print(f"   Score: {rec['relevance_score']}")
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
