"""
Bin Velocity Analysis System - Quick Setup and Test Script
Helps set up and test the new velocity analysis functionality

Usage:
    python test_velocity_system.py
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.velocity_analysis.services.velocity_service import VelocityAnalysisService
import datetime

def test_velocity_system():
    """Test the velocity analysis system with sample configuration"""
    
    print("🚀 Bin Velocity Analysis System - Quick Test")
    print("=" * 50)
    
    # Sample database configuration (update with your details)
    db_config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'root',  # Update with your password
        'database': 'neo'    # Update with your database name
    }
    
    # Test 1: Database Connection
    print("\n1️⃣ Testing Database Connection...")
    service = VelocityAnalysisService(db_config)
    
    if service.connect_database():
        print("✅ Database connection successful!")
        
        # Test 2: Check Tables
        print("\n2️⃣ Checking Velocity Tables...")
        table_status = service._check_velocity_tables()
        
        missing_tables = [table for table, exists in table_status.items() if not exists]
        
        if missing_tables:
            print(f"⚠️ Missing tables: {missing_tables}")
            print("📝 Run the database schema file to create missing tables:")
            print("   mysql -u root -p neo < database/bin_velocity_schema.sql")
        else:
            print("✅ All velocity tables exist!")
            
            # Test 3: Get System Status
            print("\n3️⃣ Getting System Status...")
            status_result = service.get_velocity_system_status()
            
            if status_result["success"]:
                print("✅ System status retrieved successfully!")
                for metric, data in status_result["status"].items():
                    print(f"   {metric}: {data['count']} records (Last update: {data['last_update']})")
            else:
                print(f"❌ System status check failed: {status_result['message']}")
        
        # Test 4: Test Parameters
        print("\n4️⃣ Testing Calculation Parameters...")
        params = service.get_calculation_parameters()
        print("✅ Parameters loaded successfully!")
        for key, value in params.items():
            print(f"   {key}: {value}")
        
        service.disconnect_database()
        
    else:
        print("❌ Database connection failed!")
        print("📝 Please check your database configuration:")
        print("   - Ensure MySQL is running")
        print("   - Verify host, port, username, password")
        print("   - Confirm database exists")
        return False
    
    print("\n🎉 Basic system test completed!")
    print("\n📋 Next Steps:")
    print("1. Start the Flask application: python app/web/main.py")
    print("2. Go to the main dashboard")
    print("3. Click 'Bin Velocity Analysis' button")
    print("4. Configure database connection")
    print("5. Initialize velocity tables if needed")
    print("6. Run velocity analysis!")
    
    return True

def create_sample_data():
    """Create sample data for testing (if orders table is empty)"""
    
    print("\n🔧 Creating Sample Data...")
    print("Note: This function would create sample order data")
    print("Implement based on your specific order table structure")
    
    # Sample SQL for creating test data
    sample_sql = """
    -- Sample order data (adjust table/column names as needed)
    INSERT INTO orders (order_date, sku_code, quantity) VALUES
    ('2025-10-01', 'SKU001', 2),
    ('2025-10-01', 'SKU002', 1),
    ('2025-10-02', 'SKU001', 3),
    ('2025-10-02', 'SKU003', 1),
    ('2025-10-03', 'SKU002', 2),
    ('2025-10-03', 'SKU004', 1);
    
    -- Sample bin configuration
    INSERT INTO bin_configuration (bin_id, sku_code, bin_capacity, zone) VALUES
    ('BIN001', 'SKU001', 2, 'Zone_A'),
    ('BIN001', 'SKU002', 2, 'Zone_A'),
    ('BIN002', 'SKU003', 4, 'Zone_B'),
    ('BIN002', 'SKU004', 4, 'Zone_B');
    """
    
    print("📝 Sample SQL commands:")
    print(sample_sql)

if __name__ == "__main__":
    try:
        success = test_velocity_system()
        
        if success:
            create_sample = input("\n❓ Would you like to see sample data creation SQL? (y/n): ")
            if create_sample.lower() == 'y':
                create_sample_data()
                
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        print("\n🔍 Troubleshooting:")
        print("1. Check if all required packages are installed: pip install -r requirements.txt")
        print("2. Verify database connection details")
        print("3. Ensure the project structure is correct")
        print("4. Check the application logs for detailed errors")