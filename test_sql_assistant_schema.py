"""
Test SQL Assistant with actual database schema
"""

import sys
sys.path.insert(0, r'c:\Users\Balmukund.Mishra\Desktop\NEO\association_mining_system')

from app.modules.neo_chatbot.services.sql_assistant_service import SQLAssistantService
from app.modules.neo_chatbot.models.schemas import ChatRequest, ChatbotType

# Initialize service
print("Initializing SQL Assistant Service with actual schema...")
service = SQLAssistantService()
print(f"Database available: {service.db_available}")
print(f"Tables available: {len(service.schema_parser.get_table_names())}\n")

# Test queries
test_queries = [
    "Show me the top 10 order lines from wms_to_wcs_order_line_request_data",
    "Get all SKU recommendations with score greater than 0.8",
    "Show me recent mining job logs from the last 7 days",
    "What are the bin velocity scores for high-velocity bins?",
    "Show me articles with proximity scores above 0.9"
]

print("=" * 80)
print("TESTING SQL QUERY GENERATION WITH ACTUAL SCHEMA")
print("=" * 80)

for i, query in enumerate(test_queries, 1):
    print(f"\n{i}. User Query: {query}")
    print("-" * 80)
    
    # Create request
    request = ChatRequest(
        message=query,
        chatbot_type=ChatbotType.SQL_ASSISTANT,
        session_id="test-session"
    )
    
    # Process query (this will generate SQL, execute, and validate)
    try:
        response = service.process_query(request)
        
        print(f"Response preview: {response.response[:300]}...")
        
        if response.sql_query:
            print(f"Generated SQL: {response.sql_query[:200]}...")
        
        if response.confidence_score:
            print(f"Confidence: {response.confidence_score:.2%}")
        
        if response.query_results:
            print(f"Results: {len(response.query_results)} rows returned")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    print()

print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
