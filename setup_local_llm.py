"""
Local LLM Setup Utility
Downloads and tests local models for fallback when Groq API is unavailable
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.modules.neo_chatbot.services.local_llm_service import LocalLLMService, get_local_llm


def list_available_models():
    """Show all available models"""
    print("\n" + "="*70)
    print("📚 Available Local LLM Models")
    print("="*70)
    
    models = LocalLLMService.list_available_models()
    
    for i, (name, info) in enumerate(models.items(), 1):
        print(f"\n{i}. {name}")
        print(f"   Description: {info['description']}")
        print(f"   Size: {info['size_mb']} MB (~{info['size_mb']/1024:.1f} GB)")
        print(f"   File: {info['filename']}")
    
    print("\n" + "="*70)


def download_model(model_name: str):
    """Download a specific model"""
    print("\n" + "="*70)
    print(f"📥 Downloading Model: {model_name}")
    print("="*70)
    
    try:
        llm = LocalLLMService(model_name=model_name)
        model_path = llm.download_model()
        
        print(f"\n✅ Model downloaded successfully!")
        print(f"   Path: {model_path}")
        print(f"   Size: {model_path.stat().st_size / (1024*1024):.1f} MB")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        return False


def test_model(model_name: str):
    """Test a model with sample queries"""
    print("\n" + "="*70)
    print(f"🧪 Testing Model: {model_name}")
    print("="*70)
    
    try:
        llm = get_local_llm(model_name=model_name)
        
        # Load model
        print("\n🔄 Loading model into memory...")
        if not llm.load_model():
            print("❌ Failed to load model")
            return False
        
        print("✅ Model loaded successfully!")
        
        # Test queries
        test_queries = [
            {
                "name": "SQL Query Generation",
                "messages": [
                    {"role": "system", "content": "You are a SQL expert. Generate SQL queries."},
                    {"role": "user", "content": "Show me all active bots from bot_master table"}
                ]
            },
            {
                "name": "Knowledge Base Question",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant. Answer questions concisely."},
                    {"role": "user", "content": "What is an Automated Storage and Retrieval System?"}
                ]
            },
            {
                "name": "Diagnostic Support",
                "messages": [
                    {"role": "system", "content": "You are a troubleshooting expert. Provide step-by-step solutions."},
                    {"role": "user", "content": "Robot is not picking items from location"}
                ]
            }
        ]
        
        for i, test in enumerate(test_queries, 1):
            print(f"\n{'-'*70}")
            print(f"Test {i}: {test['name']}")
            print(f"{'-'*70}")
            print(f"Query: {test['messages'][-1]['content']}")
            print("\nGenerating response...")
            
            try:
                response = llm.chat(
                    messages=test['messages'],
                    max_tokens=200,
                    temperature=0.3
                )
                
                print(f"\n✅ Response ({len(response)} chars):")
                print(f"{response[:300]}...")  # Show first 300 chars
                
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n" + "="*70)
        print("✅ Model testing complete!")
        print("="*70)
        
        # Unload model
        llm.unload_model()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def setup_recommended_model():
    """Download and test the recommended model (Phi-2)"""
    print("\n" + "="*70)
    print("🚀 Setting Up Recommended Local LLM (Phi-2 2.7B)")
    print("="*70)
    print("\nThis will:")
    print("1. Download Phi-2 2.7B model (1.56 GB)")
    print("2. Load it into memory")
    print("3. Test with sample queries")
    print("4. Configure as fallback for Groq API")
    
    response = input("\nProceed? (y/n): ").strip().lower()
    if response != 'y':
        print("Setup cancelled.")
        return
    
    # Download
    if not download_model("phi-2-2.7b"):
        return
    
    # Test
    if not test_model("phi-2-2.7b"):
        return
    
    # Update .env
    print("\n" + "="*70)
    print("📝 Updating Configuration")
    print("="*70)
    
    env_path = Path(".env")
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        # Add or update LOCAL_LLM settings
        if "LOCAL_LLM_ENABLED" not in env_content:
            with open(env_path, 'a') as f:
                f.write("\n\n# Local LLM Fallback (when Groq API fails)\n")
                f.write("LOCAL_LLM_ENABLED=true\n")
                f.write("LOCAL_LLM_MODEL=phi-2-2.7b\n")
            print("✅ Added LOCAL_LLM settings to .env")
        else:
            print("ℹ️  LOCAL_LLM settings already in .env")
    else:
        print("⚠️  No .env file found. Create one with:")
        print("   LOCAL_LLM_ENABLED=true")
        print("   LOCAL_LLM_MODEL=phi-2-2.7b")
    
    print("\n" + "="*70)
    print("🎉 Setup Complete!")
    print("="*70)
    print("\nLocal LLM is now configured as fallback.")
    print("\nHow it works:")
    print("1. System tries Groq API first")
    print("2. If Groq fails → automatically switches to local Phi-2")
    print("3. Responses may be slower but system stays online")
    
    print("\n💡 Tips:")
    print("- First query will be slower (loading model)")
    print("- Subsequent queries are faster (model stays in memory)")
    print("- Restart server to apply changes")


def interactive_menu():
    """Interactive menu for model management"""
    while True:
        print("\n" + "="*70)
        print("🤖 Local LLM Setup Utility")
        print("="*70)
        print("\n1. List available models")
        print("2. Download model")
        print("3. Test model")
        print("4. Quick setup (recommended: Phi-2)")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            list_available_models()
        
        elif choice == "2":
            list_available_models()
            model_name = input("\nEnter model name: ").strip()
            download_model(model_name)
        
        elif choice == "3":
            list_available_models()
            model_name = input("\nEnter model name: ").strip()
            test_model(model_name)
        
        elif choice == "4":
            setup_recommended_model()
        
        elif choice == "5":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid option. Please select 1-5.")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Local LLM Setup Utility")
    parser.add_argument("--list", action="store_true", help="List available models")
    parser.add_argument("--download", type=str, help="Download specific model")
    parser.add_argument("--test", type=str, help="Test specific model")
    parser.add_argument("--setup", action="store_true", help="Quick setup (Phi-2)")
    parser.add_argument("--interactive", action="store_true", help="Interactive menu")
    
    args = parser.parse_args()
    
    if args.list:
        list_available_models()
    elif args.download:
        download_model(args.download)
    elif args.test:
        test_model(args.test)
    elif args.setup:
        setup_recommended_model()
    elif args.interactive:
        interactive_menu()
    else:
        # Default to interactive menu
        interactive_menu()


if __name__ == "__main__":
    main()
