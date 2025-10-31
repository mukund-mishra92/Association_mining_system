#!/usr/bin/env python3
"""
Test script to verify remote database configuration compatibility 
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_remote_database_config():
    """Test that remote database configuration is supported"""
    try:
        from app.shared.database.connection import DatabaseConnection
        from app.modules.association_mining.services.scheduler_service import SchedulerService
        
        logger.info("✅ Testing remote database configuration support...")
        
        # Test 1: Database connection with custom config
        logger.info("🧪 Test 1: DatabaseConnection with custom config")
        
        # Example remote database configuration
        remote_config = {
            'host': '192.168.1.100',  # Example remote IP
            'port': 3306,
            'user': 'remote_user',
            'password': 'remote_password',
            'database': 'remote_neo',
            'order_table': 'remote_orders',
            'sku_master_table': 'remote_sku_master',
            'recommendations_table': 'remote_recommendations'
        }
        
        # Create database connection with custom config
        db_conn = DatabaseConnection(custom_config=remote_config)
        
        # Verify configuration was set correctly
        if (db_conn.db_host == '192.168.1.100' and
            db_conn.db_port == 3306 and
            db_conn.db_user == 'remote_user' and
            db_conn.db_name == 'remote_neo'):
            logger.info("✅ DatabaseConnection accepts and uses custom configuration")
        else:
            logger.error("❌ DatabaseConnection not using custom configuration correctly")
            return False
        
        # Test 2: Scheduler service with custom config
        logger.info("🧪 Test 2: SchedulerService with custom config")
        
        scheduler = SchedulerService(db_config=remote_config)
        
        # Verify scheduler is using custom config
        if (scheduler.db_connection.db_host == '192.168.1.100' and
            scheduler.db_connection.db_user == 'remote_user'):
            logger.info("✅ SchedulerService accepts and uses custom database configuration")
        else:
            logger.error("❌ SchedulerService not using custom configuration correctly")
            return False
            
        # Test 3: Check API endpoint compatibility
        logger.info("🧪 Test 3: API endpoint configuration support")
        
        try:
            from app.modules.association_mining.api.endpoints import DatabaseConfig
            
            # Test Pydantic model for database config
            api_config = DatabaseConfig(
                host='192.168.1.100',
                port=3306,
                user='api_user',
                password='api_password',
                database='api_database'
            )
            
            if api_config.host == '192.168.1.100':
                logger.info("✅ API endpoints support DatabaseConfig model")
            else:
                logger.error("❌ API DatabaseConfig model not working")
                return False
                
        except Exception as e:
            logger.error(f"❌ API configuration test failed: {e}")
            return False
        
        # Test 4: Check Flask UI configuration
        logger.info("🧪 Test 4: Flask UI configuration support")
        
        try:
            from app.web.main import USER_DB_CONFIG
            
            if isinstance(USER_DB_CONFIG, dict) and 'host' in USER_DB_CONFIG:
                logger.info("✅ Flask UI has USER_DB_CONFIG for remote database support")
                logger.info(f"   Default host: {USER_DB_CONFIG['host']}")
                logger.info(f"   Default database: {USER_DB_CONFIG['database']}")
            else:
                logger.error("❌ Flask UI USER_DB_CONFIG not properly configured")
                return False
                
        except Exception as e:
            logger.error(f"❌ Flask UI configuration test failed: {e}")
            return False
        
        logger.info("🎉 All remote database configuration tests passed!")
        logger.info("📡 Remote database support is fully maintained in production-ready-v2")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing remote database configuration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def show_remote_config_example():
    """Show examples of how to use remote database configuration"""
    logger.info("💡 Remote Database Configuration Examples:")
    logger.info("=" * 60)
    
    logger.info("📂 1. Environment (.env) Configuration:")
    logger.info("   DB_HOST=192.168.1.100")
    logger.info("   DB_PORT=3306")
    logger.info("   DB_USER=remote_user")
    logger.info("   DB_PASSWORD=remote_password")
    logger.info("   DB_NAME=remote_database")
    logger.info("")
    
    logger.info("🌐 2. Flask UI Configuration:")
    logger.info("   Visit: http://localhost:5000/db-config")
    logger.info("   Update database settings through the web interface")
    logger.info("")
    
    logger.info("🚀 3. API Configuration (FastAPI):")
    logger.info("   POST /api/mine-associations")
    logger.info("   Include 'db_config' in request body:")
    logger.info("   {")
    logger.info("     'db_config': {")
    logger.info("       'host': '192.168.1.100',")
    logger.info("       'port': 3306,")
    logger.info("       'user': 'remote_user',")
    logger.info("       'password': 'remote_password',")
    logger.info("       'database': 'remote_database'")
    logger.info("     }")
    logger.info("   }")
    logger.info("")
    
    logger.info("⏰ 4. Scheduler Configuration:")
    logger.info("   from app.modules.association_mining.services.scheduler_service import SchedulerService")
    logger.info("   remote_config = {'host': '192.168.1.100', ...}")
    logger.info("   scheduler = SchedulerService(db_config=remote_config)")

if __name__ == "__main__":
    logger.info("🧪 Testing Remote Database Configuration Compatibility...")
    logger.info("=" * 70)
    
    success = test_remote_database_config()
    
    if success:
        logger.info("🎉 Remote database compatibility verified!")
        logger.info("")
        show_remote_config_example()
    else:
        logger.error("💥 Remote database compatibility test failed!")
        sys.exit(1)