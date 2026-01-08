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
            
            # Prepare schedule parameters with all mining parameters
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
                'created_by': schedule_data.get('created_by', 'user'),
                # New parameters for data filtering and mining control
                'days_back': int(schedule_data.get('days_back', 365)),
                'max_items': int(schedule_data.get('max_items', 200)),
                'min_item_frequency': int(schedule_data.get('min_item_frequency', 5)),
                'use_enhanced_mining': bool(schedule_data.get('use_enhanced_mining', True)),
                'time_weighting_method': schedule_data.get('time_weighting_method', 'exponential_decay'),
                'time_segmentation': schedule_data.get('time_segmentation', 'weekly')
            }
            
            # Calculate next run time
            next_run = self._calculate_next_run_time(
                schedule_params['schedule_type'], 
                schedule_params['schedule_time'],
                schedule_params.get('schedule_day_of_week')
            )
            schedule_params['next_run_at'] = next_run
            
            # Insert into database with all parameters
            insert_query = """
                INSERT INTO mining_schedules (
                    job_name, job_description, schedule_type, schedule_time, 
                    schedule_day_of_week, min_support, min_confidence, min_lift,
                    max_recommendations, decay_rate, output_table, is_active,
                    created_by, next_run_at, days_back, max_items, min_item_frequency,
                    use_enhanced_mining, time_weighting_method, time_segmentation
                ) VALUES (
                    %(job_name)s, %(job_description)s, %(schedule_type)s, %(schedule_time)s,
                    %(schedule_day_of_week)s, %(min_support)s, %(min_confidence)s, %(min_lift)s,
                    %(max_recommendations)s, %(decay_rate)s, %(output_table)s, %(is_active)s,
                    %(created_by)s, %(next_run_at)s, %(days_back)s, %(max_items)s, %(min_item_frequency)s,
                    %(use_enhanced_mining)s, %(time_weighting_method)s, %(time_segmentation)s
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
    
    def get_schedules(self):
        """Get all schedules from database"""
        try:
            # Use the existing db_connection attribute
            self.db_connection.connect()
            
            query = """
            SELECT 
                id,
                job_name,
                job_description,
                schedule_type,
                schedule_time,
                is_active,
                next_run_at,
                last_run_at,
                created_at,
                min_support,
                min_confidence,
                min_lift,
                max_recommendations,
                decay_rate,
                output_table
            FROM mining_schedules
            ORDER BY created_at DESC
            """
            
            self.db_connection.cursor.execute(query)
            schedules = self.db_connection.cursor.fetchall()
            
            # Helper function to safely convert datetime/time/timedelta to string
            def safe_isoformat(dt):
                if dt is None:
                    return None
                if isinstance(dt, str):
                    return dt  # Already a string
                if isinstance(dt, timedelta):
                    return str(dt)  # Convert timedelta to string
                if hasattr(dt, 'isoformat'):
                    return dt.isoformat()  # datetime, date, or time objects
                return str(dt)  # Fallback to string conversion
            
            result = []
            for schedule in schedules:
                result.append({
                    'id': schedule[0],
                    'job_name': schedule[1],
                    'job_description': schedule[2],
                    'schedule_type': schedule[3],
                    'schedule_time': safe_isoformat(schedule[4]),  # FIX: Use helper
                    'is_active': bool(schedule[5]),
                    'next_run_at': safe_isoformat(schedule[6]),    # FIX: Use helper
                    'last_run_at': safe_isoformat(schedule[7]),    # FIX: Use helper
                    'created_at': safe_isoformat(schedule[8]),     # FIX: Use helper
                    'min_support': float(schedule[9]) if schedule[9] else None,
                    'min_confidence': float(schedule[10]) if schedule[10] else None,
                    'min_lift': float(schedule[11]) if schedule[11] else None,
                    'max_recommendations': int(schedule[12]) if schedule[12] else None,
                    'decay_rate': float(schedule[13]) if schedule[13] else None,
                    'output_table': schedule[14]
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get schedules: {str(e)}")
            raise    
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
    
    def delete_all_schedules(self) -> Dict[str, Any]:
        """Delete all schedules and related data"""
        try:
            self.db_connection.connect()
            
            # Get counts before deletion - fetchone returns tuple, not dict
            self.db_connection.cursor.execute("SELECT COUNT(*) FROM mining_schedules")
            result = self.db_connection.cursor.fetchone()
            schedule_count = result[0] if result else 0
            
            self.db_connection.cursor.execute("SELECT COUNT(*) FROM mining_job_logs")
            result = self.db_connection.cursor.fetchone()
            log_count = result[0] if result else 0
            
            self.db_connection.cursor.execute("SELECT COUNT(*) FROM mining_schedule_stats")
            result = self.db_connection.cursor.fetchone()
            stats_count = result[0] if result else 0
            
            # Remove all jobs from scheduler
            self.scheduler.remove_all_jobs()
            
            # Delete all schedules (cascade will handle logs and stats)
            self.db_connection.cursor.execute("DELETE FROM mining_schedules")
            self.db_connection.connection.commit()
            
            logger.info(f"✓ Deleted all schedules: {schedule_count} schedules, {log_count} logs, {stats_count} stats")
            
            return {
                'deleted_schedules': schedule_count,
                'deleted_logs': log_count,
                'deleted_stats': stats_count,
                'status': 'all_deleted'
            }
            
        except Exception as e:
            logger.error(f"Failed to delete all schedules: {str(e)}")
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
        """Internal method that runs the actual mining job asynchronously
        
        This method now uses the shared run_mining_task() function from the API endpoints
        to ensure scheduler and manual mining use the exact same logic and parameters.
        """
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
                'decay_rate': schedule['decay_rate'],
                'days_back': schedule.get('days_back', 365),
                'use_enhanced_mining': schedule.get('use_enhanced_mining', True),
                'time_weighting_method': schedule.get('time_weighting_method', 'exponential_decay'),
                'time_segmentation': schedule.get('time_segmentation', 'weekly')
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
            logger.info(f"🎯 Using parameters: {execution_params}")
            
            # Import the shared mining task function
            from app.modules.association_mining.api.endpoints import run_mining_task
            
            # Create custom config with output_table from schedule
            custom_db_config = {
                'recommendations_table': schedule.get('output_table', 'sku_recommendations')
            }
            if self.db_config:
                custom_db_config.update(self.db_config)
            
            # Create a minimal task manager for scheduler jobs
            class SchedulerTaskManager:
                """Minimal task manager for scheduler jobs that logs to mining_job_logs"""
                def __init__(self, log_id, db_connection):
                    self.log_id = log_id
                    self.db_connection = db_connection
                
                def start_task(self, task_id, message):
                    logger.info(f"📋 {message}")
                
                def update_progress(self, task_id, progress, message):
                    logger.info(f"⏳ Progress {int(progress*100)}%: {message}")
                
                def complete_task(self, task_id, result=None, message=""):
                    logger.info(f"✅ {message}")
                    self.result = result
                
                def fail_task(self, task_id, error_msg):
                    logger.error(f"❌ {error_msg}")
                    self.error = error_msg
            
            # Create task manager for this job
            task_manager = SchedulerTaskManager(log_id, thread_db_connection)
            
            # Temporarily replace the global task_manager
            import app.modules.association_mining.api.endpoints as endpoints_module
            original_task_manager = endpoints_module.task_manager
            endpoints_module.task_manager = task_manager
            
            try:
                # Call the shared mining function with timeout protection
                timeout_seconds = 600
                logger.info(f"⏱️ Setting {timeout_seconds} second timeout for mining job")
                
                import threading
                mining_completed = threading.Event()
                mining_error = {'error': None}
                
                def run_mining_with_timeout():
                    try:
                        run_mining_task(
                            task_id=f"scheduled_{schedule_id}_{int(start_time.timestamp())}",
                            days_back=schedule.get('days_back', 365),
                            min_support=schedule['min_support'],
                            min_confidence=schedule['min_confidence'],
                            min_lift=schedule['min_lift'],
                            max_recommendations=schedule['max_recommendations'],
                            decay_rate=schedule['decay_rate'],
                            use_enhanced_mining=schedule.get('use_enhanced_mining', True),
                            time_weighting_method=schedule.get('time_weighting_method', 'exponential_decay'),
                            time_segmentation=schedule.get('time_segmentation', 'weekly'),
                            db_config=custom_db_config
                        )
                        mining_completed.set()
                    except Exception as e:
                        mining_error['error'] = e
                        mining_completed.set()
                
                mining_thread = threading.Thread(target=run_mining_with_timeout, daemon=True)
                mining_thread.start()
                
                # Wait for completion or timeout
                if not mining_completed.wait(timeout=timeout_seconds):
                    raise TimeoutError(f"Mining job exceeded {timeout_seconds} second timeout")
                
                if mining_error['error']:
                    raise mining_error['error']
                
                # Get results from task manager
                if hasattr(task_manager, 'result') and task_manager.result:
                    results = task_manager.result
                    rules_count = results.get('recommendations_count', 0)
                    records_processed = results.get('stats', {}).get('total_orders', 0)
                else:
                    # If no result set, assume success with 0 rules
                    rules_count = 0
                    records_processed = 0
                
            finally:
                # Restore original task_manager
                endpoints_module.task_manager = original_task_manager
            
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