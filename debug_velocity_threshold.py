#!/usr/bin/env python3
"""Debug script to check minimum order threshold and actual order counts."""

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
        
        # Get calculation parameters
        params = service.get_calculation_parameters()
        print(f"Min orders threshold: {params['min_orders_for_calculation']}")
        
        # Check actual order counts for SKUs
        cursor = service.connection.cursor()
        cursor.execute("""
            SELECT ARTICLE_ID, COUNT(*) as order_count 
            FROM wms_to_wcs_order_line_request_data 
            WHERE INSERTED_TIMESTAMP >= DATE_SUB(CURDATE(), INTERVAL 90 DAY) 
            AND ARTICLE_ID IS NOT NULL 
            GROUP BY ARTICLE_ID 
            ORDER BY order_count DESC 
            LIMIT 10
        """)
        
        top_skus = cursor.fetchall()
        print("\nTop 10 SKUs by order count (last 90 days):")
        for row in top_skus:
            print(f"  {row[0]}: {row[1]} orders")
        
        # Check how many SKUs meet the threshold (correct query)
        cursor.execute("""
            SELECT COUNT(*) as qualifying_skus
            FROM (
                SELECT ARTICLE_ID, COUNT(*) as order_count
                FROM wms_to_wcs_order_line_request_data 
                WHERE INSERTED_TIMESTAMP >= DATE_SUB(CURDATE(), INTERVAL 90 DAY) 
                AND ARTICLE_ID IS NOT NULL 
                GROUP BY ARTICLE_ID 
                HAVING COUNT(*) >= %s
            ) subquery
        """, (params['min_orders_for_calculation'],))
        
        result = cursor.fetchone()
        qualifying_skus = result[0] if result else 0
        print(f"\nSKUs meeting minimum threshold ({params['min_orders_for_calculation']} orders): {qualifying_skus}")
        
        # Also check total unique SKUs
        cursor.execute("""
            SELECT COUNT(DISTINCT ARTICLE_ID) as total_skus
            FROM wms_to_wcs_order_line_request_data 
            WHERE INSERTED_TIMESTAMP >= DATE_SUB(CURDATE(), INTERVAL 90 DAY) 
            AND ARTICLE_ID IS NOT NULL
        """)
        
        result = cursor.fetchone()
        total_skus = result[0] if result else 0
        print(f"Total unique SKUs with orders in last 90 days: {total_skus}")
        
        cursor.close()
        service.disconnect_database()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()