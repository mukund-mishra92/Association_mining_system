#!/usr/bin/env python3
"""Check and fix the sku_velocity_log table and trigger issues."""

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
        
        cursor = service.connection.cursor()
        
        # Check if sku_velocity_log table exists
        cursor.execute("SHOW TABLES LIKE 'sku_velocity_log'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✅ sku_velocity_log table exists")
            cursor.execute("DESCRIBE sku_velocity_log")
            columns = cursor.fetchall()
            print("Table structure:")
            for col in columns:
                print(f"  {col}")
        else:
            print("❌ sku_velocity_log table does not exist")
            print("Creating sku_velocity_log table...")
            
            # Create the table that the triggers expect
            create_table_sql = """
            CREATE TABLE sku_velocity_log (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                SKU_ID VARCHAR(255) NOT NULL,
                NEW_VELOCITY INT,
                UPDATED_BY VARCHAR(255),
                created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_sku_id (SKU_ID),
                INDEX idx_created_timestamp (created_timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
            
            cursor.execute(create_table_sql)
            service.connection.commit()
            print("✅ sku_velocity_log table created successfully")
        
        # Test a simple update to see if triggers work now
        print("\nTesting trigger functionality with a dummy update...")
        try:
            # Update a sample SKU's velocity (to the same value) to test trigger
            cursor.execute("""
                UPDATE sku_master 
                SET VELOCITY = VELOCITY, UPDATED_BY = 'velocity_test_system'
                WHERE SKU_ID = '0018584e-5eef-48ae-b668-39b432e86532'
                LIMIT 1
            """)
            service.connection.commit()
            print("✅ Trigger test successful - no errors")
            
            # Check if log entry was created
            cursor.execute("SELECT COUNT(*) FROM sku_velocity_log WHERE SKU_ID = '0018584e-5eef-48ae-b668-39b432e86532'")
            log_count = cursor.fetchone()[0]
            print(f"Log entries for test SKU: {log_count}")
            
        except Exception as trigger_error:
            print(f"❌ Trigger still has issues: {trigger_error}")
            
            # If there's still a definer issue, let's recreate the triggers
            print("Attempting to fix trigger definers...")
            try:
                # Drop existing triggers
                cursor.execute("DROP TRIGGER IF EXISTS log_sku_master_velocity_insert")
                cursor.execute("DROP TRIGGER IF EXISTS log_sku_master_velocity_update")
                
                # Recreate triggers with current user
                cursor.execute("""
                CREATE TRIGGER log_sku_master_velocity_insert
                AFTER INSERT ON sku_master
                FOR EACH ROW
                BEGIN
                    INSERT INTO sku_velocity_log (SKU_ID, NEW_VELOCITY, UPDATED_BY)
                    VALUES (NEW.SKU_ID, NEW.VELOCITY, COALESCE(NEW.UPDATED_BY, USER()));
                END
                """)
                
                cursor.execute("""
                CREATE TRIGGER log_sku_master_velocity_update
                AFTER UPDATE ON sku_master
                FOR EACH ROW
                BEGIN
                    IF OLD.VELOCITY <> NEW.VELOCITY THEN
                        INSERT INTO sku_velocity_log (SKU_ID, NEW_VELOCITY, UPDATED_BY)
                        VALUES (NEW.SKU_ID, NEW.VELOCITY, COALESCE(NEW.UPDATED_BY, USER()));
                    END IF;
                END
                """)
                
                service.connection.commit()
                print("✅ Triggers recreated successfully")
                
                # Test again
                cursor.execute("""
                    UPDATE sku_master 
                    SET VELOCITY = 2, UPDATED_BY = 'velocity_system'
                    WHERE SKU_ID = '0018584e-5eef-48ae-b668-39b432e86532'
                    LIMIT 1
                """)
                service.connection.commit()
                print("✅ Final trigger test successful")
                
            except Exception as recreate_error:
                print(f"❌ Could not recreate triggers: {recreate_error}")
        
        cursor.close()
        service.disconnect_database()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()