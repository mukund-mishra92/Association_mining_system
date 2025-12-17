"""
Download Local LLM Models for Offline Fallback
Automatically downloads and verifies GGUF models
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.modules.neo_chatbot.services.local_llm_service import LocalLLMService

def main():
    print("=" * 60)
    print("📦 LOCAL LLM MODEL DOWNLOADER")
    print("=" * 60)
    print()
    
    # Show available models
    print("Available models:")
    for name, info in LocalLLMService.AVAILABLE_MODELS.items():
        print(f"  • {name}: {info['description']} ({info['size_mb']} MB)")
    print()
    
    # Ask user which model to download
    print("Which model would you like to download?")
    print("1. tinyllama-1.1b (Fast, 669 MB) - RECOMMENDED")
    print("2. phi-2-2.7b (Better quality, 1560 MB)")
    print("3. mistral-7b-instruct (Best quality, 4370 MB - requires good hardware)")
    print("4. All models")
    print()
    
    choice = input("Enter choice (1-4) [default: 1]: ").strip() or "1"
    
    models_to_download = []
    if choice == "1":
        models_to_download = ["tinyllama-1.1b"]
    elif choice == "2":
        models_to_download = ["phi-2-2.7b"]
    elif choice == "3":
        models_to_download = ["mistral-7b-instruct"]
    elif choice == "4":
        models_to_download = list(LocalLLMService.AVAILABLE_MODELS.keys())
    else:
        print("❌ Invalid choice")
        return
    
    print()
    print("=" * 60)
    print("📥 DOWNLOADING MODELS")
    print("=" * 60)
    print()
    
    for model_name in models_to_download:
        try:
            print(f"Downloading {model_name}...")
            llm_service = LocalLLMService(model_name=model_name)
            model_path = llm_service.download_model()
            print(f"✅ Downloaded: {model_path}")
            print()
            
            # Try to load the model to verify it works
            print(f"🔍 Verifying {model_name}...")
            if llm_service.load_model():
                print(f"✅ Model verified successfully!")
                
                # Test generation
                print("🧪 Testing generation...")
                response = llm_service.generate(
                    prompt="Q: What is 2+2?\nA:",
                    max_tokens=10,
                    temperature=0.0
                )
                print(f"Test response: {response}")
                print(f"✅ {model_name} is working!")
            else:
                print(f"❌ Failed to verify {model_name}")
            
            print()
            
        except Exception as e:
            print(f"❌ Error downloading {model_name}: {e}")
            print()
    
    print("=" * 60)
    print("✅ DOWNLOAD COMPLETE")
    print("=" * 60)
    print()
    print("The local LLM fallback is now configured.")
    print("Restart your chatbot server for changes to take effect.")

if __name__ == "__main__":
    main()
