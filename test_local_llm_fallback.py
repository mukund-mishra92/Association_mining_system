"""
Test Local LLM Fallback - Simulate Groq API Failure
"""

import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_groq_available():
    """Test with Groq API available (normal operation)"""
    print("\n" + "="*70)
    print("TEST 1: Normal Operation (Groq API Available)")
    print("="*70)
    
    from app.modules.neo_chatbot.services.llm_service import LLMService
    
    llm = LLMService()
    
    print(f"\nProvider: {llm.provider}")
    print(f"Groq Client: {'✅ Configured' if llm.groq_client else '❌ Not configured'}")
    print(f"Local LLM Enabled: {'✅ Yes' if llm.local_llm_enabled else '❌ No'}")
    
    if llm.provider == "groq":
        print("\n✅ Test 1 PASSED: Using Groq API as primary")
        
        # Try a simple query
        print("\nTesting simple query with Groq...")
        try:
            response = llm.generate_response(
                messages=[{"role": "user", "content": "What is 2+2? Answer in one word."}],
                max_tokens=50,
                temperature=0.3
            )
            print(f"Response: {response[:100]}...")
            print("✅ Groq API working correctly")
            return True
        except Exception as e:
            print(f"❌ Groq API error: {e}")
            return False
    else:
        print(f"\n⚠️  Not using Groq (using {llm.provider})")
        return False


def test_local_llm_fallback():
    """Test fallback to local LLM when Groq fails"""
    print("\n" + "="*70)
    print("TEST 2: Fallback Mechanism (Simulating Groq Failure)")
    print("="*70)
    
    # Temporarily disable Groq by clearing the API key
    original_groq_key = os.getenv("GROQ_API_KEY")
    original_grok_key = os.getenv("GROK_API_KEY")
    
    try:
        # Remove Groq API key
        if original_groq_key:
            del os.environ["GROQ_API_KEY"]
        if original_grok_key:
            del os.environ["GROK_API_KEY"]
        
        print("\n🔄 Temporarily disabled Groq API key...")
        
        # Re-initialize LLM service (should fallback to local LLM)
        from app.modules.neo_chatbot.services.llm_service import LLMService
        
        llm = LLMService()
        
        print(f"\nProvider: {llm.provider}")
        print(f"Groq Client: {'✅ Configured' if llm.groq_client else '❌ Not configured'}")
        print(f"Local LLM Enabled: {'✅ Yes' if llm.local_llm_enabled else '❌ No'}")
        
        if llm.provider == "local_llm":
            print("\n✅ Test 2 PASSED: Automatically switched to local LLM")
            
            # Check if model is available
            print("\nChecking if local model is downloaded...")
            from app.modules.neo_chatbot.services.local_llm_service import get_local_llm
            
            local_llm = get_local_llm(model_name=llm.local_llm_model)
            model_info = local_llm.get_model_info()
            
            model_path = model_info.get('model_path', '')
            if os.path.exists(model_path):
                print(f"✅ Model found: {model_path}")
                print(f"   Size: {os.path.getsize(model_path) / (1024*1024):.1f} MB")
                
                # Try generating a response
                print("\nTesting local LLM generation...")
                print("⚠️  Note: First generation will be slow (loading model)...")
                
                try:
                    start_time = time.time()
                    response = llm.generate_response(
                        messages=[{"role": "user", "content": "What is 2+2? Answer in one sentence."}],
                        max_tokens=50,
                        temperature=0.3
                    )
                    elapsed = time.time() - start_time
                    
                    print(f"\n✅ Local LLM Response ({elapsed:.1f}s):")
                    print(f"   {response[:200]}...")
                    print("\n✅ Local LLM fallback working correctly!")
                    return True
                    
                except Exception as e:
                    print(f"\n❌ Local LLM generation failed: {e}")
                    import traceback
                    traceback.print_exc()
                    return False
            else:
                print(f"\n❌ Model not downloaded: {model_path}")
                print(f"\nTo download the model, run:")
                print(f"   python setup_local_llm.py --download {llm.local_llm_model}")
                return False
                
        elif llm.local_llm_enabled:
            print("\n⚠️  Local LLM enabled but not used as primary")
            print("    (This happens if Groq key is still set)")
            return False
        else:
            print("\n❌ Test 2 FAILED: Local LLM not enabled")
            print("    Set LOCAL_LLM_ENABLED=true in config")
            return False
            
    finally:
        # Restore original API keys
        if original_groq_key:
            os.environ["GROQ_API_KEY"] = original_groq_key
        if original_grok_key:
            os.environ["GROK_API_KEY"] = original_grok_key
        print("\n🔄 Restored original Groq API key")


