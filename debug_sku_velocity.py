#!/usr/bin/env python3
"""Debug script to test SKU velocity calculation step by step."""

import sys
import os
sys.path.insert(0, '.')

from app.shared.config.config import Config
from app.modules.velocity_analysis.services.velocity_service import VelocityAnalysisService

def main():
    try:
        # Initialize configuration
        config = Config()
        db_config = {
            'host': config.DB_HOST,
            'port': config.DB_PORT,
            'user': config.DB_USER,
            'password': config.DB_PASSWORD,
            'database': config.DB_NAME
        }
        
        # Initialize service
        service = VelocityAnalysisService(db_config)
        service.connect_database()
        
        print("Testing SKU velocity calculation...")
        
        # Call the actual calculation method
        try:
            result = service.calculate_sku_velocities()
            
            print(f"Success: {result.get('success', False)}")
            print(f"Message: {result.get('message', 'No message')}")
            
            if result.get('success'):
                print(f"Statistics: {result.get('statistics', {})}")
                print(f"Parameters used: {result.get('parameters_used', {})}")
            else:
                print("❌ Calculation failed")
                print(f"Full result: {result}")
                
        except Exception as calc_error:
            print(f"❌ Exception during calculation: {calc_error}")
            print(f"Exception type: {type(calc_error)}")
            import traceback
            traceback.print_exc()
            
        service.disconnect_database()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()