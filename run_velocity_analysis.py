#!/usr/bin/env python3
"""
🚀 Velocity Analysis System - Quick Start Script

This script provides an easy way to run the complete velocity analysis system.
It includes system checks, velocity calculations, and result verification.

Usage:
    python run_velocity_analysis.py [--sku-only] [--bin-only] [--check-only]
"""

import sys
import os
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, '.')

try:
    from app.shared.config.config import Config
    from app.modules.velocity_analysis.services.velocity_service import VelocityAnalysisService
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Please ensure you're running from the project root directory and virtual environment is activated.")
    sys.exit(1)

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)

def print_success(message):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"❌ {message}")

def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")

def check_system_requirements():
    """Check if all system requirements are met"""
    print_header("SYSTEM REQUIREMENTS CHECK")
    
    try:
        # Check configuration
        config = Config()
        print_success(f"Configuration loaded successfully")
        print_info(f"Database: {config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}")
        print_info(f"User: {config.DB_USER}")
        
        # Initialize service
        db_config = {
            'host': config.DB_HOST,
            'port': config.DB_PORT,
            'user': config.DB_USER,
            'password': config.DB_PASSWORD,
            'database': config.DB_NAME
        }
        
        service = VelocityAnalysisService(db_config)
        service.connect_database()
        print_success("Database connection established")
        
        # Check required tables
        cursor = service.connection.cursor()
        required_tables = [
            'sku_master',
            'wms_to_wcs_order_line_request_data', 
            'velocity_calculation_config',
            'sku_velocity_history'
        ]
        
        for table in required_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print_success(f"{table}: {count:,} records")
            except Exception as e:
                print_error(f"{table}: Not accessible - {e}")
                return False
        
        # Check velocity configuration
        params = service.get_calculation_parameters()
        print_success("Velocity configuration loaded")
        print_info(f"Analysis period: {params['analysis_period_days']} days")
        print_info(f"Min orders threshold: {params['min_orders_for_calculation']}")
        
        cursor.close()
        service.disconnect_database()
        return True
        
    except Exception as e:
        print_error(f"System check failed: {e}")
        return False

def run_sku_velocity_analysis():
    """Run SKU velocity analysis"""
    print_header("SKU VELOCITY ANALYSIS")
    
    try:
        config = Config()
        db_config = {
            'host': config.DB_HOST,
            'port': config.DB_PORT,
            'user': config.DB_USER,
            'password': config.DB_PASSWORD,
            'database': config.DB_NAME
        }
        
        service = VelocityAnalysisService(db_config)
        service.connect_database()
        
        print_info("Starting SKU velocity calculation...")
        start_time = datetime.now()
        
        result = service.calculate_sku_velocities()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if result['success']:
            stats = result['statistics']
            print_success(f"SKU velocity analysis completed in {duration:.2f} seconds")
            print(f"   📊 Total SKUs Updated: {stats['total_skus_updated']:,}")
            print(f"   📊 Total SKUs Analyzed: {stats['total_skus_analyzed']:,}")
            print(f"   🔴 High Velocity (3): {stats['high_velocity']:,} SKUs ({stats['high_velocity']/stats['total_skus_analyzed']*100:.1f}%)")
            print(f"   🟡 Medium Velocity (2): {stats['medium_velocity']:,} SKUs ({stats['medium_velocity']/stats['total_skus_analyzed']*100:.1f}%)")
            print(f"   🟢 Low Velocity (1): {stats['low_velocity']:,} SKUs ({stats['low_velocity']/stats['total_skus_analyzed']*100:.1f}%)")
            
            # Verify results
            cursor = service.connection.cursor()
            cursor.execute("""
                SELECT VELOCITY, COUNT(*) as count 
                FROM sku_master 
                WHERE VELOCITY IS NOT NULL 
                GROUP BY VELOCITY 
                ORDER BY VELOCITY DESC
            """)
            
            print("\n   📈 sku_master table verification:")
            for row in cursor.fetchall():
                velocity_name = {3: 'High', 2: 'Medium', 1: 'Low'}.get(row[0], f'Level {row[0]}')
                print(f"      Velocity {row[0]} ({velocity_name}): {row[1]:,} SKUs")
            
            cursor.close()
            
        else:
            print_error(f"SKU velocity analysis failed: {result['message']}")
            service.disconnect_database()
            return False
        
        service.disconnect_database()
        return True
        
    except Exception as e:
        print_error(f"SKU velocity analysis error: {e}")
        return False

