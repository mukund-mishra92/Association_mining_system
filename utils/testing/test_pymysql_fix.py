#!/usr/bin/env python3
"""
Quick verification script to test that the PyMySQL issue is resolved
"""

import sys
import os
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

def test_pymysql_import():
    """Test that PyMySQL imports correctly"""
    print("Testing PyMySQL import...")
    try:
        import pymysql
        print("✅ PyMySQL import: OK")
        return True
    except ImportError as e:
        print(f"❌ PyMySQL import failed: {e}")
        return False

def test_flask_imports():
    """Test that Flask app imports work"""
    print("Testing Flask app imports...")
    try:
        from app.web.main import app
        print("✅ Flask app import: OK")
        return True
    except ImportError as e:
        print(f"❌ Flask app import failed: {e}")
        return False

def test_fastapi_imports():
    """Test that FastAPI app imports work"""
    print("Testing FastAPI app imports...")
    try:
        from app.main import app
        print("✅ FastAPI app import: OK")
        return True
    except ImportError as e:
        print(f"❌ FastAPI app import failed: {e}")
        return False

def test_database_connection():
    """Test database connection class"""
    print("Testing database connection...")
    try:
        from app.shared.database.connection import DatabaseConnection
        print("✅ Database connection import: OK")
        return True
    except ImportError as e:
        print(f"❌ Database connection import failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 PyMySQL Fix Verification")
    print("=" * 40)
    
    success = True
    success &= test_pymysql_import()
    success &= test_database_connection()
    success &= test_flask_imports()
    success &= test_fastapi_imports()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ ALL TESTS PASSED! PyMySQL issue is resolved.")
        print("🚀 Both Flask and FastAPI should start without import errors.")
    else:
        print("❌ SOME TESTS FAILED! Check the imports above.")
    
    print("=" * 40)