#!/usr/bin/env python3
"""
Test script to verify the restructured system works correctly
"""

import sys
import os
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Change to project root directory
os.chdir(project_root)

def test_imports():
    """Test that all imports work correctly"""
    print("Testing imports...")
    
    try:
        # Test shared modules
        from app.shared.config.config import config
        print("✅ Config import: OK")
        
        from app.shared.database.connection import DatabaseConnection
        print("✅ Database connection import: OK")
        
        from app.shared.utils.task_manager import task_manager
        print("✅ Task manager import: OK")
        
        # Test association mining module
        from app.modules.association_mining.api.endpoints import router
        print("✅ Association mining API import: OK")
        
        from app.modules.association_mining.services.clean_mining_service import CleanAssociationMiningService
        print("✅ Association mining service import: OK")
        
        # Test main applications
        import app.main
        print("✅ FastAPI main import: OK")
        
        import app.web.main
        print("✅ Flask web import: OK")
        
        print("\n🎉 All imports successful! The restructured system is working correctly.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_entry_point():
    """Test the main entry point"""
    print("\nTesting main entry point...")
    
    try:
        import main
        print("✅ Main entry point import: OK")
        return True
    except ImportError as e:
        print(f"❌ Main entry point import error: {e}")
        return False

if __name__ == "__main__":
    print("🔗 Association Mining System - Structure Test")
    print("=" * 50)
    
    success = True
    success &= test_imports()
    success &= test_entry_point()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ ALL TESTS PASSED! System structure is correct.")
    else:
        print("❌ SOME TESTS FAILED! Check the imports above.")
    
    print("=" * 50)