def run_bin_velocity_analysis():
    """Run bin velocity analysis"""
    print_header("BIN VELOCITY ANALYSIS")
    
    try:
        config = Config()
        db_config = {
            'host': config.DB_HOST,
            'port': config.DB_PORT,
            'user': config.DB_USER,
            'password': config.DB_PASSWORD,
            'database': config.DB_NAME
        }
        
        service = VelocityAnalysisService(db_config)
        service.connect_database()
        
        # Check if bin_configuration data exists
        cursor = service.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM bin_configuration WHERE is_active = 1")
        bin_count = cursor.fetchone()[0]
        
        if bin_count == 0:
            print_info("No active bin configuration data found")
            print_info("Bin velocity analysis requires data in bin_configuration table")
            cursor.close()
            service.disconnect_database()
            return True
        
        print_info(f"Found {bin_count:,} active bin configurations")
        print_info("Starting bin velocity calculation...")
        
        start_time = datetime.now()
        result = service.calculate_bin_velocities()
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if result['success']:
            print_success(f"Bin velocity analysis completed in {duration:.2f} seconds")
            print_info(f"Result: {result.get('message', 'Analysis completed successfully')}")
        else:
            print_error(f"Bin velocity analysis failed: {result['message']}")
            
        cursor.close()
        service.disconnect_database()
        return result['success']
        
    except Exception as e:
        print_error(f"Bin velocity analysis error: {e}")
        return False

def get_system_status():
    """Get and display system status"""
    print_header("SYSTEM STATUS")
    
    try:
        config = Config()
        db_config = {
            'host': config.DB_HOST,
            'port': config.DB_PORT,
            'user': config.DB_USER,
            'password': config.DB_PASSWORD,
            'database': config.DB_NAME
        }
        
        service = VelocityAnalysisService(db_config)
        service.connect_database()
        
        result = service.get_velocity_system_status()
        
        if result['success']:
            status = result['status']
            print_success("System status retrieved successfully")
            
            for metric_type, data in status.items():
                print(f"   📊 {metric_type.replace('_', ' ').title()}: {data['count']:,} records")
                if data['last_update']:
                    print(f"      Last updated: {data['last_update']}")
        else:
            print_error(f"Could not retrieve system status: {result['message']}")
        
        service.disconnect_database()
        
    except Exception as e:
        print_error(f"System status error: {e}")

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Velocity Analysis System Runner")
    parser.add_argument('--sku-only', action='store_true', help='Run only SKU velocity analysis')
    parser.add_argument('--bin-only', action='store_true', help='Run only bin velocity analysis')
    parser.add_argument('--check-only', action='store_true', help='Run only system checks')
    
    args = parser.parse_args()
    
    print_header("VELOCITY ANALYSIS SYSTEM")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Always run system check first
    if not check_system_requirements():
        print_error("System requirements check failed. Please resolve issues before proceeding.")
        return 1
    
    if args.check_only:
        get_system_status()
        print_success("System check completed successfully")
        return 0
    
    success = True
    
    # Run SKU velocity analysis
    if not args.bin_only:
        success &= run_sku_velocity_analysis()
    
    # Run bin velocity analysis
    if not args.sku_only and success:
        success &= run_bin_velocity_analysis()
    
    # Show final status
    get_system_status()
    
    print_header("EXECUTION SUMMARY")
    if success:
        print_success("All velocity analysis operations completed successfully!")
        print_info("The system is ready for production use.")
    else:
        print_error("Some operations failed. Please check the logs above.")
        return 1
    
    print(f"🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return 0

if __name__ == "__main__":
    sys.exit(main())