"""
Build comprehensive entity_table_map based on actual schema tables
"""
import sys
sys.path.insert(0, 'app/modules/neo_chatbot')

from utils.schema_parser import get_schema_parser

# Load schema
parser = get_schema_parser()
all_tables = sorted(parser.get_table_names())

print(f"Total tables in schema: {len(all_tables)}\n")

# Define entity categories and keywords for classification
entity_keywords = {
    'bin': ['bin', 'location', 'zone'],
    'bot': ['bot', 'robot', 'agv'],
    'order': ['order', 'shipment'],
    'wave': ['wave'],
    'pick': ['pick'],
    'put': ['put'],
    'sku': ['sku', 'article', 'product'],
    'inventory': ['inventory', 'stock'],
    'station': ['station', 'hw_station'],
    'task': ['task', 'job'],
    'alarm': ['alarm', 'alert', 'error'],
    'maintenance': ['maintenance', 'repair'],
    'user': ['user', 'operator', 'picker_user', 'packer'],
    'dashboard': ['dashboard'],
    'charging': ['charg', 'battery'],
    'conveyor': ['conveyor'],
    'log': ['log', 'history', 'audit'],
    'master': ['master', 'config'],
    'velocity': ['velocity', 'speed', 'analysis'],
}

# Categorize tables by entity
entity_tables = {entity: [] for entity in entity_keywords.keys()}

for table in all_tables:
    table_lower = table.lower()
    
    # Map table to entities based on keywords
    for entity, keywords in entity_keywords.items():
        if any(kw in table_lower for kw in keywords):
            entity_tables[entity].append(table)

# Print comprehensive entity_table_map
print("=" * 80)
print("COMPREHENSIVE ENTITY_TABLE_MAP")
print("=" * 80)
print()
print("entity_table_map = {")

for entity in sorted(entity_tables.keys()):
    tables = entity_tables[entity]
    if tables:
        print(f"    '{entity}': [")
        for table in tables[:15]:  # Limit to top 15 most relevant tables per entity
            print(f"        '{table}',")
        if len(tables) > 15:
            print(f"        # ... and {len(tables) - 15} more {entity}-related tables")
        print("    ],")

print("}")
print()

# Print statistics
print("\n" + "=" * 80)
print("STATISTICS BY ENTITY")
print("=" * 80)
for entity in sorted(entity_tables.keys()):
    count = len(entity_tables[entity])
    if count > 0:
        print(f"{entity:15} : {count:3} tables")
