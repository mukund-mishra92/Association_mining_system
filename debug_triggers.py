#!/usr/bin/env python3
"""Debug script to check triggers on sku_master table."""

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
        
        print("Checking triggers on sku_master table...")
        
        cursor = service.connection.cursor()
        
        # Check triggers
        cursor.execute("SHOW TRIGGERS LIKE 'sku_master'")
        triggers = cursor.fetchall()
        
        print(f"Found {len(triggers)} triggers on sku_master:")
        for trigger in triggers:
            print(f"  {trigger}")
        
        # Check if we can at least read from sku_master
        cursor.execute("SELECT COUNT(*) as total_rows FROM sku_master")
        count_result = cursor.fetchone()
        print(f"\nsku_master table has {count_result[0]} rows")
        
        # Check specific SKU that we know exists
        cursor.execute("SELECT SKU_ID, VELOCITY FROM sku_master WHERE SKU_ID = '0018584e-5eef-48ae-b668-39b432e86532'")
        sku_result = cursor.fetchone()
        if sku_result:
            print(f"Sample SKU: {sku_result[0]}, Current velocity: {sku_result[1]}")
        else:
            print("Sample SKU not found in sku_master")
        
        cursor.close()
        service.disconnect_database()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()