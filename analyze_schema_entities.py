"""
Analyze schema and generate entity map
"""
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from app.modules.neo_chatbot.utils.schema_parser import get_schema_parser

def analyze_tables():
    parser = get_schema_parser()
    tables = parser.get_table_names()
    
    # Categorize tables by keywords
    categories = defaultdict(list)
    
    # Define keywords to look for
    keywords = {
        'bin': ['bin', 'location', 'slot'],
        'bot': ['bot', 'robot', 'agv'],
        'order': ['order', 'shipment', 'delivery'],
        'wave': ['wave', 'batch'],
        'pick': ['pick', 'picking'],
        'put': ['put', 'putaway', 'storage'],
        'sku': ['sku', 'article', 'product', 'item'],
        'inventory': ['inventory', 'stock'],
        'station': ['station', 'hw_station'],
        'alarm': ['alarm', 'alert', 'error'],
        'log': ['log', 'history', 'audit'],
        'master': ['master', 'config', 'configuration'],
        'task': ['task', 'job', 'work'],
        'user': ['user', 'operator', 'personnel'],
        'zone': ['zone', 'area', 'section'],
        'conveyor': ['conveyor', 'transport'],
        'charging': ['charging', 'charge', 'battery'],
        'maintenance': ['maintenance', 'repair', 'service'],
        'dashboard': ['dashboard', 'report'],
    }
    
    # Categorize tables
    for table in tables:
        table_lower = table.lower()
        for category, kw_list in keywords.items():
            for keyword in kw_list:
                if keyword in table_lower:
                    categories[category].append(table)
                    break
    
    # Print results
    print("=" * 80)
    print("ENTITY MAP ANALYSIS")
    print("=" * 80)
    print(f"\nTotal tables: {len(tables)}\n")
    
    for category in sorted(categories.keys()):
        table_list = sorted(set(categories[category]))
        if table_list:
            print(f"\n{category.upper()} ({len(table_list)} tables):")
            for i, table in enumerate(table_list[:10], 1):  # Show first 10
                print(f"  {i}. {table}")
            if len(table_list) > 10:
                print(f"  ... and {len(table_list) - 10} more")
    
    # Generate entity map code
    print("\n" + "=" * 80)
    print("SUGGESTED ENTITY MAP")
    print("=" * 80)
    print("\nentity_map = {")
    
    for category in sorted(categories.keys()):
        table_list = sorted(set(categories[category]))
        if table_list and len(table_list) <= 15:  # Only include if reasonable number
            # Extract key terms from table names
            terms = set()
            for table in table_list:
                # Add table name
                terms.add(table.lower())
                # Add parts of table name
                parts = table.lower().replace('_', ' ').split()
                terms.update(parts)
            
            # Filter out common words
            common_words = {'master', 'data', 'info', 'table', 'log', 'history'}
            terms = [t for t in sorted(terms) if t not in common_words and len(t) > 2]
            
            if terms:
                print(f"    '{category}': {terms[:8]},")
    
    print("}")

if __name__ == "__main__":
    analyze_tables()
