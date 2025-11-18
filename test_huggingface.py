"""
Test HuggingFace Embeddings
Quick script to verify your HuggingFace API key works
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_huggingface_embeddings():
    """Test HuggingFace embedding generation"""
    
    print("=" * 60)
    print("🤗 HuggingFace Embeddings Test")
    print("=" * 60)
    print()
    
    # Check for API key
    hf_key = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")
    
    if not hf_key:
        print("❌ HUGGINGFACE_API_KEY not found in .env file")
        print()
        print("📝 Setup Instructions:")
        print("1. Go to: https://huggingface.co/settings/tokens")
        print("2. Create new token (Read access)")
        print("3. Add to .env file:")
        print("   HUGGINGFACE_API_KEY=hf_your_token_here")
        print()
        return False
    
    print(f"✅ API Key found: {hf_key[:10]}...{hf_key[-5:]}")
    print()
    
    # Test embedding generation
    try:
        print("📦 Loading HuggingFace client...")
        from huggingface_hub import InferenceClient
        
        client = InferenceClient(token=hf_key)
        print("✅ HuggingFace client initialized")
        print()
        
        # Test with sample text
        test_texts = [
            "What is NEO Warehouse Management System?",
            "How does Fleet Management work?",
            "Tell me about station picking"
        ]
        
        print("🧪 Testing embedding generation...")
        print("-" * 60)
        
        for i, text in enumerate(test_texts, 1):
            print(f"\nTest {i}: {text}")
            print("Generating embedding...")
            
            try:
                embedding = client.feature_extraction(
                    text,
                    model="BAAI/bge-small-en-v1.5"
                )
                
                # Flatten if nested
                if isinstance(embedding, list):
                    if isinstance(embedding[0], list):
                        embedding = embedding[0]
                
                print(f"✅ Success! Embedding dimensions: {len(embedding)}")
                print(f"   Sample values: [{embedding[0]:.4f}, {embedding[1]:.4f}, {embedding[2]:.4f}, ...]")
                
                # Calculate magnitude (should be close to 1.0 for normalized embeddings)
                import numpy as np
                magnitude = np.linalg.norm(embedding)
                print(f"   Magnitude: {magnitude:.4f} {'✅ (normalized)' if 0.9 < magnitude < 1.1 else '⚠️ (not normalized)'}")
                
            except Exception as e:
                print(f"❌ Failed: {e}")
                return False
        
        print()
        print("-" * 60)
        print()
        print("=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("✅ Your HuggingFace setup is working perfectly!")
        print("✅ Embeddings: High quality, FREE, unlimited")
        print("✅ Model: BAAI/bge-small-en-v1.5 (384 dimensions)")
        print()
        print("🚀 Your chatbot will now use these FREE embeddings")
        print("   for accurate semantic search and document retrieval!")
        print()
        return True
        
    except ImportError:
        print("❌ huggingface_hub not installed")
        print()
        print("📦 Install it with:")
        print("   pip install huggingface_hub")
        print()
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("🔧 Troubleshooting:")
        print("1. Verify your API key is correct")
        print("2. Check internet connection")
        print("3. Try regenerating token at: https://huggingface.co/settings/tokens")
        print()
        return False


if __name__ == "__main__":
    success = test_huggingface_embeddings()
    
    if success:
        print("✅ Next steps:")
        print("   1. Restart your chatbot application")
        print("   2. Test with: 'What is NEO?'")
        print("   3. Check logs for: '✅ Generated HuggingFace embedding'")
        print()
    else:
        print("❌ Setup incomplete - follow instructions above")
        print()
