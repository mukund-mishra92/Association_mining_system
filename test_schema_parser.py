"""
Test the JSON schema parser
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.modules.neo_chatbot.utils.schema_parser import get_schema_parser

def test_schema_parser():
    print("=" * 80)
    print("🧪 TESTING JSON SCHEMA PARSER")
    print("=" * 80)
    
    try:
        # Load schema parser
        print("\n📂 Loading schema...")
        parser = get_schema_parser()
        
        # Get table names
        tables = parser.get_table_names()
        print(f"\n✅ Loaded {len(tables)} tables")
        
        # Show first 10 tables
        print("\n📋 First 10 tables:")
        for i, table in enumerate(tables[:10], 1):
            print(f"  {i}. {table}")
        
        # Test getting table info
        if tables:
            test_table = tables[0]
            print(f"\n🔍 Examining table: {test_table}")
            columns = parser.get_table_info(test_table)
            print(f"   Columns: {len(columns)}")
            for col in columns[:5]:
                print(f"     - {col['field']}: {col['type']} {col.get('comment', '')}")
        
        # Test search
        print("\n🔎 Searching for 'bin' tables:")
        bin_tables = parser.search_tables('bin')
        for table in bin_tables[:5]:
            print(f"   - {table}")
        
        print("\n✅ Schema parser test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_schema_parser()
