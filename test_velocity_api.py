#!/usr/bin/env python3
"""
Test script to debug velocity analysis API issues
"""

import sys
import os

# Add the current directory to Python path
sys.path.append('.')

from flask import Flask
import requests
import json

def test_velocity_api():
    """Test velocity analysis API registration and endpoints"""
    
    print("🔍 Testing Velocity Analysis API...")
    
    # Create Flask app
    app = Flask(__name__)
    
    # Try to register velocity API
    try:
        from app.modules.velocity_analysis.api.velocity_endpoints import register_velocity_api
        register_velocity_api(app)
        print("✅ Velocity API registered successfully")
        
        # Check if blueprints are registered
        for blueprint_name, blueprint in app.blueprints.items():
            print(f"📋 Blueprint: {blueprint_name} -> URL Prefix: {blueprint.url_prefix}")
            
        # Start test server
        @app.route('/test')
        def test_endpoint():
            return {'status': 'Test server working'}
            
        print("\n🚀 Starting test server on port 5001...")
        print("Test endpoints:")
        print("- Basic test: http://localhost:5001/test")
        print("- Velocity connection: http://localhost:5001/api/velocity/test-connection")
        
        app.run(host='0.0.0.0', port=5001, debug=True)
        
    except ImportError as e:
        print(f"❌ Failed to import velocity API: {e}")
        return False
    except Exception as e:
        print(f"❌ Error registering velocity API: {e}")
        return False

if __name__ == "__main__":
    test_velocity_api()