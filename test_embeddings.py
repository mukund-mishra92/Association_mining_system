"""
Test Embedding Generation
Verifies LLM service generates correct embedding dimensions
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app.modules.neo_chatbot.services.llm_service import LLMService

def main():
    print("\n" + "="*80)
    print("🧪 EMBEDDING GENERATION TEST")
    print("="*80)
    
    # Initialize service
    print("\n📦 Initializing LLM Service...")
    llm = LLMService()
    
    # Test text
    test_text = "This is a test document for embedding generation."
    print(f"\n📝 Test text: '{test_text}'")
    
    # Generate embedding
    print(f"\n⚡ Generating embedding...")
    embedding = llm.generate_embedding(test_text)
    
    if not embedding:
        print(f"\n❌ FAILED: No embedding generated")
        print(f"   Check LLM service configuration")
        print(f"   Verify OpenAI API key is set")
        print("="*80 + "\n")
        return
    
    # Check dimensions
    dimension = len(embedding)
    print(f"\n📏 Generated Embedding:")
    print(f"   Dimension: {dimension}")
    
    # Expected dimension for OpenAI text-embedding-3-small
    expected = 1536
    
    if dimension == expected:
        print(f"   ✅ CORRECT: Matches OpenAI standard ({expected} dimensions)")
    else:
        print(f"   ❌ MISMATCH: Expected {expected}, got {dimension}")
        print(f"\n⚠️  This will cause issues when querying!")
        print(f"\n🔧 Possible causes:")
        print(f"   1. Using fallback embedding generation")
        print(f"   2. Different embedding model configured")
        print(f"   3. Mock embeddings being used")
    
    # Sample values
    print(f"\n📊 Sample values (first 10):")
    print(f"   {embedding[:10]}")
    
    # Check if all zeros
    if all(v == 0.0 for v in embedding):
        print(f"\n   ⚠️  WARNING: All zeros detected!")
        print(f"   This suggests mock/fallback embeddings")
        print(f"   💡 Set OPENAI_API_KEY for real embeddings")
    
    # Check range
    min_val = min(embedding)
    max_val = max(embedding)
    print(f"\n📈 Value range:")
    print(f"   Min: {min_val:.6f}")
    print(f"   Max: {max_val:.6f}")
    
    # OpenAI embeddings typically range from -1 to 1
    if -1.5 < min_val < 1.5 and -1.5 < max_val < 1.5:
        print(f"   ✅ Reasonable range for normalized embeddings")
    else:
        print(f"   ⚠️  Unusual range - check embedding generation")
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
