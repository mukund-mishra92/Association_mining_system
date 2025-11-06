#!/usr/bin/env python3
"""Debug script to trace the exact error in SKU velocity calculation."""

import sys
import os
sys.path.insert(0, '.')

from app.shared.config.config import Config
from app.modules.velocity_analysis.services.velocity_service import VelocityAnalysisService
from datetime import date, timedelta
import math

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
        
        print("Manual SKU velocity calculation trace...")
        
        # Get parameters
        params = service.get_calculation_parameters()
        print(f"Parameters: {params}")
        
        # Get order data manually
        analysis_date = date.today()
        end_date = analysis_date
        start_date = end_date - timedelta(days=int(params['analysis_period_days']))
        
        cursor = service.connection.cursor(dictionary=True)
        
        order_query = """
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
        LIMIT 20
        """
        
        cursor.execute(order_query, (end_date, start_date, end_date))
        order_data = cursor.fetchall()
        
        print(f"Found {len(order_data)} order records")
        
        if order_data:
            print("Sample order records:")
            for i, row in enumerate(order_data[:5]):
                print(f"  {i+1}. SKU: {row['sku_code']}, Orders: {row['daily_orders']}, Days ago: {row['days_ago']}")
        
        # Process a few records manually
        sku_metrics = {}
        
        for row in order_data[:10]:  # Process only first 10 for debugging
            sku_code = str(row['sku_code'])
            days_ago = int(row['days_ago']) if row['days_ago'] is not None else 0
            daily_orders = int(row['daily_orders']) if row['daily_orders'] is not None else 0
            
            if sku_code not in sku_metrics:
                sku_metrics[sku_code] = {
                    'total_orders': 0.0,
                    'weighted_score': 0.0,
                    'order_days': 0
                }
            
            # Apply time decay: more recent orders have higher weight
            time_weight = math.exp(-float(params['time_decay_rate']) * float(days_ago))
            weighted_orders = float(daily_orders) * time_weight
            
            sku_metrics[sku_code]['total_orders'] += float(daily_orders)
            sku_metrics[sku_code]['weighted_score'] += weighted_orders
            sku_metrics[sku_code]['order_days'] += 1
            
            print(f"SKU {sku_code}: days_ago={days_ago}, time_weight={time_weight:.4f}, weighted_orders={weighted_orders:.4f}")
        
        print(f"\nSKU metrics calculated:")
        for sku, metrics in sku_metrics.items():
            print(f"  {sku}: total_orders={metrics['total_orders']}, weighted_score={metrics['weighted_score']:.4f}")
        
        # Filter SKUs with minimum order threshold
        filtered_skus = {
            sku: metrics for sku, metrics in sku_metrics.items()
            if metrics['total_orders'] >= params['min_orders_for_calculation']
        }
        
        print(f"\nFiltered SKUs (meeting threshold {params['min_orders_for_calculation']}): {len(filtered_skus)}")
        
        if filtered_skus:
            weighted_scores = [float(metrics['weighted_score']) for metrics in filtered_skus.values()]
            print(f"Weighted scores: {weighted_scores}")
            
            # Try the percentile calculation that might be failing
            try:
                import numpy as np
                high_threshold = np.percentile(weighted_scores, params['high_velocity_threshold'] * 100)
                medium_threshold = np.percentile(weighted_scores, params['medium_velocity_threshold'] * 100)
                print(f"Thresholds calculated: high={high_threshold}, medium={medium_threshold}")
            except Exception as np_error:
                print(f"❌ Numpy percentile error: {np_error}")
                print(f"Error type: {type(np_error)}")
        
        cursor.close()
        service.disconnect_database()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()