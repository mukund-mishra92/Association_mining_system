"""
Test Format Decision Agent - 3-Agent Agentic AI System
Tests various format requests to validate Format Decision Agent functionality
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.modules.neo_chatbot.services.agentic_service import get_agentic_service
from app.modules.neo_chatbot.models.schemas import ChatRequest

def print_section(title: str):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_result(query: str, response):
    """Print test result with format details"""
    print(f"\nQuery: {query}")
    
    # Extract metadata
    metadata = response.metadata if hasattr(response, 'metadata') and response.metadata else {}
    format_decision = metadata.get('format_decision', 'N/A') if isinstance(metadata, dict) else 'N/A'
    user_constraints = metadata.get('user_constraints', {}) if isinstance(metadata, dict) else {}
    
    print(f"\n[FORMAT] Decision: {format_decision}")
    print(f"[FORMAT] User Constraints: {user_constraints}")
    print(f"\n[RESPONSE] Length: {len(response.response)} chars")
    print("-" * 80)
    print(response.response[:500] + "..." if len(response.response) > 500 else response.response)
    print("-" * 80)
    print(f"[CONFIDENCE] {response.confidence_score}")
    print(f"[SOURCES] {len(response.sources) if response.sources else 0} documents")
    
    exec_time = metadata.get('agent_execution_time', 'N/A') if isinstance(metadata, dict) else 'N/A'
    print(f"[TIME] {exec_time}s")

def main():
    """Test Format Decision Agent with various query types"""
    
    print_section("NEO CHATBOT - 3-AGENT AGENTIC AI SYSTEM TEST")
    print("Testing: Format Decision Agent -> Response Agent -> Verification Agent")
    
    # Initialize agentic service
    print("\nInitializing agentic service...")
    agentic_service = get_agentic_service()
    
    if not agentic_service:
        print("[ERROR] Could not initialize agentic service")
        return
    
    print("[OK] Agentic service initialized")
    
    # Test cases with different format requirements
    test_cases = [
        {
            "name": "Brief Summary Request",
            "query": "Summarize Sorter Service in 50 words",
            "expected_format": "brief_paragraph"
        },
        {
            "name": "Bullet Points Request",
            "query": "List the key features of cross belt sorter",
            "expected_format": "bullet_list"
        },
        {
            "name": "Detailed Explanation",
            "query": "Explain WCS architecture in detail with sections",
            "expected_format": "detailed_explanation"
        },
        {
            "name": "Simple Question",
            "query": "What is NEO?",
            "expected_format": "brief_paragraph"
        },
        {
            "name": "Step-by-Step Guide",
            "query": "How to configure association mining parameters step by step",
            "expected_format": "numbered_steps"
        },
        {
            "name": "Code Example Request",
            "query": "Show me code example for using vector store service",
            "expected_format": "code_example"
        }
    ]
    
    # Run tests
    for i, test in enumerate(test_cases, 1):
        print_section(f"TEST {i}/{len(test_cases)}: {test['name']}")
        
        # Create request
        request = ChatRequest(
            message=test["query"],
            session_id="test_format_session",
            conversation_history=[]
        )
        
        try:
            # Process through agentic system
            print(f"\n[PROCESSING] {test['query']}")
            response = agentic_service.process_query(request)
            
            # Display results
            print_result(test["query"], response)
            
            # Validate format
            metadata = response.metadata if hasattr(response, 'metadata') and response.metadata else {}
            actual_format = metadata.get('format_decision', '') if isinstance(metadata, dict) else ''
            print(f"\n[VALIDATION]")
            print(f"   Expected: {test['expected_format']}")
            print(f"   Actual: {actual_format}")
            print(f"   Match: {'YES' if test['expected_format'] in actual_format else 'NO'}")
            
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
    
    # Final summary
    print_section("TEST SUMMARY")
    print(f"[OK] Completed {len(test_cases)} test cases")
    print("\nFormat Decision Agent Features Tested:")
    print("  - Brief summary with word limit")
    print("  - Bullet point formatting")
    print("  - Detailed explanation with sections")
    print("  - Simple question handling")
    print("  - Step-by-step numbered guide")
    print("  - Code example inclusion")
    print("\n[DONE] 3-Agent system validation complete!")

if __name__ == "__main__":
    main()
