#!/usr/bin/env python3
"""
Debug version of velocity test to find exact division error location
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

from app.shared.config.config import Config
from app.modules.velocity_analysis.services.velocity_service import VelocityAnalysisService

def debug_velocity_calculation():
    """Debug the SKU velocity calculation to find the exact error"""
    print("🐛 DEBUG: Testing SKU velocity calculation step by step")
    
    try:
        # Get database configuration
        config = Config()
        db_config = {
            'host': config.DB_HOST,
            'port': config.DB_PORT,
            'user': config.DB_USER,
            'password': config.DB_PASSWORD,
            'database': config.DB_NAME
        }
        
        # Initialize velocity service
        velocity_service = VelocityAnalysisService(db_config)
        velocity_service.connect_database()
        
        print("✅ Connected to database")
        
        # Get calculation parameters manually
        try:
            params = velocity_service.get_calculation_parameters()
            print(f"✅ Parameters: {params}")
        except Exception as e:
            print(f"⚠️  Parameters error (using defaults): {e}")
            # Use default parameters
            params = {
                'analysis_period_days': 90,
                'min_orders_for_calculation': 5,
                'high_velocity_threshold': 0.8,
                'medium_velocity_threshold': 0.5,
                'time_decay_rate': 0.05
            }
        
        # Check parameter types
        print(f"🔍 Parameter types:")
        for key, value in params.items():
            print(f"  {key}: {type(value)} = {value}")
        
        # Test a simple SKU velocity calculation manually
        from datetime import date, timedelta
        import math
        
        analysis_date = date.today()
        start_date = analysis_date - timedelta(days=params['analysis_period_days'])
        end_date = analysis_date
        
        print(f"📅 Analysis period: {start_date} to {end_date}")
        
        # Get a small sample of order data
        cursor = velocity_service.connection.cursor(dictionary=True)
        test_query = """
        SELECT 
            ARTICLE_ID as sku_code,
            DATE(INSERTED_TIMESTAMP) as order_date,
            COUNT(*) as daily_orders,
            SUM(QUANTITY) as daily_quantity,
            DATEDIFF(%s, MAX(DATE(INSERTED_TIMESTAMP))) as days_ago
        FROM wms_to_wcs_order_line_request_data 
        WHERE INSERTED_TIMESTAMP BETWEEN %s AND %s
        AND ARTICLE_ID IS NOT NULL AND INSERTED_TIMESTAMP IS NOT NULL
        GROUP BY ARTICLE_ID, DATE(INSERTED_TIMESTAMP)
        ORDER BY ARTICLE_ID, DATE(INSERTED_TIMESTAMP)
        LIMIT 10
        """
        
        cursor.execute(test_query, (end_date, start_date, end_date))
        sample_data = cursor.fetchall()
        
        print(f"📊 Sample data ({len(sample_data)} rows):")
        for row in sample_data[:3]:
            print(f"  Row types: {[(k, type(v), v) for k, v in row.items()]}")
        
        # Test the problematic calculation manually
        sku_metrics = {}
        
        print("🔢 Testing calculation logic...")
        for i, row in enumerate(sample_data[:3]):
            try:
                sku_code = str(row['sku_code'])
                days_ago = int(row['days_ago']) if row['days_ago'] is not None else 0
                daily_orders = int(row['daily_orders']) if row['daily_orders'] is not None else 0
                
                print(f"  Row {i+1}: sku={sku_code}, days_ago={days_ago} ({type(days_ago)}), orders={daily_orders} ({type(daily_orders)})")
                
                if sku_code not in sku_metrics:
                    sku_metrics[sku_code] = {
                        'total_orders': 0.0,
                        'weighted_score': 0.0,
                        'order_days': 0
                    }
                
                # Test the time decay calculation
                time_decay_rate = float(params['time_decay_rate'])
                print(f"    time_decay_rate: {time_decay_rate} ({type(time_decay_rate)})")
                
                time_weight = math.exp(-time_decay_rate * float(days_ago))
                print(f"    time_weight: {time_weight} ({type(time_weight)})")
                
                weighted_orders = float(daily_orders) * time_weight
                print(f"    weighted_orders: {weighted_orders} ({type(weighted_orders)})")
                
                sku_metrics[sku_code]['total_orders'] += float(daily_orders)
                sku_metrics[sku_code]['weighted_score'] += weighted_orders
                sku_metrics[sku_code]['order_days'] += 1
                
                print(f"    ✅ Row {i+1} processed successfully")
                
            except Exception as e:
                print(f"    ❌ Error in row {i+1}: {e}")
                import traceback
                traceback.print_exc()
                break
        
        # Test the division that's causing problems
        print("\n🧮 Testing division operations...")
        for sku_code, metrics in sku_metrics.items():
            try:
                total_orders = float(metrics['total_orders'])
                analysis_period_days = float(params['analysis_period_days'])
                
                print(f"  SKU {sku_code}:")
                print(f"    total_orders: {total_orders} ({type(total_orders)})")
                print(f"    analysis_period_days: {analysis_period_days} ({type(analysis_period_days)})")
                
                order_frequency = total_orders / analysis_period_days
                print(f"    order_frequency: {order_frequency} ({type(order_frequency)}) ✅")
                
            except Exception as e:
                print(f"    ❌ Division error for SKU {sku_code}: {e}")
                import traceback
                traceback.print_exc()
        
        cursor.close()
        velocity_service.disconnect_database()
        
        print("\n🎯 Debug completed!")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_velocity_calculation()