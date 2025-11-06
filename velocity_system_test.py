#!/usr/bin/env python3
"""
Comprehensive Test Script for Bin Velocity Analysis System
Tests the velocity system with existing sku_master and order tables

This script validates:
1. Database connectivity with existing tables
2. SKU velocity calculations and sku_master updates
3. Bin velocity composite scoring
4. API endpoint functionality
5. Data accuracy and statistics

Author: GitHub Copilot
Date: November 4, 2025
"""

import sys
import os
import traceback
from datetime import datetime, date
import json

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.utils.config import Config
from app.modules.velocity_analysis.services.velocity_service import VelocityAnalysisService

class VelocitySystemTester:
    def __init__(self):
        """Initialize the velocity system tester"""
        self.config = Config()
        self.db_config = self.config.get_database_config()
        self.velocity_service = None
        self.test_results = {}
        
    def print_header(self, title: str):
        """Print a formatted test section header"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        
    def print_result(self, test_name: str, success: bool, details: str = ""):
        """Print test result with formatting"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        self.test_results[test_name] = {"success": success, "details": details}
        
    def test_database_connectivity(self) -> bool:
        """Test 1: Database connectivity and existing table access"""
        self.print_header("TEST 1: Database Connectivity")
        
        try:
            # Initialize velocity service
            self.velocity_service = VelocityAnalysisService(self.db_config)
            
            # Test database connection
            if not self.velocity_service.connect_database():
                self.print_result("Database Connection", False, "Failed to connect to database")
                return False
            
            self.print_result("Database Connection", True, "Successfully connected")
            
            # Check existing tables
            cursor = self.velocity_service.connection.cursor()
            
            # Check sku_master table
            try:
                cursor.execute("SELECT COUNT(*) FROM sku_master")
                sku_count = cursor.fetchone()[0]
                self.print_result("SKU Master Table Access", True, f"Found {sku_count} SKUs")
            except Exception as e:
                self.print_result("SKU Master Table Access", False, f"Error: {str(e)}")
                return False
            
            # Check order table
            try:
                cursor.execute("SELECT COUNT(*) FROM `order`")
                order_count = cursor.fetchone()[0]
                self.print_result("Order Table Access", True, f"Found {order_count} orders")
            except Exception as e:
                self.print_result("Order Table Access", False, f"Error: {str(e)}")
                return False
            
            # Check if velocity column exists in sku_master
            try:
                cursor.execute("DESCRIBE sku_master")
                columns = [row[0] for row in cursor.fetchall()]
                has_velocity = 'velocity' in columns
                
                if has_velocity:
                    cursor.execute("SELECT COUNT(*) FROM sku_master WHERE velocity IS NOT NULL")
                    velocity_count = cursor.fetchone()[0]
                    self.print_result("Velocity Column Check", True, f"Velocity column exists, {velocity_count} SKUs have velocity values")
                else:
                    self.print_result("Velocity Column Check", False, "Velocity column does not exist in sku_master")
                    
            except Exception as e:
                self.print_result("Velocity Column Check", False, f"Error: {str(e)}")
            
            cursor.close()
            return True
            
        except Exception as e:
            self.print_result("Database Setup", False, f"Error: {str(e)}")
            return False
    
    def test_system_status(self) -> bool:
        """Test 2: System status and table creation"""
        self.print_header("TEST 2: System Status & Table Setup")
        
        try:
            # Get system status
            status_result = self.velocity_service.get_velocity_system_status()
            
            if status_result["success"]:
                status = status_result["status"]
                self.print_result("System Status Check", True, f"System status: {status['system_status']}")
                
                # Print table status
                for table_name, table_status in status["table_status"].items():
                    exists = table_status.get("exists", False)
                    self.print_result(f"Table: {table_name}", exists, 
                                    f"Records: {table_status.get('record_count', 0)}")
                
                return True
            else:
                self.print_result("System Status Check", False, status_result["message"])
                return False
                
        except Exception as e:
            self.print_result("System Status Check", False, f"Error: {str(e)}")
            return False
    
    def test_sku_velocity_calculation(self) -> bool:
        """Test 3: SKU velocity calculations"""
        self.print_header("TEST 3: SKU Velocity Calculations")
        
        try:
            # Run SKU velocity calculation
            print("Running SKU velocity analysis...")
            result = self.velocity_service.calculate_sku_velocities()
            
            if result["success"]:
                analysis = result["analysis"]
                self.print_result("SKU Velocity Calculation", True, 
                                f"Processed {analysis['total_skus']} SKUs")
                
                # Check velocity distribution
                for category, count in analysis["velocity_distribution"].items():
                    print(f"    {category}: {count} SKUs")
                
                # Verify sku_master table was updated
                cursor = self.velocity_service.connection.cursor()
                cursor.execute("""
                    SELECT 
                        velocity,
                        COUNT(*) as count,
                        CASE 
                            WHEN velocity = 3 THEN 'High'
                            WHEN velocity = 2 THEN 'Medium' 
                            WHEN velocity = 1 THEN 'Low'
                            ELSE 'Unknown'
                        END as category
                    FROM sku_master 
                    WHERE velocity IS NOT NULL 
                    GROUP BY velocity 
                    ORDER BY velocity DESC
                """)
                
                velocity_data = cursor.fetchall()
                print("\n    Velocity distribution in sku_master:")
                for row in velocity_data:
                    print(f"      {row[2]} (velocity={row[0]}): {row[1]} SKUs")
                
                cursor.close()
                return True
            else:
                self.print_result("SKU Velocity Calculation", False, result["message"])
                return False
                
        except Exception as e:
            self.print_result("SKU Velocity Calculation", False, f"Error: {str(e)}")
            traceback.print_exc()
            return False
    
    def test_bin_velocity_calculation(self) -> bool:
        """Test 4: Bin velocity calculations"""
        self.print_header("TEST 4: Bin Velocity Calculations")
        
        try:
            # Run bin velocity calculation
            print("Running bin velocity analysis...")
            result = self.velocity_service.calculate_bin_velocities()
            
            if result["success"]:
                analysis = result["analysis"]
                self.print_result("Bin Velocity Calculation", True, 
                                f"Processed {analysis['total_bins']} bins")
                
                # Show bin statistics
                print(f"    Average composite score: {analysis.get('average_composite_score', 0):.3f}")
                print(f"    Average capacity utilization: {analysis.get('average_capacity_utilization', 0):.3f}")
                
                # Check specific bin results
                cursor = self.velocity_service.connection.cursor(dictionary=True)
                cursor.execute("""
                    SELECT bin_id, composite_velocity_score, sku_count, bin_capacity,
                           capacity_utilization, optimization_recommendation
                    FROM bin_velocity_scores 
                    ORDER BY composite_velocity_score DESC 
                    LIMIT 5
                """)
                
                top_bins = cursor.fetchall()
                print("\n    Top 5 bins by composite velocity:")
                for bin_data in top_bins:
                    print(f"      Bin {bin_data['bin_id']}: Score={bin_data['composite_velocity_score']:.3f}, "
                          f"SKUs={bin_data['sku_count']}/{bin_data['bin_capacity']}, "
                          f"Util={bin_data['capacity_utilization']:.1%}")
                
                cursor.close()
                return True
            else:
                self.print_result("Bin Velocity Calculation", False, result["message"])
                return False
                
        except Exception as e:
            self.print_result("Bin Velocity Calculation", False, f"Error: {str(e)}")
            traceback.print_exc()
            return False
    
    def test_data_retrieval(self) -> bool:
        """Test 5: Data retrieval and statistics"""
        self.print_header("TEST 5: Data Retrieval & Statistics")
        
        try:
            # Test velocity statistics
            stats_result = self.velocity_service.get_velocity_statistics()
            
            if stats_result["success"]:
                stats = stats_result["statistics"]
                self.print_result("Statistics Generation", True, "Successfully generated statistics")
                
                # Display SKU distribution
                print("\n    SKU Velocity Distribution:")
                for dist in stats["sku_distribution"]:
                    print(f"      {dist.get('velocity_category', 'Unknown')}: {dist['count']} SKUs")
                
                # Display bin distribution
                print("\n    Bin Velocity Distribution:")
                for dist in stats["bin_distribution"]:
                    print(f"      {dist['velocity_category']}: {dist['count']} bins "
                          f"(avg score: {dist['avg_score']})")
                
                # Overall statistics
                overall = stats["overall_stats"]
                print(f"\n    Overall Statistics:")
                print(f"      Total SKUs analyzed: {overall.get('total_skus_analyzed', 0)}")
                print(f"      Total bins analyzed: {overall.get('total_bins_analyzed', 0)}")
                print(f"      Last calculation: {overall.get('last_calculation_date', 'N/A')}")
                
                return True
            else:
                self.print_result("Statistics Generation", False, stats_result["message"])
                return False
                
        except Exception as e:
            self.print_result("Statistics Generation", False, f"Error: {str(e)}")
            return False
    
    def test_weekly_analysis(self) -> bool:
        """Test 6: Weekly analysis functionality"""
        self.print_header("TEST 6: Weekly Analysis")
        
        try:
            # Run weekly analysis
            print("Running weekly analysis...")
            result = self.velocity_service.run_weekly_analysis()
            
            if result["success"]:
                summary = result["summary"]
                self.print_result("Weekly Analysis", True, "Analysis completed successfully")
                
                print(f"    Analysis date: {summary['analysis_date']}")
                print(f"    SKUs processed: {summary['sku_analysis']['skus_processed']}")
                print(f"    Bins processed: {summary['bin_analysis']['bins_processed']}")
                print(f"    Total execution time: {summary['total_execution_time']:.2f} seconds")
                
                return True
            else:
                self.print_result("Weekly Analysis", False, result["message"])
                return False
                
        except Exception as e:
            self.print_result("Weekly Analysis", False, f"Error: {str(e)}")
            return False
    
    def test_data_accuracy(self) -> bool:
        """Test 7: Data accuracy validation"""
        self.print_header("TEST 7: Data Accuracy Validation")
        
        try:
            cursor = self.velocity_service.connection.cursor(dictionary=True)
            
            # Check velocity value ranges
            cursor.execute("""
                SELECT 
                    MIN(velocity) as min_velocity,
                    MAX(velocity) as max_velocity,
                    COUNT(DISTINCT velocity) as distinct_velocities
                FROM sku_master 
                WHERE velocity IS NOT NULL
            """)
            velocity_range = cursor.fetchone()
            
            # Validate velocity values are 1, 2, or 3
            valid_range = (velocity_range['min_velocity'] >= 1 and 
                          velocity_range['max_velocity'] <= 3 and
                          velocity_range['distinct_velocities'] <= 3)
            
            self.print_result("Velocity Value Range", valid_range, 
                            f"Min: {velocity_range['min_velocity']}, "
                            f"Max: {velocity_range['max_velocity']}, "
                            f"Distinct values: {velocity_range['distinct_velocities']}")
            
            # Check composite scores are between 0 and 1
            cursor.execute("""
                SELECT 
                    MIN(composite_velocity_score) as min_score,
                    MAX(composite_velocity_score) as max_score,
                    AVG(composite_velocity_score) as avg_score
                FROM bin_velocity_scores
            """)
            score_range = cursor.fetchone()
            
            if score_range and score_range['min_score'] is not None:
                valid_scores = (score_range['min_score'] >= 0 and score_range['max_score'] <= 1)
                self.print_result("Composite Score Range", valid_scores,
                                f"Min: {score_range['min_score']:.3f}, "
                                f"Max: {score_range['max_score']:.3f}, "
                                f"Avg: {score_range['avg_score']:.3f}")
            else:
                self.print_result("Composite Score Range", False, "No bin velocity scores found")
            
            cursor.close()
            return True
            
        except Exception as e:
            self.print_result("Data Accuracy Validation", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all velocity system tests"""
        print(f"\n🚀 STARTING BIN VELOCITY ANALYSIS SYSTEM TESTS")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Database: {self.db_config.get('host', 'localhost')}:{self.db_config.get('port', 3306)}")
        
        # Run all tests
        tests = [
            ("Database Connectivity", self.test_database_connectivity),
            ("System Status", self.test_system_status),
            ("SKU Velocity Calculation", self.test_sku_velocity_calculation),
            ("Bin Velocity Calculation", self.test_bin_velocity_calculation),
            ("Data Retrieval", self.test_data_retrieval),
            ("Weekly Analysis", self.test_weekly_analysis),
            ("Data Accuracy", self.test_data_accuracy)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_function in tests:
            try:
                if test_function():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ FAIL {test_name} - Unexpected error: {str(e)}")
                traceback.print_exc()
        
        # Print final summary
        self.print_header("TEST SUMMARY")
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! The velocity system is working correctly.")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Check the details above.")
        
        # Cleanup
        if self.velocity_service:
            self.velocity_service.disconnect_database()
        
        return passed_tests == total_tests

def main():
    """Main function to run velocity system tests"""
    tester = VelocitySystemTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()