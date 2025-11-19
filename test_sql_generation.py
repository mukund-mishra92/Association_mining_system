"""
Test SQL generation to debug the issue
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from app.modules.neo_chatbot.services.llm_service import LLMService

def test_sql_generation():
    print("=" * 80)
    print("🧪 TESTING SQL GENERATION")
    print("=" * 80)
    
    # Initialize LLM service
    llm = LLMService()
    print(f"\n✅ LLM Provider: {llm.provider}")
    
    if llm.provider == "mock":
        print("❌ No LLM available! Check your API keys.")
        return
    
    # Test query
    test_query = "Show me all bins in zone A"
    print(f"\n📝 Test Query: {test_query}")
    
    # Simple system prompt
    system_prompt = """You are a SQL expert. Convert natural language to MySQL queries.

Available tables:
- bin_master (columns: bin_id, bin_name, zone, status)
- station_master (columns: station_id, station_name, status)
- sku_master (columns: sku_id, sku_name, description)

Instructions:
1. Generate ONLY the SQL query
2. Use proper MySQL syntax
3. Return the query wrapped in ```sql code block
4. No explanations, just the SQL query"""

    messages = [
        {"role": "user", "content": f"Convert to SQL: {test_query}"}
    ]
    
    print("\n🔄 Calling LLM...")
    try:
        response = llm.generate_response(
            messages=messages,
            system_prompt=system_prompt,
            max_tokens=300,
            temperature=0.1
        )
        
        print("\n📤 LLM Response:")
        print("-" * 80)
        print(response)
        print("-" * 80)
        
        # Try to extract SQL
        print("\n🔍 Extracting SQL...")
        
        if "```sql" in response.lower():
            start = response.lower().find("```sql") + 6
            end = response.find("```", start)
            if end > start:
                sql = response[start:end].strip()
                print(f"\n✅ Extracted SQL:")
                print("-" * 80)
                print(sql)
                print("-" * 80)
            else:
                print("❌ Could not find closing ```")
        else:
            print("❌ No ```sql code block found in response")
            
            # Try to find SELECT
            if "SELECT" in response.upper():
                lines = response.split('\n')
                sql_lines = []
                for line in lines:
                    if 'SELECT' in line.upper():
                        sql_lines.append(line)
                        # Get next few lines
                        idx = lines.index(line)
                        for i in range(idx + 1, min(idx + 5, len(lines))):
                            sql_lines.append(lines[i])
                            if ';' in lines[i]:
                                break
                        break
                
                if sql_lines:
                    print(f"\n⚠️  Found SELECT statement:")
                    print("-" * 80)
                    print('\n'.join(sql_lines))
                    print("-" * 80)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sql_generation()
