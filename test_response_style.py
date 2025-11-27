"""
Quick test for improved response style
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.modules.neo_chatbot.services.agentic_service import get_agentic_service
from app.modules.neo_chatbot.models.schemas import ChatRequest

def test_query(query: str):
    """Test a query and display the response"""
    print("\n" + "="*80)
    print(f"Query: {query}")
    print("="*80)
    
    service = get_agentic_service()
    if not service:
        print("ERROR: Could not initialize service")
        return
    
    request = ChatRequest(
        message=query,
        session_id="style_test",
        conversation_history=[]
    )
    
    try:
        response = service.process_query(request)
        
        print("\nRESPONSE:")
        print("-" * 80)
        print(response.response)
        print("-" * 80)
        
        # Check for style issues
        response_text = response.response
        issues = []
        
        if "```markdown" in response_text or "```python" in response_text:
            issues.append("Contains code block markers")
        if "Implementation:" in response_text or "💻 Implementation:" in response_text:
            issues.append("Contains 'Implementation:' label")
        if response_text.count("``") > 2:
            issues.append("Contains excessive backticks")
        if "Based on the provided documentation" in response_text and "are not explicitly mentioned" in response_text:
            issues.append("Uses awkward 'not explicitly mentioned' phrasing")
        
        print(f"\nSTYLE CHECK:")
        if issues:
            print("  Issues found:")
            for issue in issues:
                print(f"    - {issue}")
        else:
            print("  ✓ Clean, natural response style")
        
        print(f"\nCONFIDENCE: {response.confidence_score}")
        print(f"SOURCES: {len(response.sources) if response.sources else 0}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing improved response style...")
    print("Expected: Clean, natural prose without markdown artifacts\n")
    
    # Test the problematic query
    test_query("what are the different types of conveyors in our system")
    
    # Test another query
    test_query("what is GTC station")
    
    print("\n" + "="*80)
    print("EXPECTED IMPROVEMENTS:")
    print("="*80)
    print("✓ No '💻 Implementation:' labels")
    print("✓ No '```markdown' or code block markers in text")
    print("✓ Natural, direct answers")
    print("✓ Clean citations: 'Document 3 (Page 16)' not awkward references")
    print("✓ Professional prose, not meta-commentary")