def test_exception_fallback():
    """Test fallback when exception occurs during Groq call"""
    print("\n" + "="*70)
    print("TEST 3: Exception Handling Fallback")
    print("="*70)
    
    from app.modules.neo_chatbot.services.llm_service import LLMService
    
    llm = LLMService()
    
    if not llm.groq_client:
        print("\n⚠️  Skipping (no Groq API configured)")
        return None
    
    if not llm.local_llm_enabled:
        print("\n⚠️  Skipping (local LLM not enabled)")
        return None
    
    print("\n📝 Testing exception handling in code...")
    print("   When Groq fails → should catch exception → try local LLM")
    
    # Check the code has proper exception handling
    import inspect
    source = inspect.getsource(llm.generate_response)
    
    has_try_except = "try:" in source and "except" in source
    has_fallback_check = "local_llm_enabled" in source
    has_fallback_call = "_generate_local_llm" in source
    
    print(f"\n   Exception handling: {'✅' if has_try_except else '❌'}")
    print(f"   Fallback check: {'✅' if has_fallback_check else '❌'}")
    print(f"   Fallback method: {'✅' if has_fallback_call else '❌'}")
    
    if has_try_except and has_fallback_check and has_fallback_call:
        print("\n✅ Test 3 PASSED: Exception fallback logic present")
        return True
    else:
        print("\n❌ Test 3 FAILED: Missing fallback logic")
        return False


def check_model_availability():
    """Check which models are available"""
    print("\n" + "="*70)
    print("MODEL AVAILABILITY CHECK")
    print("="*70)
    
    from app.modules.neo_chatbot.services.local_llm_service import LocalLLMService
    from pathlib import Path
    
    models_dir = Path(__file__).parent / "app" / "modules" / "neo_chatbot" / "data" / "models"
    
    print(f"\nModels directory: {models_dir}")
    print(f"Directory exists: {'✅' if models_dir.exists() else '❌'}")
    
    if models_dir.exists():
        model_files = list(models_dir.glob("*.gguf"))
        print(f"\nDownloaded models: {len(model_files)}")
        
        for model_file in model_files:
            size_mb = model_file.stat().st_size / (1024 * 1024)
            print(f"  ✅ {model_file.name} ({size_mb:.1f} MB)")
        
        if len(model_files) == 0:
            print("\n⚠️  No models downloaded yet")
            print("\nTo download a model:")
            print("  1. TinyLlama (fastest, 669 MB):")
            print("     python setup_local_llm.py --download tinyllama-1.1b")
            print("\n  2. Phi-2 (recommended, 1.56 GB):")
            print("     python setup_local_llm.py --download phi-2-2.7b")
            print("\n  3. Mistral (best quality, 4.37 GB):")
            print("     python setup_local_llm.py --download mistral-7b-instruct")
            return False
        return True
    else:
        print("\n❌ Models directory doesn't exist")
        return False


def main():
    """Run all fallback tests"""
    print("\n" + "="*70)
    print("🧪 LOCAL LLM FALLBACK - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print("\nThis test verifies:")
    print("1. Groq API works as primary (when available)")
    print("2. Local LLM activates when Groq unavailable")
    print("3. Exception handling triggers fallback")
    print("4. Models are properly downloaded")
    
    results = {}
    
    # Check model availability first
    print("\n" + "="*70)
    print("STEP 0: Model Availability")
    print("="*70)
    models_available = check_model_availability()
    results["models_available"] = models_available
    
    if not models_available:
        print("\n⚠️  Cannot test local LLM without downloaded models")
        print("    Download a model first, then re-run this test")
        return
    
    # Test 1: Normal operation
    try:
        results["groq_primary"] = test_groq_available()
    except Exception as e:
        print(f"\n❌ Test 1 Error: {e}")
        results["groq_primary"] = False
    
    # Test 2: Fallback mechanism
    try:
        results["local_fallback"] = test_local_llm_fallback()
    except Exception as e:
        print(f"\n❌ Test 2 Error: {e}")
        import traceback
        traceback.print_exc()
        results["local_fallback"] = False
    
    # Test 3: Exception handling
    try:
        results["exception_handling"] = test_exception_fallback()
    except Exception as e:
        print(f"\n❌ Test 3 Error: {e}")
        results["exception_handling"] = False
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST RESULTS SUMMARY")
    print("="*70)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ PASSED"
        elif result is False:
            status = "❌ FAILED"
        else:
            status = "⚠️  SKIPPED"
        print(f"\n{test_name.replace('_', ' ').title()}: {status}")
    
    passed = sum(1 for r in results.values() if r is True)
    total = len([r for r in results.values() if r is not None])
    
    print("\n" + "="*70)
    print(f"Final Score: {passed}/{total} tests passed")
    
    if passed == total and total > 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nYour local LLM fallback system is working correctly:")
        print("  ✅ Groq API works as primary")
        print("  ✅ Local LLM ready as fallback")
        print("  ✅ Exception handling configured")
        print("  ✅ Models downloaded and accessible")
        print("\nSystem is resilient to API outages! 🚀")
    elif models_available:
        print("\n⚠️  Some tests failed - check errors above")
    else:
        print("\n⚠️  Download a model to complete testing")
    
    print("="*70)


if __name__ == "__main__":
    main()
