"""
Bin Velocity Analysis Service
Calculates SKU velocities and bin composite scores for warehouse optimization

This service implements:
- SKU velocity calculation (1, 2, 3) based on order patterns with time decay
- Bin composite velocity scoring based on SKU composition
- Weekly automated processing for bin optimization decisions
"""

import mysql.connector
from datetime import datetime, timedelta, date
import json
import logging
import math
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VelocityAnalysisService:
    """Main service for calculating SKU and bin velocities"""
    
    def __init__(self, db_config: Dict):
        """
        Initialize the velocity analysis service
        
        Args:
            db_config: Database connection configuration
        """
        self.db_config = db_config
        self.connection = None
        
        # Default calculation parameters (can be overridden from database)
        self.default_params = {
            'time_decay_rate': 0.05,
            'high_velocity_threshold': 0.80,
            'medium_velocity_threshold': 0.50,
            'analysis_period_days': 90,
            'min_orders_for_calculation': 5,
            'weekly_calculation_day': 1  # Monday
        }
        
    def connect_database(self) -> bool:
        """
        Establish database connection
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            logger.info("Database connection established for velocity analysis")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return False
            
    def disconnect_database(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed")
            
    def get_calculation_parameters(self) -> Dict:
        """
        Load calculation parameters from database
        
        Returns:
            Dict: Calculation parameters with proper data types
        """
        if not self.connection:
            return self.default_params
            
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT parameter_name, parameter_value FROM velocity_calculation_config")
            db_params = {row['parameter_name']: row['parameter_value'] for row in cursor.fetchall()}
            
            # Merge with defaults for any missing parameters
            merged_params = {**self.default_params, **db_params}
            
            # Convert Decimal types to appropriate Python types
            converted_params = {}
            for key, value in merged_params.items():
                if hasattr(value, '__float__'):  # Decimal types
                    if key in ['min_orders_for_calculation', 'weekly_calculation_day']:
                        converted_params[key] = int(value)
                    else:
                        converted_params[key] = float(value)
                else:
                    converted_params[key] = value
            
            cursor.close()
            return converted_params
            
        except Exception as e:
            logger.error(f"Error loading calculation parameters: {str(e)}")
            return self.default_params
            
    def calculate_sku_velocities(self, analysis_date: Optional[date] = None) -> Dict:
        """
        Calculate velocity scores (1, 2, 3) for all SKUs based on order patterns
        Updates the velocity column in the existing sku_master table
        
        Args:
            analysis_date: Date for analysis (defaults to today)
            
        Returns:
            Dict: Results with success status and statistics
        """
        if not analysis_date:
            analysis_date = date.today()
            
        params = self.get_calculation_parameters()
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Get order data for analysis period
            end_date = analysis_date
            start_date = end_date - timedelta(days=int(params['analysis_period_days']))
            
            # Query to get order data with time decay weighting
            # Uses your existing 'wms_to_wcs_order_line_request_data' table
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
            """
            
            cursor.execute(order_query, (end_date, start_date, end_date))
            order_data = cursor.fetchall()
            
            if not order_data:
                logger.warning("No order data found for velocity calculation")
                return {"success": False, "message": "No order data available"}
            
            # Process order data to calculate weighted scores
            sku_metrics = {}
            
            for row in order_data:
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
            
            # Filter SKUs with minimum order threshold
            filtered_skus = {
                sku: metrics for sku, metrics in sku_metrics.items()
                if metrics['total_orders'] >= params['min_orders_for_calculation']
            }
            
            if not filtered_skus:
                logger.warning("No SKUs meet minimum order threshold")
                return {"success": False, "message": "No SKUs meet minimum order criteria"}
            
            # Calculate percentiles for velocity assignment
            weighted_scores = [float(metrics['weighted_score']) for metrics in filtered_skus.values()]
            high_threshold = np.percentile(weighted_scores, params['high_velocity_threshold'] * 100)
            medium_threshold = np.percentile(weighted_scores, params['medium_velocity_threshold'] * 100)
            
            # Assign velocity scores and update sku_master table
            velocity_results = []
            updated_count = 0
            
            for sku_code, metrics in filtered_skus.items():
                weighted_score = float(metrics['weighted_score'])
                total_orders = float(metrics['total_orders'])
                order_frequency = total_orders / float(params['analysis_period_days'])
                
                # Determine velocity score
                if weighted_score >= high_threshold:
                    velocity_score = 3  # High velocity
                elif weighted_score >= medium_threshold:
                    velocity_score = 2  # Medium velocity
                else:
                    velocity_score = 1  # Low velocity
                
                # Get current velocity from sku_master
                cursor.execute("SELECT VELOCITY FROM sku_master WHERE SKU_ID = %s", (sku_code,))
                current_record = cursor.fetchone()
                old_velocity = current_record['VELOCITY'] if current_record else None
                
                # Update velocity in sku_master table
                update_query = """
                UPDATE sku_master 
                SET VELOCITY = %s, UPDATED_TIMESTAMP = CURRENT_TIMESTAMP 
                WHERE SKU_ID = %s
                """
                cursor.execute(update_query, (velocity_score, sku_code))
                updated_count += 1
                
                # Save to history table for tracking
                history_query = """
                INSERT INTO sku_velocity_history 
                (SKU_ID, old_velocity, new_velocity, reason, final_score, changed_at) 
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                reason = f"Auto-calculated: {total_orders} orders, freq={order_frequency:.4f}/day"
                cursor.execute(history_query, (
                    sku_code, old_velocity, velocity_score, reason, weighted_score, analysis_date
                ))
                
                velocity_results.append({
                    'sku_code': sku_code,
                    'old_velocity': old_velocity,
                    'new_velocity': velocity_score,
                    'order_frequency': round(order_frequency, 4),
                    'total_orders': total_orders,
                    'weighted_score': round(weighted_score, 4),
                    'analysis_period_days': int(params['analysis_period_days']),
                    'calculation_date': analysis_date
                })
            
            # Commit all changes
            self.connection.commit()
            
            # Generate statistics
            velocity_stats = {
                'high_velocity': len([r for r in velocity_results if r['new_velocity'] == 3]),
                'medium_velocity': len([r for r in velocity_results if r['new_velocity'] == 2]),
                'low_velocity': len([r for r in velocity_results if r['new_velocity'] == 1]),
                'total_skus_updated': updated_count,
                'total_skus_analyzed': len(velocity_results)
            }
            
            cursor.close()
            
            logger.info(f"SKU velocity calculation completed: {velocity_stats}")
            
            return {
                "success": True,
                "message": f"SKU velocities updated in sku_master table successfully",
                "statistics": velocity_stats,
                "calculation_date": analysis_date.isoformat(),
                "parameters_used": params
            }
            
        except Exception as e:
            logger.error(f"Error calculating SKU velocities: {str(e)}")
            logger.error(f"Exception type: {type(e)}")
            logger.error(f"Exception details: {repr(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"success": False, "message": str(e)}
            
    def _save_sku_velocities(self, velocity_results: List[Dict]):
        """Save SKU velocity results to database"""
        cursor = self.connection.cursor()
        
        # Deactivate old records
        cursor.execute("UPDATE sku_velocity SET is_active = FALSE WHERE is_active = TRUE")
        
        # Insert new records
        insert_query = """
        INSERT INTO sku_velocity 
        (sku_code, velocity_score, order_frequency, total_orders, weighted_score, 
         analysis_period_days, calculated_date) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        for result in velocity_results:
            cursor.execute(insert_query, (
                result['sku_code'], result['velocity_score'], result['order_frequency'],
                result['total_orders'], result['weighted_score'], 
                result['analysis_period_days'], result['calculated_date']
            ))
        
        self.connection.commit()
        cursor.close()
        
    def calculate_bin_velocities(self, calculation_date: Optional[date] = None) -> Dict:
        """
        Calculate composite velocity scores for bins based on SKU composition
        Reads velocity data from the existing sku_master table
        
        Args:
            calculation_date: Date for calculation (defaults to today)
            
        Returns:
            Dict: Results with success status and statistics
        """
        if not calculation_date:
            calculation_date = date.today()
            
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Get current bin configurations with SKU velocities from sku_master
            bin_query = """
            SELECT 
                bc.bin_id,
                bc.sku_code,
                bc.bin_capacity,
                bc.zone,
                bc.bin_location,
                sm.velocity as velocity_score
            FROM bin_configuration bc
            LEFT JOIN sku_master sm ON bc.sku_code = sm.SKU_ID
            WHERE bc.is_active = TRUE 
            AND sm.velocity IS NOT NULL
            ORDER BY bc.bin_id, bc.sku_code
            """
            
            cursor.execute(bin_query)
            bin_data = cursor.fetchall()
            
            if not bin_data:
                logger.warning("No bin configuration data found with velocity information")
                return {"success": False, "message": "No bin configuration data available with velocity data"}
            
            # Group by bin_id and calculate composite scores
            bin_scores = {}
            
            for row in bin_data:
                bin_id = row['bin_id']
                
                if bin_id not in bin_scores:
                    bin_scores[bin_id] = {
                        'bin_capacity': row['bin_capacity'],
                        'zone': row['zone'],
                        'bin_location': row['bin_location'],
                        'sku_velocities': [],
                        'sku_codes': []
                    }
                
                if row['velocity_score']:  # SKU has velocity data
                    bin_scores[bin_id]['sku_velocities'].append(row['velocity_score'])
                    bin_scores[bin_id]['sku_codes'].append(row['sku_code'])
            
            # Calculate composite scores and recommendations
            velocity_results = []
            
            for bin_id, data in bin_scores.items():
                sku_velocities = data['sku_velocities']
                
                if not sku_velocities:
                    continue  # Skip bins with no velocity data
                
                # Calculate composite velocity score
                composite_score = self._calculate_composite_velocity(sku_velocities, data['bin_capacity'])
                
                # Calculate utilization
                sku_count = len(sku_velocities)
                capacity_utilization = (sku_count / data['bin_capacity']) * 100
                
                # Generate optimization recommendation
                recommendation = self._generate_bin_recommendation(
                    composite_score, capacity_utilization, sku_velocities, data['bin_capacity']
                )
                
                # Calculate priority score (1-10)
                priority_score = self._calculate_priority_score(composite_score, capacity_utilization)
                
                velocity_results.append({
                    'bin_id': bin_id,
                    'composite_velocity_score': round(composite_score, 2),
                    'individual_sku_velocities': json.dumps(sku_velocities),
                    'sku_count': sku_count,
                    'bin_capacity': data['bin_capacity'],
                    'capacity_utilization': round(capacity_utilization, 2),
                    'optimization_recommendation': recommendation,
                    'priority_score': priority_score,
                    'calculation_date': calculation_date
                })
            
            # Save results to database
            self._save_bin_velocities(velocity_results, calculation_date)
            
            # Generate statistics
            bin_stats = {
                'total_bins': len(velocity_results),
                'high_priority_bins': len([r for r in velocity_results if r['priority_score'] >= 8]),
                'medium_priority_bins': len([r for r in velocity_results if 5 <= r['priority_score'] < 8]),
                'low_priority_bins': len([r for r in velocity_results if r['priority_score'] < 5]),
                'average_composite_score': round(np.mean([r['composite_velocity_score'] for r in velocity_results]), 2),
                'average_utilization': round(np.mean([r['capacity_utilization'] for r in velocity_results]), 2)
            }
            
            cursor.close()
            
            logger.info(f"Bin velocity calculation completed: {bin_stats}")
            
            return {
                "success": True,
                "message": "Bin velocities calculated successfully using sku_master table",
                "statistics": bin_stats,
                "calculation_date": calculation_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating bin velocities: {str(e)}")
            return {"success": False, "message": str(e)}
            
    def _calculate_composite_velocity(self, sku_velocities: List[int], bin_capacity: int) -> float:
        """
        Calculate composite velocity score for a bin
        
        Args:
            sku_velocities: List of individual SKU velocity scores
            bin_capacity: Bin capacity (1, 2, 4, 6)
            
        Returns:
            float: Composite velocity score
        """
        if not sku_velocities:
            return 0.0
        
        # Weighted average based on velocity importance
        velocity_weights = {1: 1.0, 2: 2.0, 3: 3.0}  # Higher velocities get more weight
        
        weighted_sum = sum(velocity_weights[v] for v in sku_velocities)
        max_possible_weight = len(sku_velocities) * velocity_weights[3]
        
        # Base composite score (0-3)
        base_score = (weighted_sum / max_possible_weight) * 3
        
        # Apply capacity utilization bonus/penalty
        utilization = len(sku_velocities) / bin_capacity
        if utilization >= 0.8:  # Well utilized
            capacity_multiplier = 1.1
        elif utilization <= 0.5:  # Under-utilized
            capacity_multiplier = 0.9
        else:
            capacity_multiplier = 1.0
        
        return base_score * capacity_multiplier
        
    def _generate_bin_recommendation(self, composite_score: float, utilization: float, 
                                   sku_velocities: List[int], bin_capacity: int) -> str:
        """Generate optimization recommendation for a bin"""
        
        recommendations = []
        
        # Velocity-based recommendations
        if composite_score >= 2.5:
            recommendations.append("HIGH PRIORITY: Place in easily accessible zone")
        elif composite_score >= 1.5:
            recommendations.append("MEDIUM PRIORITY: Standard warehouse location")
        else:
            recommendations.append("LOW PRIORITY: Can be placed in remote areas")
        
        # Utilization-based recommendations
        if utilization < 0.5:
            recommendations.append(f"UNDERUTILIZED: Consider consolidating (only {len(sku_velocities)}/{bin_capacity} slots used)")
        elif utilization == 1.0:
            recommendations.append("FULLY UTILIZED: Monitor for expansion needs")
        
        # Velocity mix recommendations
        velocity_range = max(sku_velocities) - min(sku_velocities) if sku_velocities else 0
        if velocity_range >= 2:
            recommendations.append("MIXED VELOCITIES: Consider segregating high/low velocity items")
        
        return " | ".join(recommendations)
        
    def _calculate_priority_score(self, composite_score: float, utilization: float) -> int:
        """Calculate priority score (1-10) for bin placement decisions"""
        
        # Base score from composite velocity (0-6 points)
        velocity_points = min(6, int(composite_score * 2))
        
        # Utilization points (0-4 points)
        if utilization >= 0.8:
            utilization_points = 4
        elif utilization >= 0.6:
            utilization_points = 3
        elif utilization >= 0.4:
            utilization_points = 2
        else:
            utilization_points = 1
        
        return min(10, velocity_points + utilization_points)
        
    def _save_bin_velocities(self, velocity_results: List[Dict], calculation_date: date):
        """Save bin velocity results to database"""
        cursor = self.connection.cursor()
        
        # Delete old records for this calculation date
        cursor.execute("DELETE FROM bin_velocity_scores WHERE calculation_date = %s", (calculation_date,))
        
        # Insert new records
        insert_query = """
        INSERT INTO bin_velocity_scores 
        (bin_id, composite_velocity_score, individual_sku_velocities, sku_count, 
         bin_capacity, capacity_utilization, optimization_recommendation, priority_score,
         calculation_date, analysis_period_start, analysis_period_end) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        analysis_end = calculation_date
        analysis_start = analysis_end - timedelta(days=7)  # Weekly analysis
        
        for result in velocity_results:
            cursor.execute(insert_query, (
                result['bin_id'], result['composite_velocity_score'], 
                result['individual_sku_velocities'], result['sku_count'],
                result['bin_capacity'], result['capacity_utilization'],
                result['optimization_recommendation'], result['priority_score'],
                result['calculation_date'], analysis_start, analysis_end
            ))
        
        self.connection.commit()
        cursor.close()
        
    def get_velocity_system_status(self) -> Dict:
        """Get current status of the velocity analysis system"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Manual status collection instead of stored procedure
            status_data = {}
            
            # Get SKU velocity status
            cursor.execute("""
                SELECT 
                    'sku_velocities' as metric_type,
                    COUNT(*) as total_count,
                    MAX(UPDATED_TIMESTAMP) as last_update
                FROM sku_master 
                WHERE VELOCITY IS NOT NULL
            """)
            sku_result = cursor.fetchone()
            if sku_result:
                status_data['sku_velocities'] = {
                    'count': sku_result['total_count'],
                    'last_update': sku_result['last_update']
                }
            
            # Get bin velocity status
            cursor.execute("""
                SELECT 
                    'bin_velocities' as metric_type,
                    COUNT(*) as total_count,
                    MAX(calculation_date) as last_update
                FROM bin_velocity_scores
            """)
            bin_result = cursor.fetchone()
            if bin_result:
                status_data['bin_velocities'] = {
                    'count': bin_result['total_count'],
                    'last_update': bin_result['last_update']
                }
            
            # Get velocity configuration status
            cursor.execute("""
                SELECT 
                    'configuration' as metric_type,
                    COUNT(*) as total_count,
                    MAX(last_updated) as last_update
                FROM velocity_calculation_config
            """)
            config_result = cursor.fetchone()
            if config_result:
                status_data['configuration'] = {
                    'count': config_result['total_count'],
                    'last_update': config_result['last_update']
                }
            
            cursor.close()
            return {"success": True, "status": status_data}
            
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return {"success": False, "message": str(e)}
            
    def run_weekly_analysis(self) -> Dict:
        """Run complete weekly velocity analysis (SKUs + Bins)"""
        logger.info("Starting weekly velocity analysis")
        
        results = {
            "job_id": f"weekly_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "start_time": datetime.now(),
            "sku_analysis": None,
            "bin_analysis": None,
            "overall_success": False
        }
        
        try:
            # Step 1: Calculate SKU velocities
            logger.info("Step 1: Calculating SKU velocities")
            sku_result = self.calculate_sku_velocities()
            results["sku_analysis"] = sku_result
            
            if not sku_result["success"]:
                return results
            
            # Step 2: Calculate bin velocities
            logger.info("Step 2: Calculating bin velocities") 
            bin_result = self.calculate_bin_velocities()
            results["bin_analysis"] = bin_result
            
            if not bin_result["success"]:
                return results
            
            results["overall_success"] = True
            results["end_time"] = datetime.now()
            results["duration"] = (results["end_time"] - results["start_time"]).total_seconds()
            
            logger.info(f"Weekly analysis completed successfully in {results['duration']} seconds")
            
        except Exception as e:
            logger.error(f"Weekly analysis failed: {str(e)}")
            results["error"] = str(e)
            results["end_time"] = datetime.now()
            
        return results
        
    def _check_velocity_tables(self) -> Dict:
        """Check if velocity analysis tables exist in database"""
        required_tables = [
            'sku_master',  # Existing table with velocity column
            'wms_to_wcs_order_line_request_data',  # Existing table with order data
            'bin_configuration', 'bin_velocity_scores',
            'velocity_calculation_config', 'velocity_calculation_jobs',
            'sku_velocity_history'
        ]
        
        try:
            cursor = self.connection.cursor()
            table_status = {}
            
            for table in required_tables:
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                exists = cursor.fetchone() is not None
                table_status[table] = exists
                
                # For existing tables, check if velocity column exists in sku_master
                if table == 'sku_master' and exists:
                    cursor.execute(f"SHOW COLUMNS FROM sku_master LIKE 'velocity'")
                    velocity_column_exists = cursor.fetchone() is not None
                    table_status['sku_master_velocity_column'] = velocity_column_exists
            
            cursor.close()
            return table_status
            
        except Exception as e:
            logger.error(f"Error checking tables: {str(e)}")
            return {table: False for table in required_tables}
    
    def _create_velocity_tables(self) -> Dict:
        """Create velocity analysis tables in database (for existing table structure)"""
        try:
            cursor = self.connection.cursor()
            
            # Read and execute the updated schema file for existing tables
            schema_file = "c:\\Users\\Balmukund.Mishra\\Desktop\\NEO\\association_mining_system\\database\\bin_velocity_schema_existing_tables.sql"
            
            with open(schema_file, 'r') as file:
                schema_sql = file.read()
            
            # Split and execute SQL statements
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            tables_created = []
            
            for statement in statements:
                if statement.upper().startswith('CREATE TABLE'):
                    try:
                        cursor.execute(statement)
                        # Extract table name
                        table_name = statement.split('CREATE TABLE IF NOT EXISTS')[1].split('(')[0].strip()
                        tables_created.append(table_name)
                    except Exception as e:
                        logger.warning(f"Table creation warning: {str(e)}")
                elif statement.upper().startswith(('INSERT', 'DELIMITER', 'CREATE TRIGGER', 'CREATE VIEW', 'CREATE PROCEDURE')):
                    try:
                        cursor.execute(statement)
                    except Exception as e:
                        logger.warning(f"Statement execution warning: {str(e)}")
            
            # Check if velocity column exists in sku_master, if not add it
            try:
                cursor.execute("SHOW COLUMNS FROM sku_master LIKE 'velocity'")
                velocity_column_exists = cursor.fetchone() is not None
                
                if not velocity_column_exists:
                    cursor.execute("ALTER TABLE sku_master ADD COLUMN velocity INT DEFAULT 1 CHECK (velocity IN (1, 2, 3))")
                    cursor.execute("ALTER TABLE sku_master ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
                    tables_created.append("sku_master velocity column")
                    logger.info("Added velocity column to sku_master table")
            except Exception as e:
                logger.warning(f"Could not add velocity column to sku_master: {str(e)}")
            
            self.connection.commit()
            cursor.close()
            
            return {
                "success": True,
                "message": f"Successfully created/updated {len(tables_created)} tables/columns",
                "tables_created": tables_created
            }
            
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def _update_calculation_parameters(self, parameters: Dict):
        """Update calculation parameters temporarily for this instance"""
        self.default_params.update(parameters)
        
    def _get_velocity_data(self, data_type: str, limit: int, filters: Dict) -> Dict:
        """Get velocity data for display with optional filters"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            if data_type in ['sku_velocities', 'both']:
                # Get SKU velocity data from sku_master table
                sku_query = """
                SELECT 
                    sku_code, 
                    velocity as velocity_score, 
                    updated_at as calculated_date,
                    CASE 
                        WHEN velocity = 3 THEN 'High'
                        WHEN velocity = 2 THEN 'Medium'
                        WHEN velocity = 1 THEN 'Low'
                        ELSE 'Unknown'
                    END as velocity_category
                FROM sku_master 
                WHERE sku_code IS NOT NULL
                """
                
                # Add filters
                params = []
                if 'velocity_score' in filters:
                    sku_query += " AND velocity IN (" + ",".join(['%s'] * len(filters['velocity_score'])) + ")"
                    params.extend(filters['velocity_score'])
                
                if 'date_range' in filters and len(filters['date_range']) == 2:
                    sku_query += " AND updated_at BETWEEN %s AND %s"
                    params.extend(filters['date_range'])
                
                sku_query += f" ORDER BY updated_at DESC, velocity DESC LIMIT {limit}"
                
                cursor.execute(sku_query, params)
                sku_data = cursor.fetchall()
                
                # Get additional statistics from history table if available
                for row in sku_data:
                    try:
                        history_query = """
                        SELECT order_frequency, total_orders, weighted_score 
                        FROM sku_velocity_history 
                        WHERE sku_code = %s 
                        ORDER BY calculation_date DESC 
                        LIMIT 1
                        """
                        cursor.execute(history_query, (row['sku_code'],))
                        history = cursor.fetchone()
                        if history:
                            row.update(history)
                        else:
                            row['order_frequency'] = 0
                            row['total_orders'] = 0
                            row['weighted_score'] = 0
                    except:
                        row['order_frequency'] = 0
                        row['total_orders'] = 0
                        row['weighted_score'] = 0
            else:
                sku_data = []
            
            if data_type in ['bin_velocities', 'both']:
                # Get bin velocity data
                bin_query = """
                SELECT bvs.bin_id, bvs.composite_velocity_score, bvs.sku_count,
                       bvs.bin_capacity, bvs.capacity_utilization, bvs.priority_score,
                       bvs.optimization_recommendation, bvs.calculation_date,
                       bc.zone, bc.bin_location
                FROM bin_velocity_scores bvs
                LEFT JOIN bin_configuration bc ON bvs.bin_id = bc.bin_id
                WHERE bc.is_active = TRUE
                """
                
                # Add filters
                params = []
                if 'bin_capacity' in filters:
                    bin_query += " AND bvs.bin_capacity IN (" + ",".join(['%s'] * len(filters['bin_capacity'])) + ")"
                    params.extend(filters['bin_capacity'])
                
                if 'date_range' in filters and len(filters['date_range']) == 2:
                    bin_query += " AND bvs.calculation_date BETWEEN %s AND %s"
                    params.extend(filters['date_range'])
                
                bin_query += f" GROUP BY bvs.bin_id ORDER BY bvs.calculation_date DESC, bvs.priority_score DESC LIMIT {limit}"
                
                cursor.execute(bin_query, params)
                bin_data = cursor.fetchall()
            else:
                bin_data = []
            
            cursor.close()
            
            return {
                "success": True,
                "data": {
                    "sku_velocities": sku_data,
                    "bin_velocities": bin_data
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting velocity data: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def _export_velocity_data(self, data_type: str, export_format: str, filters: Dict) -> Dict:
        """Export velocity data in specified format"""
        try:
            # Get all data (no limit)
            data_result = self._get_velocity_data(data_type, 10000, filters)
            
            if not data_result["success"]:
                return data_result
            
            if export_format == 'csv':
                import csv
                import io
                
                output = io.StringIO()
                
                if data_type == 'sku_velocities' and data_result["data"]["sku_velocities"]:
                    writer = csv.DictWriter(output, fieldnames=data_result["data"]["sku_velocities"][0].keys())
                    writer.writeheader()
                    writer.writerows(data_result["data"]["sku_velocities"])
                elif data_type == 'bin_velocities' and data_result["data"]["bin_velocities"]:
                    writer = csv.DictWriter(output, fieldnames=data_result["data"]["bin_velocities"][0].keys())
                    writer.writeheader()
                    writer.writerows(data_result["data"]["bin_velocities"])
                
                csv_data = output.getvalue()
                output.close()
                
                return {
                    "success": True,
                    "data": csv_data,
                    "format": "csv"
                }
            else:
                return {
                    "success": True,
                    "data": data_result["data"],
                    "format": "json"
                }
                
        except Exception as e:
            logger.error(f"Error exporting velocity data: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def get_velocity_statistics(self) -> Dict:
        """Get comprehensive velocity statistics and analysis"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Get SKU velocity distribution from sku_master
            sku_stats_query = """
            SELECT 
                velocity as velocity_score,
                COUNT(*) as count,
                CASE 
                    WHEN velocity = 3 THEN 'High'
                    WHEN velocity = 2 THEN 'Medium'
                    WHEN velocity = 1 THEN 'Low'
                    ELSE 'Unknown'
                END as velocity_category
            FROM sku_master 
            WHERE velocity IS NOT NULL AND sku_code IS NOT NULL
            GROUP BY velocity
            ORDER BY velocity DESC
            """
            cursor.execute(sku_stats_query)
            sku_distribution = cursor.fetchall()
            
            # Get additional stats from history table if available
            try:
                sku_history_query = """
                SELECT 
                    velocity_score,
                    ROUND(AVG(order_frequency), 2) as avg_order_frequency,
                    ROUND(AVG(weighted_score), 2) as avg_weighted_score
                FROM sku_velocity_history
                WHERE calculation_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                GROUP BY velocity_score
                ORDER BY velocity_score DESC
                """
                cursor.execute(sku_history_query)
                history_stats = {row['velocity_score']: row for row in cursor.fetchall()}
                
                # Merge with sku_distribution
                for row in sku_distribution:
                    if row['velocity_score'] in history_stats:
                        row.update(history_stats[row['velocity_score']])
                    else:
                        row['avg_order_frequency'] = 0
                        row['avg_weighted_score'] = 0
            except:
                for row in sku_distribution:
                    row['avg_order_frequency'] = 0
                    row['avg_weighted_score'] = 0
            
            # Get bin velocity distribution
            bin_stats_query = """
            SELECT 
                CASE 
                    WHEN composite_velocity_score >= 0.7 THEN 'High'
                    WHEN composite_velocity_score >= 0.3 THEN 'Medium'
                    ELSE 'Low'
                END as velocity_category,
                COUNT(*) as count,
                ROUND(AVG(composite_velocity_score), 2) as avg_score,
                ROUND(AVG(capacity_utilization), 2) as avg_utilization
            FROM bin_velocity_scores
            GROUP BY velocity_category
            ORDER BY avg_score DESC
            """
            cursor.execute(bin_stats_query)
            bin_distribution = cursor.fetchall()
            
            # Get overall statistics
            overall_stats_query = """
            SELECT 
                COUNT(DISTINCT sm.SKU_ID) as total_skus_analyzed,
                COUNT(DISTINCT bvs.bin_id) as total_bins_analyzed,
                ROUND(AVG(bvs.composite_velocity_score), 2) as avg_bin_score,
                MAX(sm.updated_at) as last_calculation_date
            FROM sku_master sm
            CROSS JOIN bin_velocity_scores bvs
            WHERE sm.velocity IS NOT NULL AND sm.SKU_ID IS NOT NULL
            """
            cursor.execute(overall_stats_query)
            overall_stats = cursor.fetchone()
            
            # Get average order frequency from history if available
            try:
                freq_query = "SELECT ROUND(AVG(order_frequency), 2) as avg_order_frequency FROM sku_velocity_history WHERE calculation_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
                cursor.execute(freq_query)
                freq_result = cursor.fetchone()
                if freq_result and freq_result['avg_order_frequency']:
                    overall_stats['avg_order_frequency'] = freq_result['avg_order_frequency']
                else:
                    overall_stats['avg_order_frequency'] = 0
            except:
                overall_stats['avg_order_frequency'] = 0
            
            # Get capacity analysis
            capacity_analysis_query = """
            SELECT 
                bin_capacity,
                COUNT(*) as bin_count,
                ROUND(AVG(composite_velocity_score), 2) as avg_velocity,
                ROUND(AVG(capacity_utilization), 2) as avg_utilization,
                ROUND(AVG(sku_count), 1) as avg_sku_count
            FROM bin_velocity_scores
            GROUP BY bin_capacity
            ORDER BY bin_capacity
            """
            cursor.execute(capacity_analysis_query)
            capacity_analysis = cursor.fetchall()
            
            # Get trends from sku_master (last 30 days)
            trends_query = """
            SELECT 
                DATE(updated_at) as date,
                COUNT(DISTINCT sku_code) as skus_calculated,
                COUNT(CASE WHEN velocity = 3 THEN 1 END) as high_velocity_count,
                COUNT(CASE WHEN velocity = 2 THEN 1 END) as medium_velocity_count,
                COUNT(CASE WHEN velocity = 1 THEN 1 END) as low_velocity_count
            FROM sku_master 
            WHERE updated_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            AND velocity IS NOT NULL AND sku_code IS NOT NULL
            GROUP BY DATE(updated_at)
            ORDER BY date DESC
            LIMIT 30
            """
            cursor.execute(trends_query)
            trends = cursor.fetchall()
            
            # Try to get weighted scores from history for trends
            try:
                for trend in trends:
                    history_trend_query = """
                    SELECT ROUND(AVG(weighted_score), 2) as avg_weighted_score
                    FROM sku_velocity_history 
                    WHERE DATE(calculation_date) = %s
                    """
                    cursor.execute(history_trend_query, (trend['date'],))
                    history_trend = cursor.fetchone()
                    if history_trend and history_trend['avg_weighted_score']:
                        trend['avg_weighted_score'] = history_trend['avg_weighted_score']
                    else:
                        trend['avg_weighted_score'] = 0
            except:
                for trend in trends:
                    trend['avg_weighted_score'] = 0
            
            cursor.close()
            
            return {
                "success": True,
                "statistics": {
                    "sku_distribution": sku_distribution,
                    "bin_distribution": bin_distribution,
                    "overall_stats": overall_stats,
                    "capacity_analysis": capacity_analysis,
                    "trends": trends
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting velocity statistics: {str(e)}")
            return {"success": False, "message": str(e)}