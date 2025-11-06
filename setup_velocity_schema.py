#!/usr/bin/env python3
"""
Simple script to set up the velocity analysis database schema
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

from app.shared.config.config import Config
import mysql.connector

def setup_schema():
    """Set up the velocity analysis database schema"""
    print("🚀 Setting up Velocity Analysis Database Schema")
    print("="*50)
    
    try:
        # Get database configuration
        config = Config()
        conn = mysql.connector.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )
        cursor = conn.cursor()
        print("✅ Connected to database")
        
        # Read schema file
        schema_file = 'database/bin_velocity_schema_existing_tables.sql'
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Split into statements
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        print(f"📝 Executing {len(statements)} SQL statements...")
        
        success_count = 0
        error_count = 0
        
        for i, stmt in enumerate(statements):
            try:
                cursor.execute(stmt)
                print(f"✅ Statement {i+1}: OK")
                success_count += 1
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"⚠️  Statement {i+1}: Table already exists (OK)")
                    success_count += 1
                else:
                    print(f"❌ Statement {i+1}: {e}")
                    error_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"\n📊 Schema Setup Summary:")
        print(f"   Successful: {success_count}")
        print(f"   Errors: {error_count}")
        
        if error_count == 0:
            print("🎉 Schema setup completed successfully!")
            return True
        else:
            print("⚠️  Schema setup completed with some errors")
            return False
            
    except Exception as e:
        print(f"❌ Schema setup failed: {e}")
        return False

if __name__ == "__main__":
    success = setup_schema()
    sys.exit(0 if success else 1)