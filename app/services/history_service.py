"""
Database History Service for Association Mining System
Handles job history tracking, performance analytics, and historical analysis
"""

import pymysql
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import traceback

class HistoryService:
    def __init__(self, db_config: Dict[str, Any]):
        """Initialize with database configuration"""
        # Filter config to only include valid pymysql connection parameters
        valid_connection_keys = {'host', 'port', 'user', 'password', 'database', 'charset', 'autocommit'}
        self.db_config = {k: v for k, v in db_config.items() if k in valid_connection_keys}
        
        # Add default charset if not specified
        if 'charset' not in self.db_config:
            self.db_config['charset'] = 'utf8mb4'
            
        self.logger = logging.getLogger(__name__)
        
    def create_history_tables(self):
        """Create history and statistics tables if they don't exist"""
        try:
            self.logger.info(f"Attempting to connect to database with config: {self.db_config}")
            connection = pymysql.connect(**self.db_config)
            cursor = connection.cursor()
            
            # Create mining_history table
            create_history_table = """
            CREATE TABLE IF NOT EXISTS mining_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                job_id VARCHAR(100) UNIQUE NOT NULL,
                job_name VARCHAR(200),
                mining_method ENUM('direct', 'api') NOT NULL,
                mining_type VARCHAR(50) DEFAULT 'association',
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                duration_seconds INT,
                status ENUM('running', 'completed', 'failed', 'cancelled') DEFAULT 'running',
                parameters JSON,
                results_count INT DEFAULT 0,
                error_message TEXT,
                user_ip VARCHAR(45),
                database_used VARCHAR(100),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_job_id (job_id),
                INDEX idx_start_time (start_time),
                INDEX idx_status (status),
                INDEX idx_mining_method (mining_method)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            
            # Create mining_statistics table
            create_stats_table = """
            CREATE TABLE IF NOT EXISTS mining_statistics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                job_id VARCHAR(100) NOT NULL,
                metric_name VARCHAR(100) NOT NULL,
                metric_value DECIMAL(15,6),
                metric_text VARCHAR(500),
                metric_json JSON,
                recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES mining_history(job_id) ON DELETE CASCADE,
                INDEX idx_job_id (job_id),
                INDEX idx_metric_name (metric_name),
                INDEX idx_recorded_at (recorded_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            
            # Create performance_metrics table
            create_perf_table = """
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                job_id VARCHAR(100) NOT NULL,
                cpu_usage_percent DECIMAL(5,2),
                memory_usage_mb DECIMAL(10,2),
                disk_io_mb DECIMAL(10,2),
                network_io_mb DECIMAL(10,2),
                db_query_time_ms DECIMAL(10,2),
                processing_time_ms DECIMAL(10,2),
                rules_generated INT DEFAULT 0,
                rules_filtered INT DEFAULT 0,
                confidence_avg DECIMAL(5,4),
                confidence_max DECIMAL(5,4),
                confidence_min DECIMAL(5,4),
                support_avg DECIMAL(5,4),
                support_max DECIMAL(5,4),
                support_min DECIMAL(5,4),
                lift_avg DECIMAL(8,4),
                lift_max DECIMAL(8,4),
                lift_min DECIMAL(8,4),
                recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES mining_history(job_id) ON DELETE CASCADE,
                INDEX idx_job_id (job_id),
                INDEX idx_recorded_at (recorded_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            
            cursor.execute(create_history_table)
            cursor.execute(create_stats_table)
            cursor.execute(create_perf_table)
            
            connection.commit()
            cursor.close()
            connection.close()
            
            self.logger.info("History tables created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating history tables: {str(e)}")
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return False
    
    def start_job(self, job_id: str, job_name: str, mining_method: str, 
                  parameters: Dict, user_ip: str = None) -> bool:
        """Start tracking a new mining job"""
        try:
            connection = pymysql.connect(**self.db_config)
            cursor = connection.cursor()
            
            query = """
            INSERT INTO mining_history 
            (job_id, job_name, mining_method, start_time, parameters, user_ip, database_used, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'running')
            """
            
            cursor.execute(query, (
                job_id,
                job_name,
                mining_method,
                datetime.now(),
                json.dumps(parameters),
                user_ip,
                self.db_config.get('database', 'neo')
            ))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            self.logger.info(f"Started tracking job: {job_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting job tracking: {str(e)}")
            return False
    
    def finish_job(self, job_id: str, status: str = 'completed', 
                   results_count: int = 0, error_message: str = None) -> bool:
        """Mark a job as finished and calculate duration"""
        try:
            connection = pymysql.connect(**self.db_config)
            cursor = connection.cursor()
            
            # Get start time to calculate duration
            cursor.execute("SELECT start_time FROM mining_history WHERE job_id = %s", (job_id,))
            result = cursor.fetchone()
            
            if result:
                start_time = result[0]
                end_time = datetime.now()
                duration = int((end_time - start_time).total_seconds())
                
                query = """
                UPDATE mining_history 
                SET end_time = %s, duration_seconds = %s, status = %s, 
                    results_count = %s, error_message = %s
                WHERE job_id = %s
                """
                
                cursor.execute(query, (
                    end_time, duration, status, results_count, error_message, job_id
                ))
                
                connection.commit()
                self.logger.info(f"Finished tracking job: {job_id} with status: {status}")
                
            cursor.close()
            connection.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Error finishing job tracking: {str(e)}")
            return False
    
    def log_performance_metrics(self, job_id: str, metrics: Dict[str, Any]) -> bool:
        """Log performance metrics for a job"""
        try:
            connection = pymysql.connect(**self.db_config)
            cursor = connection.cursor()
            
            query = """
            INSERT INTO performance_metrics 
            (job_id, cpu_usage_percent, memory_usage_mb, db_query_time_ms, 
             processing_time_ms, rules_generated, rules_filtered, confidence_avg, 
             confidence_max, confidence_min, support_avg, support_max, support_min,
             lift_avg, lift_max, lift_min)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                job_id,
                metrics.get('cpu_usage', 0),
                metrics.get('memory_usage', 0),
                metrics.get('db_query_time', 0),
                metrics.get('processing_time', 0),
                metrics.get('rules_generated', 0),
                metrics.get('rules_filtered', 0),
                metrics.get('confidence_avg', 0),
                metrics.get('confidence_max', 0),
                metrics.get('confidence_min', 0),
                metrics.get('support_avg', 0),
                metrics.get('support_max', 0),
                metrics.get('support_min', 0),
                metrics.get('lift_avg', 0),
                metrics.get('lift_max', 0),
                metrics.get('lift_min', 0)
            ))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            self.logger.info(f"Logged performance metrics for job: {job_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error logging performance metrics: {str(e)}")
            return False
    
    def log_custom_metric(self, job_id: str, metric_name: str, 
                         value: float = None, text: str = None, json_data: Dict = None) -> bool:
        """Log a custom metric for a job"""
        try:
            connection = pymysql.connect(**self.db_config)
            cursor = connection.cursor()
            
            query = """
            INSERT INTO mining_statistics 
            (job_id, metric_name, metric_value, metric_text, metric_json)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                job_id,
                metric_name,
                value,
                text,
                json.dumps(json_data) if json_data else None
            ))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error logging custom metric: {str(e)}")
            return False
    
    def get_job_history(self, limit: int = 100, offset: int = 0, 
                       status: str = None, days: int = None) -> List[Dict]:
        """Get job history with optional filtering"""
        try:
            connection = pymysql.connect(**self.db_config)
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            
            where_conditions = []
            params = []
            
            if status:
                where_conditions.append("status = %s")
                params.append(status)
            
            if days:
                cutoff_date = datetime.now() - timedelta(days=days)
                where_conditions.append("start_time >= %s")
                params.append(cutoff_date)
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            query = f"""
            SELECT * FROM mining_history 
            {where_clause}
            ORDER BY start_time DESC 
            LIMIT %s OFFSET %s
            """
            
            params.extend([limit, offset])
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # Parse JSON parameters
            for result in results:
                if result['parameters']:
                    try:
                        result['parameters'] = json.loads(result['parameters'])
                    except:
                        result['parameters'] = {}
            
            cursor.close()
            connection.close()
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error getting job history: {str(e)}")
            return []
    
    def get_performance_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get performance analytics for the specified period"""
        try:
            connection = pymysql.connect(**self.db_config)
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Job statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_jobs,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_jobs,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_jobs,
                    AVG(duration_seconds) as avg_duration,
                    MAX(duration_seconds) as max_duration,
                    MIN(duration_seconds) as min_duration,
                    SUM(results_count) as total_rules_generated
                FROM mining_history 
                WHERE start_time >= %s
            """, (cutoff_date,))
            
            job_stats = cursor.fetchone()
            
            # Performance metrics averages
            cursor.execute("""
                SELECT 
                    AVG(pm.cpu_usage_percent) as avg_cpu,
                    AVG(pm.memory_usage_mb) as avg_memory,
                    AVG(pm.processing_time_ms) as avg_processing_time,
                    AVG(pm.confidence_avg) as avg_confidence,
                    AVG(pm.support_avg) as avg_support,
                    AVG(pm.lift_avg) as avg_lift
                FROM performance_metrics pm
                JOIN mining_history mh ON pm.job_id = mh.job_id
                WHERE mh.start_time >= %s
            """, (cutoff_date,))
            
            perf_stats = cursor.fetchone()
            
            # Daily job counts
            cursor.execute("""
                SELECT 
                    DATE(start_time) as job_date,
                    COUNT(*) as job_count,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count
                FROM mining_history 
                WHERE start_time >= %s
                GROUP BY DATE(start_time)
                ORDER BY job_date DESC
                LIMIT 30
            """, (cutoff_date,))
            
            daily_stats = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            return {
                'job_statistics': job_stats,
                'performance_metrics': perf_stats,
                'daily_trends': daily_stats,
                'period_days': days
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance analytics: {str(e)}")
            return {}
    
    def get_job_details(self, job_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific job"""
        try:
            connection = pymysql.connect(**self.db_config)
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            
            # Get job history
            cursor.execute("SELECT * FROM mining_history WHERE job_id = %s", (job_id,))
            job_info = cursor.fetchone()
            
            if not job_info:
                return {}
            
            # Parse JSON parameters
            if job_info['parameters']:
                try:
                    job_info['parameters'] = json.loads(job_info['parameters'])
                except:
                    job_info['parameters'] = {}
            
            # Get performance metrics
            cursor.execute("SELECT * FROM performance_metrics WHERE job_id = %s", (job_id,))
            performance = cursor.fetchall()
            
            # Get custom statistics
            cursor.execute("SELECT * FROM mining_statistics WHERE job_id = %s ORDER BY recorded_at", (job_id,))
            statistics = cursor.fetchall()
            
            # Parse JSON data in statistics
            for stat in statistics:
                if stat['metric_json']:
                    try:
                        stat['metric_json'] = json.loads(stat['metric_json'])
                    except:
                        stat['metric_json'] = {}
            
            cursor.close()
            connection.close()
            
            return {
                'job_info': job_info,
                'performance_metrics': performance,
                'statistics': statistics
            }
            
        except Exception as e:
            self.logger.error(f"Error getting job details: {str(e)}")
            return {}
    
    def cleanup_old_records(self, days: int = 90) -> bool:
        """Clean up old history records"""
        try:
            connection = pymysql.connect(**self.db_config)
            cursor = connection.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Delete old records (cascade will handle related tables)
            cursor.execute("DELETE FROM mining_history WHERE start_time < %s", (cutoff_date,))
            deleted_count = cursor.rowcount
            
            connection.commit()
            cursor.close()
            connection.close()
            
            self.logger.info(f"Cleaned up {deleted_count} old history records")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old records: {str(e)}")
            return False