#!/usr/bin/env python3
"""
Simple Test Script for Bin Velocity Analysis System
Quick validation of the velocity system with existing sku_master and order tables
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

try:
    # Import required modules
    from app.shared.config.config import Config
    from app.modules.velocity_analysis.services.velocity_service import VelocityAnalysisService
    print("✅ Successfully imported velocity modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_velocity_system():
    """Quick test of the velocity system"""
    print("\n🚀 TESTING BIN VELOCITY ANALYSIS SYSTEM")
    print("="*50)
    
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
        print(f"✅ Database config loaded: {db_config.get('host', 'localhost')}:{db_config.get('port', 3306)}")
        
        # Initialize velocity service
        velocity_service = VelocityAnalysisService(db_config)
        print("✅ Velocity service initialized")
        
        # Test database connection
        if velocity_service.connect_database():
            print("✅ Database connection successful")
            
            # Check existing tables
            cursor = velocity_service.connection.cursor()
            
            # Check sku_master table
            try:
                cursor.execute("SELECT COUNT(*) FROM sku_master")
                sku_count = cursor.fetchone()[0]
                print(f"✅ sku_master table: {sku_count} records")
            except Exception as e:
                print(f"❌ sku_master table error: {e}")
                return False
            
            # Check order table (wms_to_wcs_order_line_request_data)
            try:
                cursor.execute("SELECT COUNT(*) FROM wms_to_wcs_order_line_request_data")
                order_count = cursor.fetchone()[0]
                print(f"✅ wms_to_wcs_order_line_request_data table: {order_count} records")
            except Exception as e:
                print(f"❌ order table error: {e}")
                return False
            
            # Check velocity column in sku_master
            try:
                cursor.execute("SHOW COLUMNS FROM sku_master LIKE 'velocity'")
                velocity_column = cursor.fetchone()
                if velocity_column:
                    cursor.execute("SELECT COUNT(*) FROM sku_master WHERE velocity IS NOT NULL")
                    velocity_count = cursor.fetchone()[0]
                    print(f"✅ velocity column exists: {velocity_count} SKUs have velocity values")
                else:
                    print("⚠️  velocity column does not exist - will be created during analysis")
            except Exception as e:
                print(f"❌ velocity column check error: {e}")
            
            # Test system status
            try:
                status_result = velocity_service.get_velocity_system_status()
                if status_result["success"]:
                    print("✅ System status check successful")
                    print(f"   System status: {status_result['status']['system_status']}")
                else:
                    print(f"❌ System status check failed: {status_result['message']}")
            except Exception as e:
                print(f"❌ System status error: {e}")
            
            # Test SKU velocity calculation
            print("\n📊 Running SKU velocity analysis...")
            try:
                result = velocity_service.calculate_sku_velocities()
                if result["success"]:
                    stats = result["statistics"]
                    print(f"✅ SKU velocity calculation successful!")
                    print(f"   Updated {stats['total_skus_updated']} SKUs")
                    print(f"   Analyzed {stats['total_skus_analyzed']} SKUs")
                    print(f"   Velocity distribution:")
                    print(f"     High velocity (3): {stats['high_velocity']} SKUs")
                    print(f"     Medium velocity (2): {stats['medium_velocity']} SKUs")
                    print(f"     Low velocity (1): {stats['low_velocity']} SKUs")
                    
                    # Verify sku_master was updated
                    cursor.execute("""
                        SELECT velocity, COUNT(*) as count
                        FROM sku_master 
                        WHERE velocity IS NOT NULL 
                        GROUP BY velocity 
                        ORDER BY velocity DESC
                    """)
                    velocity_data = cursor.fetchall()
                    print(f"   Updated sku_master table:")
                    for row in velocity_data:
                        velocity_name = {3: 'High', 2: 'Medium', 1: 'Low'}.get(row[0], 'Unknown')
                        print(f"     Velocity {row[0]} ({velocity_name}): {row[1]} SKUs")
                        
                else:
                    print(f"❌ SKU velocity calculation failed: {result['message']}")
                    return False
            except Exception as e:
                print(f"❌ SKU velocity calculation error: {e}")
                return False
            
            # Test bin velocity calculation
            print("\n🗂️  Running bin velocity analysis...")
            try:
                result = velocity_service.calculate_bin_velocities()
                if result["success"]:
                    analysis = result["analysis"]
                    print(f"✅ Bin velocity calculation successful!")
                    print(f"   Processed {analysis['total_bins']} bins")
                    print(f"   Average composite score: {analysis.get('average_composite_score', 0):.3f}")
                    
                    # Show top bins
                    cursor.execute("""
                        SELECT bin_id, composite_velocity_score, sku_count, bin_capacity
                        FROM bin_velocity_scores 
                        ORDER BY composite_velocity_score DESC 
                        LIMIT 3
                    """)
                    top_bins = cursor.fetchall()
                    print(f"   Top bins by velocity:")
                    for bin_data in top_bins:
                        print(f"     Bin {bin_data[0]}: Score={bin_data[1]:.3f}, SKUs={bin_data[2]}/{bin_data[3]}")
                        
                else:
                    print(f"❌ Bin velocity calculation failed: {result['message']}")
                    return False
            except Exception as e:
                print(f"❌ Bin velocity calculation error: {e}")
                return False
            
            cursor.close()
            velocity_service.disconnect_database()
            
            print("\n🎉 ALL TESTS PASSED!")
            print("The bin velocity analysis system is working correctly with your existing database.")
            return True
            
        else:
            print("❌ Failed to connect to database")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_velocity_system()
    sys.exit(0 if success else 1)