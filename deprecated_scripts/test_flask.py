"""
Run Flask server for background mode (production settings)
"""
import sys
import os
from pathlib import Path

project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Redirect print output to prevent pipe errors
sys.stdout = open(project_dir / "logs" / "flask_stdout.log", "w", encoding="utf-8", buffering=1)
sys.stderr = open(project_dir / "logs" / "flask_stderr.log", "w", encoding="utf-8", buffering=1)

try:
    print("Importing Flask app...")
    from app.web.main import app
    print("✓ Flask app imported successfully")
    
    print("\nStarting Flask server on port 5000 (production mode)...")
    print("Access at: http://localhost:5000")
    
    # Run without debug mode for background operation
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
