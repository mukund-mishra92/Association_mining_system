import json
import logging
import threading
from datetime import datetime, timedelta, time
from typing import List, Dict, Optional, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
import pymysql
from app.shared.database.connection import DatabaseConnection
from app.modules.association_mining.services.clean_mining_service import CleanAssociationMiningService
from app.shared.config.config import config

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self, db_config=None):
        """Initialize the scheduler service with APScheduler"""
        self.db_config = db_config
        self.db_connection = DatabaseConnection(db_config)
        
        # Configure APScheduler
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': ThreadPoolExecutor(10)
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 1,
            'misfire_grace_time': 300  # 5 minutes
        }
        
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )
        
        self.is_running = False
        
    def start(self):
        """Start the scheduler"""
        try:
            if not self.is_running:
                self.scheduler.start()
                self.is_running = True
                logger.info("✓ Scheduler service started successfully")
                
                # Load existing schedules from database
                self._load_schedules_from_database()
                
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
            raise
    
    def stop(self):
        """Stop the scheduler"""
        try:
            if self.is_running:
                self.scheduler.shutdown(wait=False)
                self.is_running = False
                logger.info("✓ Scheduler service stopped")
        except Exception as e:
            logger.error(f"Failed to stop scheduler: {str(e)}")
    
    def create_schedule(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new mining schedule"""
        try:
            # Validate schedule data
            required_fields = ['job_name', 'schedule_type', 'schedule_time']
            for field in required_fields:
                if field not in schedule_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Connect to database
            self.db_connection.connect()
            
            # Prepare schedule parameters
            schedule_params = {
                'job_name': schedule_data['job_name'],
                'job_description': schedule_data.get('job_description', ''),
                'schedule_type': schedule_data['schedule_type'],
                'schedule_time': schedule_data['schedule_time'],
                'schedule_day_of_week': schedule_data.get('schedule_day_of_week'),
                'min_support': float(schedule_data.get('min_support', 0.300)),
                'min_confidence': float(schedule_data.get('min_confidence', 0.300)),
                'min_lift': float(schedule_data.get('min_lift', 1.0)),
                'max_recommendations': int(schedule_data.get('max_recommendations', 10)),
                'decay_rate': float(schedule_data.get('decay_rate', 0.050)),
                'output_table': schedule_data.get('output_table', 'sku_recommendations'),
                'is_active': schedule_data.get('is_active', True),
                'created_by': schedule_data.get('created_by', 'user')
            }
            
            # Calculate next run time
            next_run = self._calculate_next_run_time(
                schedule_params['schedule_type'], 
                schedule_params['schedule_time'],
                schedule_params.get('schedule_day_of_week')
            )
            schedule_params['next_run_at'] = next_run
            
            # Insert into database
            insert_query = """
                INSERT INTO mining_schedules (
                    job_name, job_description, schedule_type, schedule_time, 
                    schedule_day_of_week, min_support, min_confidence, min_lift,
                    max_recommendations, decay_rate, output_table, is_active,
                    created_by, next_run_at
                ) VALUES (
                    %(job_name)s, %(job_description)s, %(schedule_type)s, %(schedule_time)s,
                    %(schedule_day_of_week)s, %(min_support)s, %(min_confidence)s, %(min_lift)s,
                    %(max_recommendations)s, %(decay_rate)s, %(output_table)s, %(is_active)s,
                    %(created_by)s, %(next_run_at)s
                )
            """
            
            self.db_connection.cursor.execute(insert_query, schedule_params)
            schedule_id = self.db_connection.cursor.lastrowid
            self.db_connection.connection.commit()
            
            # Initialize stats record
            stats_query = """
                INSERT INTO mining_schedule_stats (schedule_id) 
                VALUES (%s)
            """
            self.db_connection.cursor.execute(stats_query, (schedule_id,))
            self.db_connection.connection.commit()
            
            # Add job to scheduler if active
            if schedule_params['is_active']:
                self._add_job_to_scheduler(schedule_id, schedule_params)
            
            logger.info(f"✓ Created schedule '{schedule_params['job_name']}' with ID {schedule_id}")
            
            return {
                'schedule_id': schedule_id,
                'job_name': schedule_params['job_name'],
                'next_run_at': next_run.isoformat() if next_run else None,
                'status': 'created'
            }
            
        except Exception as e:
            logger.error(f"Failed to create schedule: {str(e)}")
            if self.db_connection.connection:
                self.db_connection.connection.rollback()
            raise
        finally:
            self.db_connection.disconnect()
    
    def get_schedules(self) -> List[Dict[str, Any]]:
        """Get all schedules from database"""
        try:
            self.db_connection.connect()
            
            query = """
                SELECT s.*, st.total_executions, st.successful_executions, 
                       st.failed_executions, st.last_success_at, st.last_failure_at
                FROM mining_schedules s
                LEFT JOIN mining_schedule_stats st ON s.id = st.schedule_id
                ORDER BY s.created_at DESC
            """
            
            self.db_connection.cursor.execute(query)
            results = self.db_connection.cursor.fetchall()
            
            schedules = []
            for row in results:
                schedule = {
                    'id': row[0],
                    'job_name': row[1],
                    'job_description': row[2],
                    'schedule_type': row[3],
                    'schedule_time': str(row[4]),
                    'schedule_day_of_week': row[5],
                    'min_support': float(row[6]),
                    'min_confidence': float(row[7]),
                    'min_lift': float(row[8]),
                    'max_recommendations': row[9],
                    'decay_rate': float(row[10]),
                    'output_table': row[11],
                    'is_active': bool(row[12]),
                    'created_at': row[13].isoformat() if row[13] else None,
                    'updated_at': row[14].isoformat() if row[14] else None,
                    'last_run_at': row[15].isoformat() if row[15] else None,
                    'next_run_at': row[16].isoformat() if row[16] else None,
                    'created_by': row[17],
                    'stats': {
                        'total_executions': row[18] or 0,
                        'successful_executions': row[19] or 0,
                        'failed_executions': row[20] or 0,
                        'last_success_at': row[21].isoformat() if row[21] else None,
                        'last_failure_at': row[22].isoformat() if row[22] else None
                    }
                }
                schedules.append(schedule)
            
            return schedules
            
        except Exception as e:
            logger.error(f"Failed to get schedules: {str(e)}")
            raise
        finally:
            self.db_connection.disconnect()
    
    def update_schedule(self, schedule_id: int, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing schedule"""
        try:
            self.db_connection.connect()
            
            # Remove job from scheduler first
            job_id = f"mining_job_{schedule_id}"
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # Build update query dynamically
            update_fields = []
            update_values = {}
            
            allowed_fields = [
                'job_name', 'job_description', 'schedule_type', 'schedule_time',
                'schedule_day_of_week', 'min_support', 'min_confidence', 'min_lift',
                'max_recommendations', 'decay_rate', 'output_table', 'is_active'
            ]
            
            for field in allowed_fields:
                if field in schedule_data:
                    update_fields.append(f"{field} = %({field})s")
                    update_values[field] = schedule_data[field]
            
            if not update_fields:
                raise ValueError("No valid fields to update")
            
            # Calculate new next_run_at if schedule details changed
            if any(field in schedule_data for field in ['schedule_type', 'schedule_time', 'schedule_day_of_week']):
                # Get current schedule info
                self.db_connection.cursor.execute("SELECT schedule_type, schedule_time, schedule_day_of_week FROM mining_schedules WHERE id = %s", (schedule_id,))
                current = self.db_connection.cursor.fetchone()
                
                schedule_type = schedule_data.get('schedule_type', current[0])
                schedule_time = schedule_data.get('schedule_time', str(current[1]))
                schedule_day_of_week = schedule_data.get('schedule_day_of_week', current[2])
                
                next_run = self._calculate_next_run_time(schedule_type, schedule_time, schedule_day_of_week)
                update_fields.append("next_run_at = %(next_run_at)s")
                update_values['next_run_at'] = next_run
            
            update_query = f"""
                UPDATE mining_schedules 
                SET {', '.join(update_fields)}
                WHERE id = %(schedule_id)s
            """
            update_values['schedule_id'] = schedule_id
            
            self.db_connection.cursor.execute(update_query, update_values)
            self.db_connection.connection.commit()
            
            # Add job back to scheduler if active
            if schedule_data.get('is_active', True):
                # Get updated schedule info
                self.db_connection.cursor.execute("SELECT * FROM mining_schedules WHERE id = %s", (schedule_id,))
                schedule_row = self.db_connection.cursor.fetchone()
                if schedule_row:
                    schedule_params = self._row_to_schedule_dict(schedule_row)
                    self._add_job_to_scheduler(schedule_id, schedule_params)
            
            logger.info(f"✓ Updated schedule ID {schedule_id}")
            
            return {'schedule_id': schedule_id, 'status': 'updated'}
            
        except Exception as e:
            logger.error(f"Failed to update schedule: {str(e)}")
            if self.db_connection.connection:
                self.db_connection.connection.rollback()
            raise
        finally:
            self.db_connection.disconnect()
    
    def delete_schedule(self, schedule_id: int) -> Dict[str, Any]:
        """Delete a schedule"""
        try:
            # Remove job from scheduler
            job_id = f"mining_job_{schedule_id}"
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # Delete from database (cascade will handle related records)
            self.db_connection.connect()
            self.db_connection.cursor.execute("DELETE FROM mining_schedules WHERE id = %s", (schedule_id,))
            self.db_connection.connection.commit()
            
            logger.info(f"✓ Deleted schedule ID {schedule_id}")
            
            return {'schedule_id': schedule_id, 'status': 'deleted'}
            
        except Exception as e:
            logger.error(f"Failed to delete schedule: {str(e)}")
            if self.db_connection.connection:
                self.db_connection.connection.rollback()
            raise
        finally:
            self.db_connection.disconnect()
    
    def execute_mining_job(self, schedule_id: int):
        """Execute a mining job for a schedule - runs in background thread"""
        logger.info(f"🎯 Scheduling mining job for schedule {schedule_id} in background thread")
        
        # Run the actual mining in a separate thread to avoid blocking the API
        thread = threading.Thread(
            target=self._execute_mining_job_async,
            args=(schedule_id,),
            daemon=True,
            name=f"MiningJob-{schedule_id}"
        )
        thread.start()
        logger.info(f"✅ Mining job thread started for schedule {schedule_id}")
    
    def _execute_mining_job_async(self, schedule_id: int):
        """Internal method that runs the actual mining job asynchronously"""
        start_time = datetime.now()
        log_id = None
        
        # Create a separate database connection for this background thread
        thread_db_connection = None
        
        try:
            # Initialize separate database connection for this thread
            from app.shared.database.connection import DatabaseConnection
            thread_db_connection = DatabaseConnection(self.db_config)
            thread_db_connection.connect()
            
            # Get schedule details
            thread_db_connection.cursor.execute("SELECT * FROM mining_schedules WHERE id = %s", (schedule_id,))
            schedule_row = thread_db_connection.cursor.fetchone()
            
            if not schedule_row:
                raise ValueError(f"Schedule {schedule_id} not found")
            
            schedule = self._row_to_schedule_dict(schedule_row)
            
            # Create job log entry
            log_query = """
                INSERT INTO mining_job_logs (
                    schedule_id, job_name, execution_parameters, started_at
                ) VALUES (%s, %s, %s, %s)
            """
            execution_params = {
                'min_support': schedule['min_support'],
                'min_confidence': schedule['min_confidence'],
                'min_lift': schedule['min_lift'],
                'max_recommendations': schedule['max_recommendations'],
                'decay_rate': schedule['decay_rate']
            }
            
            thread_db_connection.cursor.execute(log_query, (
                schedule_id, 
                schedule['job_name'],
                json.dumps(execution_params),
                start_time
            ))
            log_id = thread_db_connection.cursor.lastrowid
            thread_db_connection.connection.commit()
            
            logger.info(f"🚀 Starting mining job for schedule '{schedule['job_name']}' (ID: {schedule_id})")
            
            # Execute mining with optimized schedule parameters for performance
            algorithm_params = {
                'min_support': max(0.05, schedule['min_support']),  # Use at least 5% support for performance
                'min_confidence': max(0.1, schedule['min_confidence']),  # Use at least 10% confidence  
                'min_lift': schedule['min_lift'],
                'max_recommendations': schedule['max_recommendations'],
                'decay_rate': schedule['decay_rate']
            }
            
            # Log the optimized parameters
            logger.info(f"🎯 Optimized algorithm parameters: {algorithm_params}")
            
            # Connect to database for data fetching
            from app.shared.database.connection import DatabaseConnection
            data_db = DatabaseConnection()
            
            # Debug logging for database configuration
            logger.info(f"🔍 Database config: host={data_db.db_host}, database={data_db.db_name}")
            logger.info(f"🔍 Order table: {data_db.order_table}")
            logger.info(f"🔍 SKU master table: {data_db.sku_master_table}")
            
            if not data_db.connect():
                raise Exception("Failed to connect to database for data fetching")
                
            # Fetch order data (use optimized parameters for performance)
            days_back = schedule.get('days_back', 365)  # Default to 1 year for historical data
            logger.info(f"🔍 Fetching order data for last {days_back} days")
            
            # Use optimized filtering for scheduled jobs (similar to fast mining)
            df_basket = data_db.fetch_order_data(
                days_back=days_back,
                max_items=200,  # Reduced from 1000 for better performance
                min_item_frequency=5  # Increased from 2 for better quality and performance
            )
            logger.info(f"🔍 Fetched data shape: {df_basket.shape if df_basket is not None else 'None'}")
            
            if df_basket is None or df_basket.empty:
                logger.error(f"❌ No data found with {days_back} days - trying more lenient criteria...")
                # Try with more lenient criteria
                df_basket = data_db.fetch_order_data(
                    days_back=days_back,
                    max_items=500,  # Still reasonable
                    min_item_frequency=2
                )
                logger.info(f"🔍 Second attempt data shape: {df_basket.shape if df_basket is not None else 'None'}")
                
                if df_basket is None or df_basket.empty:
                    raise Exception("No data found for mining even with lenient criteria")
            
            # Create mining service
            mining_service = CleanAssociationMiningService(
                task_id=f"scheduled_{schedule_id}_{int(start_time.timestamp())}",
                task_manager=None,  # No task manager for scheduled jobs
                algorithm_params=algorithm_params
            )
            
            # Run mining pipeline
            recommendations = mining_service.run_mining_pipeline(df_basket)
            
            # Save recommendations to database
            if not recommendations.empty:
                success = data_db.save_recommendations(recommendations)
                if not success:
                    raise Exception("Failed to save recommendations to database")
                
            results = {
                'total_rules': len(recommendations) if not recommendations.empty else 0,
                'records_processed': len(df_basket)
            }
            
            # Calculate execution time
            end_time = datetime.now()
            execution_time = int((end_time - start_time).total_seconds())
            
            # Update job log with success
            update_log_query = """
                UPDATE mining_job_logs 
                SET completed_at = %s, execution_status = 'success', 
                    rules_generated = %s, execution_time_seconds = %s,
                    records_processed = %s
                WHERE id = %s
            """
            
            rules_count = results.get('total_rules', 0) if results else 0
            records_processed = results.get('records_processed', 0) if results else 0
            
            thread_db_connection.cursor.execute(update_log_query, (
                end_time, rules_count, execution_time, records_processed, log_id
            ))
            
            # Update schedule last_run_at and next_run_at
            next_run = self._calculate_next_run_time(
                schedule['schedule_type'],
                schedule['schedule_time'],
                schedule.get('schedule_day_of_week')
            )
            
            schedule_update_query = """
                UPDATE mining_schedules 
                SET last_run_at = %s, next_run_at = %s 
                WHERE id = %s
            """
            thread_db_connection.cursor.execute(schedule_update_query, (end_time, next_run, schedule_id))
            
            # Update statistics using thread connection
            self._update_schedule_stats_with_connection(thread_db_connection, schedule_id, True, execution_time, rules_count)
            
            thread_db_connection.connection.commit()
            
            logger.info(f"✅ Mining job completed successfully for schedule '{schedule['job_name']}' - Generated {rules_count} rules in {execution_time}s")
            
        except Exception as e:
            end_time = datetime.now()
            execution_time = int((end_time - start_time).total_seconds())
            
            logger.error(f"❌ Mining job failed for schedule {schedule_id}: {str(e)}")
            
            # Update job log with failure
            if log_id and thread_db_connection:
                try:
                    update_log_query = """
                        UPDATE mining_job_logs 
                        SET completed_at = %s, execution_status = 'failed',
                            execution_time_seconds = %s, error_message = %s
                        WHERE id = %s
                    """
                    thread_db_connection.cursor.execute(update_log_query, (
                        end_time, execution_time, str(e), log_id
                    ))
                    
                    # Update statistics using thread connection
                    self._update_schedule_stats_with_connection(thread_db_connection, schedule_id, False, execution_time, 0)
                    
                    thread_db_connection.connection.commit()
                except Exception as log_error:
                    logger.error(f"Failed to update job log: {str(log_error)}")
            
        finally:
            # Clean up the thread-specific database connection
            if thread_db_connection:
                try:
                    thread_db_connection.disconnect()
                except Exception as disconnect_error:
                    logger.error(f"Error disconnecting thread database connection: {str(disconnect_error)}")
    
    def _load_schedules_from_database(self):
        """Load existing active schedules from database and add to scheduler"""
        try:
            schedules = self.get_schedules()
            for schedule in schedules:
                if schedule['is_active']:
                    self._add_job_to_scheduler(schedule['id'], schedule)
            
            logger.info(f"✓ Loaded {len([s for s in schedules if s['is_active']])} active schedules")
            
        except Exception as e:
            logger.error(f"Failed to load schedules from database: {str(e)}")
    
    def _add_job_to_scheduler(self, schedule_id: int, schedule_params: Dict[str, Any]):
        """Add a job to the APScheduler"""
        try:
            job_id = f"mining_job_{schedule_id}"
            
            # Remove existing job if it exists
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # Parse time
            time_parts = schedule_params['schedule_time'].split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            
            # Create trigger based on schedule type
            if schedule_params['schedule_type'] == 'daily':
                trigger = CronTrigger(hour=hour, minute=minute)
            elif schedule_params['schedule_type'] == 'weekly':
                day_of_week = schedule_params.get('schedule_day_of_week', 0)
                trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
            else:
                raise ValueError(f"Unsupported schedule type: {schedule_params['schedule_type']}")
            
            # Add job to scheduler
            self.scheduler.add_job(
                func=self.execute_mining_job,
                trigger=trigger,
                args=[schedule_id],
                id=job_id,
                name=f"Mining: {schedule_params['job_name']}",
                replace_existing=True
            )
            
            logger.info(f"✓ Added job '{schedule_params['job_name']}' to scheduler")
            
        except Exception as e:
            logger.error(f"Failed to add job to scheduler: {str(e)}")
            raise
    
    def _calculate_next_run_time(self, schedule_type: str, schedule_time: str, day_of_week: Optional[int] = None) -> datetime:
        """Calculate the next run time for a schedule"""
        now = datetime.now()
        time_parts = schedule_time.split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        
        if schedule_type == 'daily':
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        elif schedule_type == 'weekly':
            if day_of_week is None:
                day_of_week = 0  # Default to Monday
            
            days_ahead = day_of_week - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            
            next_run = (now + timedelta(days=days_ahead)).replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
        else:
            raise ValueError(f"Unsupported schedule type: {schedule_type}")
        
        return next_run
    
    def _update_schedule_stats(self, schedule_id: int, success: bool, execution_time: int, rules_generated: int):
        """Update schedule statistics using the main database connection"""
        self._update_schedule_stats_with_connection(self.db_connection, schedule_id, success, execution_time, rules_generated)

    def _update_schedule_stats_with_connection(self, db_conn, schedule_id: int, success: bool, execution_time: int, rules_generated: int):
        """Update schedule statistics with a specific database connection"""
        try:
            if success:
                stats_query = """
                    UPDATE mining_schedule_stats 
                    SET total_executions = total_executions + 1,
                        successful_executions = successful_executions + 1,
                        last_success_at = NOW(),
                        avg_execution_time_seconds = (
                            (avg_execution_time_seconds * successful_executions + %s) / (successful_executions + 1)
                        ),
                        total_rules_generated = total_rules_generated + %s
                    WHERE schedule_id = %s
                """
                db_conn.cursor.execute(stats_query, (execution_time, rules_generated, schedule_id))
            else:
                stats_query = """
                    UPDATE mining_schedule_stats 
                    SET total_executions = total_executions + 1,
                        failed_executions = failed_executions + 1,
                        last_failure_at = NOW()
                    WHERE schedule_id = %s
                """
                db_conn.cursor.execute(stats_query, (schedule_id,))
            
        except Exception as e:
            logger.error(f"Failed to update schedule stats: {str(e)}")
    
    def _row_to_schedule_dict(self, row) -> Dict[str, Any]:
        """Convert database row to schedule dictionary"""
        return {
            'id': row[0],
            'job_name': row[1],
            'job_description': row[2],
            'schedule_type': row[3],
            'schedule_time': str(row[4]),
            'schedule_day_of_week': row[5],
            'min_support': float(row[6]),
            'min_confidence': float(row[7]),
            'min_lift': float(row[8]),
            'max_recommendations': row[9],
            'decay_rate': float(row[10]),
            'output_table': row[11],
            'is_active': bool(row[12]),
            'created_at': row[13],
            'updated_at': row[14],
            'last_run_at': row[15],
            'next_run_at': row[16],
            'created_by': row[17]
        }
    
    def get_job_logs(self, schedule_id: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get job execution logs"""
        try:
            self.db_connection.connect()
            
            if schedule_id:
                query = """
                    SELECT * FROM mining_job_logs 
                    WHERE schedule_id = %s 
                    ORDER BY started_at DESC 
                    LIMIT %s
                """
                self.db_connection.cursor.execute(query, (schedule_id, limit))
            else:
                query = """
                    SELECT * FROM mining_job_logs 
                    ORDER BY started_at DESC 
                    LIMIT %s
                """
                self.db_connection.cursor.execute(query, (limit,))
            
            results = self.db_connection.cursor.fetchall()
            
            logs = []
            for row in results:
                log = {
                    'id': row[0],
                    'schedule_id': row[1],
                    'job_name': row[2],
                    'started_at': row[3].isoformat() if row[3] else None,
                    'completed_at': row[4].isoformat() if row[4] else None,
                    'execution_status': row[5],
                    'rules_generated': row[6],
                    'records_processed': row[7],
                    'execution_time_seconds': row[8],
                    'error_message': row[9],
                    'error_details': json.loads(row[10]) if row[10] else None,
                    'execution_parameters': json.loads(row[11]) if row[11] else None
                }
                logs.append(log)
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get job logs: {str(e)}")
            raise
        finally:
            self.db_connection.disconnect()

# Global scheduler instance
scheduler_service = None

def get_scheduler_service(db_config=None) -> SchedulerService:
    """Get or create the global scheduler service instance"""
    global scheduler_service
    if scheduler_service is None:
        scheduler_service = SchedulerService(db_config)
    return scheduler_service