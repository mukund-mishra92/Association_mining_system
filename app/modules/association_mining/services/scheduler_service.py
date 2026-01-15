# # import json
# # import logging
# # import threading
# # from datetime import datetime, timedelta, time
# # from typing import List, Dict, Optional, Any
# # from apscheduler.schedulers.background import BackgroundScheduler
# # from apscheduler.triggers.cron import CronTrigger
# # from apscheduler.jobstores.memory import MemoryJobStore
# # from apscheduler.executors.pool import ThreadPoolExecutor
# # import pymysql
# # from app.shared.database.connection import DatabaseConnection
# # from app.modules.association_mining.services.clean_mining_service import CleanAssociationMiningService
# # from app.shared.config.config import config

# # logger = logging.getLogger(__name__)

# # class SchedulerService:
# #     def __init__(self, db_config=None):
# #         """Initialize the scheduler service with APScheduler"""
# #         self.db_config = db_config
# #         self.db_connection = DatabaseConnection(db_config)
        
# #         # Configure APScheduler
# #         jobstores = {
# #             'default': MemoryJobStore()
# #         }
# #         executors = {
# #             'default': ThreadPoolExecutor(10)
# #         }
# #         job_defaults = {
# #             'coalesce': False,
# #             'max_instances': 1,
# #             'misfire_grace_time': 300  # 5 minutes
# #         }
        
# #         self.scheduler = BackgroundScheduler(
# #             jobstores=jobstores,
# #             executors=executors,
# #             job_defaults=job_defaults,
# #             timezone='UTC'
# #         )
        
# #         self.is_running = False
        
# #     def start(self):
# #         """Start the scheduler"""
# #         try:
# #             if not self.is_running:
# #                 self.scheduler.start()
# #                 self.is_running = True
# #                 logger.info("✓ Scheduler service started successfully")
                
# #                 # Load existing schedules from database
# #                 self._load_schedules_from_database()
                
# #         except Exception as e:
# #             logger.error(f"Failed to start scheduler: {str(e)}")
# #             raise
    
# #     def stop(self):
# #         """Stop the scheduler"""
# #         try:
# #             if self.is_running:
# #                 self.scheduler.shutdown(wait=False)
# #                 self.is_running = False
# #                 logger.info("✓ Scheduler service stopped")
# #         except Exception as e:
# #             logger.error(f"Failed to stop scheduler: {str(e)}")
    
# #     def create_schedule(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
# #         """Create a new mining schedule"""
# #         try:
# #             # Validate schedule data
# #             required_fields = ['job_name', 'schedule_type', 'schedule_time']
# #             for field in required_fields:
# #                 if field not in schedule_data:
# #                     raise ValueError(f"Missing required field: {field}")
            
# #             # Connect to database
# #             self.db_connection.connect()
            
# #             # Prepare schedule parameters with all mining parameters
# #             schedule_params = {
# #                 'job_name': schedule_data['job_name'],
# #                 'job_description': schedule_data.get('job_description', ''),
# #                 'schedule_type': schedule_data['schedule_type'],
# #                 'schedule_time': schedule_data['schedule_time'],
# #                 'schedule_day_of_week': schedule_data.get('schedule_day_of_week'),
# #                 'min_support': float(schedule_data.get('min_support', 0.300)),
# #                 'min_confidence': float(schedule_data.get('min_confidence', 0.300)),
# #                 'min_lift': float(schedule_data.get('min_lift', 1.0)),
# #                 'max_recommendations': int(schedule_data.get('max_recommendations', 10)),
# #                 'decay_rate': float(schedule_data.get('decay_rate', 0.050)),
# #                 'output_table': schedule_data.get('output_table', 'sku_recommendations'),
# #                 'is_active': schedule_data.get('is_active', True),
# #                 'created_by': schedule_data.get('created_by', 'user'),
# #                 # New parameters for data filtering and mining control
# #                 'days_back': int(schedule_data.get('days_back', 365)),
# #                 'max_items': int(schedule_data.get('max_items', 200)),
# #                 'min_item_frequency': int(schedule_data.get('min_item_frequency', 5)),
# #                 'use_enhanced_mining': bool(schedule_data.get('use_enhanced_mining', True)),
# #                 'time_weighting_method': schedule_data.get('time_weighting_method', 'exponential_decay'),
# #                 'time_segmentation': schedule_data.get('time_segmentation', 'weekly')
# #             }
            
# #             # Calculate next run time
# #             next_run = self._calculate_next_run_time(
# #                 schedule_params['schedule_type'], 
# #                 schedule_params['schedule_time'],
# #                 schedule_params.get('schedule_day_of_week')
# #             )
# #             schedule_params['next_run_at'] = next_run
            
# #             # Insert into database with all parameters
# #             insert_query = """
# #                 INSERT INTO mining_schedules (
# #                     job_name, job_description, schedule_type, schedule_time, 
# #                     schedule_day_of_week, min_support, min_confidence, min_lift,
# #                     max_recommendations, decay_rate, output_table, is_active,
# #                     created_by, next_run_at, days_back, max_items, min_item_frequency,
# #                     use_enhanced_mining, time_weighting_method, time_segmentation
# #                 ) VALUES (
# #                     %(job_name)s, %(job_description)s, %(schedule_type)s, %(schedule_time)s,
# #                     %(schedule_day_of_week)s, %(min_support)s, %(min_confidence)s, %(min_lift)s,
# #                     %(max_recommendations)s, %(decay_rate)s, %(output_table)s, %(is_active)s,
# #                     %(created_by)s, %(next_run_at)s, %(days_back)s, %(max_items)s, %(min_item_frequency)s,
# #                     %(use_enhanced_mining)s, %(time_weighting_method)s, %(time_segmentation)s
# #                 )
# #             """
            
# #             self.db_connection.cursor.execute(insert_query, schedule_params)
# #             schedule_id = self.db_connection.cursor.lastrowid
# #             self.db_connection.connection.commit()
            
# #             # Initialize stats record
# #             stats_query = """
# #                 INSERT INTO mining_schedule_stats (schedule_id) 
# #                 VALUES (%s)
# #             """
# #             self.db_connection.cursor.execute(stats_query, (schedule_id,))
# #             self.db_connection.connection.commit()
            
# #             # Add job to scheduler if active
# #             if schedule_params['is_active']:
# #                 self._add_job_to_scheduler(schedule_id, schedule_params)
            
# #             logger.info(f"✓ Created schedule '{schedule_params['job_name']}' with ID {schedule_id}")
            
# #             return {
# #                 'schedule_id': schedule_id,
# #                 'job_name': schedule_params['job_name'],
# #                 'next_run_at': next_run.isoformat() if next_run else None,
# #                 'status': 'created'
# #             }
            
# #         except Exception as e:
# #             logger.error(f"Failed to create schedule: {str(e)}")
# #             if self.db_connection.connection:
# #                 self.db_connection.connection.rollback()
# #             raise
# #         finally:
# #             self.db_connection.disconnect()
    
# #     def get_schedules(self):
# #         """Get all schedules from database"""
# #         try:
# #             # Use the existing db_connection attribute
# #             self.db_connection.connect()
            
# #             query = """
# #             SELECT 
# #                 s.id,
# #                 s.job_name,
# #                 s.job_description,
# #                 s.schedule_type,
# #                 s.schedule_time,
# #                 s.schedule_day_of_week,
# #                 s.is_active,
# #                 s.next_run_at,
# #                 s.last_run_at,
# #                 s.created_at,
# #                 s.updated_at,
# #                 s.created_by,
# #                 s.min_support,
# #                 s.min_confidence,
# #                 s.min_lift,
# #                 s.max_recommendations,
# #                 s.decay_rate,
# #                 s.output_table,
# #                 s.days_back,
# #                 s.max_items,
# #                 s.min_item_frequency,
# #                 s.use_enhanced_mining,
# #                 s.time_weighting_method,
# #                 s.time_segmentation,
# #                 st.total_executions,
# #                 st.successful_executions,
# #                 st.failed_executions,
# #                 st.avg_execution_time_seconds,
# #                 st.total_rules_generated
# #             FROM mining_schedules s
# #             LEFT JOIN mining_schedule_stats st ON s.id = st.schedule_id
# #             ORDER BY s.created_at DESC
# #             """
            
# #             self.db_connection.cursor.execute(query)
# #             schedules = self.db_connection.cursor.fetchall()
            
# #             # Helper function to safely convert datetime/time/timedelta to string
# #             def safe_isoformat(dt):
# #                 if dt is None:
# #                     return None
# #                 if isinstance(dt, str):
# #                     return dt  # Already a string
# #                 if isinstance(dt, timedelta):
# #                     return str(dt)  # Convert timedelta to string
# #                 if hasattr(dt, 'isoformat'):
# #                     return dt.isoformat()  # datetime, date, or time objects
# #                 return str(dt)  # Fallback to string conversion
            
# #             result = []
# #             for schedule in schedules:
# #                 stats = None
# #                 # Build stats dict if any stat fields are present (now only 5 stats columns)
# #                 if schedule[24] is not None or schedule[25] is not None:  # total_executions or successful_executions
# #                     stats = {
# #                         'total_executions': schedule[24],
# #                         'successful_executions': schedule[25],
# #                         'failed_executions': schedule[26],
# #                         'average_execution_time': float(schedule[27]) if schedule[27] else None,
# #                         'total_rules_generated': schedule[28]
# #                     }
                
# #                 result.append({
# #                     'id': schedule[0],
# #                     'job_name': schedule[1],
# #                     'job_description': schedule[2],
# #                     'schedule_type': schedule[3],
# #                     'schedule_time': safe_isoformat(schedule[4]),
# #                     'schedule_day_of_week': schedule[5],
# #                     'is_active': bool(schedule[6]),
# #                     'next_run_at': safe_isoformat(schedule[7]),
# #                     'last_run_at': safe_isoformat(schedule[8]),
# #                     'created_at': safe_isoformat(schedule[9]),
# #                     'updated_at': safe_isoformat(schedule[10]),
# #                     'created_by': schedule[11] if schedule[11] else 'system',
# #                     'min_support': float(schedule[12]) if schedule[12] else None,
# #                     'min_confidence': float(schedule[13]) if schedule[13] else None,
# #                     'min_lift': float(schedule[14]) if schedule[14] else None,
# #                     'max_recommendations': int(schedule[15]) if schedule[15] else None,
# #                     'decay_rate': float(schedule[16]) if schedule[16] else None,
# #                     'output_table': schedule[17],
# #                     'days_back': schedule[18],
# #                     'max_items': schedule[19],
# #                     'min_item_frequency': schedule[20],
# #                     'use_enhanced_mining': bool(schedule[21]) if schedule[21] is not None else True,
# #                     'time_weighting_method': schedule[22],
# #                     'time_segmentation': schedule[23],
# #                     'stats': stats
# #                 })
            
# #             return result
            
# #         except Exception as e:
# #             logger.error(f"Failed to get schedules: {str(e)}")
# #             raise    
# #     def update_schedule(self, schedule_id: int, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
# #         """Update an existing schedule"""
# #         try:
# #             self.db_connection.connect()
            
# #             # Remove job from scheduler first
# #             job_id = f"mining_job_{schedule_id}"
# #             if self.scheduler.get_job(job_id):
# #                 self.scheduler.remove_job(job_id)
            
# #             # Build update query dynamically
# #             update_fields = []
# #             update_values = {}
            
# #             allowed_fields = [
# #                 'job_name', 'job_description', 'schedule_type', 'schedule_time',
# #                 'schedule_day_of_week', 'min_support', 'min_confidence', 'min_lift',
# #                 'max_recommendations', 'decay_rate', 'output_table', 'is_active'
# #             ]
            
# #             for field in allowed_fields:
# #                 if field in schedule_data:
# #                     update_fields.append(f"{field} = %({field})s")
# #                     update_values[field] = schedule_data[field]
            
# #             if not update_fields:
# #                 raise ValueError("No valid fields to update")
            
# #             # Calculate new next_run_at if schedule details changed
# #             if any(field in schedule_data for field in ['schedule_type', 'schedule_time', 'schedule_day_of_week']):
# #                 # Get current schedule info
# #                 self.db_connection.cursor.execute("SELECT schedule_type, schedule_time, schedule_day_of_week FROM mining_schedules WHERE id = %s", (schedule_id,))
# #                 current = self.db_connection.cursor.fetchone()
                
# #                 schedule_type = schedule_data.get('schedule_type', current[0])
# #                 schedule_time = schedule_data.get('schedule_time', str(current[1]))
# #                 schedule_day_of_week = schedule_data.get('schedule_day_of_week', current[2])
                
# #                 next_run = self._calculate_next_run_time(schedule_type, schedule_time, schedule_day_of_week)
# #                 update_fields.append("next_run_at = %(next_run_at)s")
# #                 update_values['next_run_at'] = next_run
            
# #             update_query = f"""
# #                 UPDATE mining_schedules 
# #                 SET {', '.join(update_fields)}
# #                 WHERE id = %(schedule_id)s
# #             """
# #             update_values['schedule_id'] = schedule_id
            
# #             self.db_connection.cursor.execute(update_query, update_values)
# #             self.db_connection.connection.commit()
            
# #             # Add job back to scheduler if active
# #             if schedule_data.get('is_active', True):
# #                 # Get updated schedule info
# #                 self.db_connection.cursor.execute("SELECT * FROM mining_schedules WHERE id = %s", (schedule_id,))
# #                 schedule_row = self.db_connection.cursor.fetchone()
# #                 if schedule_row:
# #                     schedule_params = self._row_to_schedule_dict(schedule_row)
# #                     self._add_job_to_scheduler(schedule_id, schedule_params)
            
# #             logger.info(f"✓ Updated schedule ID {schedule_id}")
            
# #             return {'schedule_id': schedule_id, 'status': 'updated'}
            
# #         except Exception as e:
# #             logger.error(f"Failed to update schedule: {str(e)}")
# #             if self.db_connection.connection:
# #                 self.db_connection.connection.rollback()
# #             raise
# #         finally:
# #             self.db_connection.disconnect()
    
# #     def delete_schedule(self, schedule_id: int) -> Dict[str, Any]:
# #         """Delete a schedule"""
# #         try:
# #             # Remove job from scheduler
# #             job_id = f"mining_job_{schedule_id}"
# #             if self.scheduler.get_job(job_id):
# #                 self.scheduler.remove_job(job_id)
            
# #             # Delete from database (cascade will handle related records)
# #             self.db_connection.connect()
# #             self.db_connection.cursor.execute("DELETE FROM mining_schedules WHERE id = %s", (schedule_id,))
# #             self.db_connection.connection.commit()
            
# #             logger.info(f"✓ Deleted schedule ID {schedule_id}")
            
# #             return {'schedule_id': schedule_id, 'status': 'deleted'}
            
# #         except Exception as e:
# #             logger.error(f"Failed to delete schedule: {str(e)}")
# #             if self.db_connection.connection:
# #                 self.db_connection.connection.rollback()
# #             raise
# #         finally:
# #             self.db_connection.disconnect()
    
# #     def delete_all_schedules(self) -> Dict[str, Any]:
# #         """Delete all schedules and related data"""
# #         try:
# #             self.db_connection.connect()
            
# #             # Get counts before deletion - fetchone returns tuple, not dict
# #             self.db_connection.cursor.execute("SELECT COUNT(*) FROM mining_schedules")
# #             result = self.db_connection.cursor.fetchone()
# #             schedule_count = result[0] if result else 0
            
# #             self.db_connection.cursor.execute("SELECT COUNT(*) FROM mining_job_logs")
# #             result = self.db_connection.cursor.fetchone()
# #             log_count = result[0] if result else 0
            
# #             self.db_connection.cursor.execute("SELECT COUNT(*) FROM mining_schedule_stats")
# #             result = self.db_connection.cursor.fetchone()
# #             stats_count = result[0] if result else 0
            
# #             # Remove all jobs from scheduler
# #             self.scheduler.remove_all_jobs()
            
# #             # Delete all schedules (cascade will handle logs and stats)
# #             self.db_connection.cursor.execute("DELETE FROM mining_schedules")
# #             self.db_connection.connection.commit()
            
# #             logger.info(f"✓ Deleted all schedules: {schedule_count} schedules, {log_count} logs, {stats_count} stats")
            
# #             return {
# #                 'deleted_schedules': schedule_count,
# #                 'deleted_logs': log_count,
# #                 'deleted_stats': stats_count,
# #                 'status': 'all_deleted'
# #             }
            
# #         except Exception as e:
# #             logger.error(f"Failed to delete all schedules: {str(e)}")
# #             if self.db_connection.connection:
# #                 self.db_connection.connection.rollback()
# #             raise
# #         finally:
# #             self.db_connection.disconnect()
    
# #     def execute_mining_job(self, schedule_id: int):
# #         """Execute a mining job for a schedule - runs in background thread"""
# #         logger.info(f"🎯 Scheduling mining job for schedule {schedule_id} in background thread")
        
# #         # Run the actual mining in a separate thread to avoid blocking the API
# #         thread = threading.Thread(
# #             target=self._execute_mining_job_async,
# #             args=(schedule_id,),
# #             daemon=True,
# #             name=f"MiningJob-{schedule_id}"
# #         )
# #         thread.start()
# #         logger.info(f"✅ Mining job thread started for schedule {schedule_id}")
    
# #     def _execute_mining_job_async(self, schedule_id: int):
# #         """Internal method that runs the actual mining job asynchronously
        
# #         This method now uses the shared run_mining_task() function from the API endpoints
# #         to ensure scheduler and manual mining use the exact same logic and parameters.
# #         """
# #         start_time = datetime.now()
# #         log_id = None
        
# #         # Create a separate database connection for this background thread
# #         thread_db_connection = None
        
# #         try:
# #             # Initialize separate database connection for this thread
# #             from app.shared.database.connection import DatabaseConnection
# #             thread_db_connection = DatabaseConnection(self.db_config)
# #             thread_db_connection.connect()
            
# #             # Get schedule details
# #             thread_db_connection.cursor.execute("SELECT * FROM mining_schedules WHERE id = %s", (schedule_id,))
# #             schedule_row = thread_db_connection.cursor.fetchone()
            
# #             if not schedule_row:
# #                 raise ValueError(f"Schedule {schedule_id} not found")
            
# #             schedule = self._row_to_schedule_dict(schedule_row)
            
# #             # Create job log entry
# #             log_query = """
# #                 INSERT INTO mining_job_logs (
# #                     schedule_id, job_name, execution_parameters, started_at
# #                 ) VALUES (%s, %s, %s, %s)
# #             """
# #             execution_params = {
# #                 'min_support': schedule['min_support'],
# #                 'min_confidence': schedule['min_confidence'],
# #                 'min_lift': schedule['min_lift'],
# #                 'max_recommendations': schedule['max_recommendations'],
# #                 'decay_rate': schedule['decay_rate'],
# #                 'days_back': schedule.get('days_back', 365),
# #                 'use_enhanced_mining': schedule.get('use_enhanced_mining', True),
# #                 'time_weighting_method': schedule.get('time_weighting_method', 'exponential_decay'),
# #                 'time_segmentation': schedule.get('time_segmentation', 'weekly')
# #             }
            
# #             thread_db_connection.cursor.execute(log_query, (
# #                 schedule_id, 
# #                 schedule['job_name'],
# #                 json.dumps(execution_params),
# #                 start_time
# #             ))
# #             log_id = thread_db_connection.cursor.lastrowid
# #             thread_db_connection.connection.commit()
            
# #             logger.info(f"🚀 Starting mining job for schedule '{schedule['job_name']}' (ID: {schedule_id})")
# #             logger.info(f"🎯 Using parameters: {execution_params}")
            
# #             # Import the shared mining task function
# #             from app.modules.association_mining.api.endpoints import run_mining_task
            
# #             # Create custom config with output_table from schedule
# #             custom_db_config = {
# #                 'recommendations_table': schedule.get('output_table', 'sku_recommendations')
# #             }
# #             if self.db_config:
# #                 custom_db_config.update(self.db_config)
            
# #             # Create a minimal task manager for scheduler jobs
# #             class SchedulerTaskManager:
# #                 """Minimal task manager for scheduler jobs that logs to mining_job_logs"""
# #                 def __init__(self, log_id, db_connection):
# #                     self.log_id = log_id
# #                     self.db_connection = db_connection
                
# #                 def start_task(self, task_id, message):
# #                     logger.info(f"📋 {message}")
                
# #                 def update_progress(self, task_id, progress, message):
# #                     logger.info(f"⏳ Progress {int(progress*100)}%: {message}")
                
# #                 def complete_task(self, task_id, result=None, message=""):
# #                     logger.info(f"✅ {message}")
# #                     self.result = result
                
# #                 def fail_task(self, task_id, error_msg):
# #                     logger.error(f"❌ {error_msg}")
# #                     self.error = error_msg
            
# #             # Create task manager for this job
# #             task_manager = SchedulerTaskManager(log_id, thread_db_connection)
            
# #             # Temporarily replace the global task_manager
# #             import app.modules.association_mining.api.endpoints as endpoints_module
# #             original_task_manager = endpoints_module.task_manager
# #             endpoints_module.task_manager = task_manager
            
# #             try:
# #                 # Call the shared mining function directly
# #                 # Note: This is already running in a background thread from APScheduler,
# #                 # so no need for additional threading wrapper
# #                 logger.info(f"🚀 Calling run_mining_task directly (already in APScheduler thread)")
                
# #                 run_mining_task(
# #                     task_id=f"scheduled_{schedule_id}_{int(start_time.timestamp())}",
# #                     days_back=schedule.get('days_back', 365),
# #                     min_support=schedule['min_support'],
# #                     min_confidence=schedule['min_confidence'],
# #                     min_lift=schedule['min_lift'],
# #                     max_recommendations=schedule['max_recommendations'],
# #                     decay_rate=schedule['decay_rate'],
# #                     use_enhanced_mining=schedule.get('use_enhanced_mining', True),
# #                     time_weighting_method=schedule.get('time_weighting_method', 'exponential_decay'),
# #                     time_segmentation=schedule.get('time_segmentation', 'weekly'),
# #                     db_config=custom_db_config
# #                 )
                
# #                 # Get results from task manager
# #                 if hasattr(task_manager, 'result') and task_manager.result:
# #                     results = task_manager.result
# #                     rules_count = results.get('recommendations_count', 0)
# #                     records_processed = results.get('stats', {}).get('total_orders', 0)
# #                 else:
# #                     # If no result set, assume success with 0 rules
# #                     rules_count = 0
# #                     records_processed = 0
                
# #             finally:
# #                 # Restore original task_manager
# #                 endpoints_module.task_manager = original_task_manager
            
# #             # Calculate execution time
# #             end_time = datetime.now()
# #             execution_time = int((end_time - start_time).total_seconds())
            
# #             # Update job log with success
# #             update_log_query = """
# #                 UPDATE mining_job_logs 
# #                 SET completed_at = %s, execution_status = 'success', 
# #                     rules_generated = %s, execution_time_seconds = %s,
# #                     records_processed = %s
# #                 WHERE id = %s
# #             """
            
# #             thread_db_connection.cursor.execute(update_log_query, (
# #                 end_time, rules_count, execution_time, records_processed, log_id
# #             ))
            
# #             # Update schedule last_run_at and next_run_at
# #             next_run = self._calculate_next_run_time(
# #                 schedule['schedule_type'],
# #                 schedule['schedule_time'],
# #                 schedule.get('schedule_day_of_week')
# #             )
            
# #             schedule_update_query = """
# #                 UPDATE mining_schedules 
# #                 SET last_run_at = %s, next_run_at = %s 
# #                 WHERE id = %s
# #             """
# #             thread_db_connection.cursor.execute(schedule_update_query, (end_time, next_run, schedule_id))
            
# #             # Update statistics using thread connection
# #             self._update_schedule_stats_with_connection(thread_db_connection, schedule_id, True, execution_time, rules_count)
            
# #             thread_db_connection.connection.commit()
            
# #             logger.info(f"✅ Mining job completed successfully for schedule '{schedule['job_name']}' - Generated {rules_count} rules in {execution_time}s")
            
# #         except Exception as e:
# #             end_time = datetime.now()
# #             execution_time = int((end_time - start_time).total_seconds())
            
# #             logger.error(f"❌ Mining job failed for schedule {schedule_id}: {str(e)}")
            
# #             # Update job log with failure
# #             if log_id and thread_db_connection:
# #                 try:
# #                     update_log_query = """
# #                         UPDATE mining_job_logs 
# #                         SET completed_at = %s, execution_status = 'failed',
# #                             execution_time_seconds = %s, error_message = %s
# #                         WHERE id = %s
# #                     """
# #                     thread_db_connection.cursor.execute(update_log_query, (
# #                         end_time, execution_time, str(e), log_id
# #                     ))
                    
# #                     # Update statistics using thread connection
# #                     self._update_schedule_stats_with_connection(thread_db_connection, schedule_id, False, execution_time, 0)
                    
# #                     thread_db_connection.connection.commit()
# #                 except Exception as log_error:
# #                     logger.error(f"Failed to update job log: {str(log_error)}")
            
# #         finally:
# #             # Clean up the thread-specific database connection
# #             if thread_db_connection:
# #                 try:
# #                     thread_db_connection.disconnect()
# #                 except Exception as disconnect_error:
# #                     logger.error(f"Error disconnecting thread database connection: {str(disconnect_error)}")
    
# #     def _load_schedules_from_database(self):
# #         """Load existing active schedules from database and add to scheduler"""
# #         try:
# #             schedules = self.get_schedules()
# #             for schedule in schedules:
# #                 if schedule['is_active']:
# #                     self._add_job_to_scheduler(schedule['id'], schedule)
            
# #             logger.info(f"✓ Loaded {len([s for s in schedules if s['is_active']])} active schedules")
            
# #         except Exception as e:
# #             logger.error(f"Failed to load schedules from database: {str(e)}")
    
# #     def _add_job_to_scheduler(self, schedule_id: int, schedule_params: Dict[str, Any]):
# #         """Add a job to the APScheduler"""
# #         try:
# #             job_id = f"mining_job_{schedule_id}"
            
# #             # Remove existing job if it exists
# #             if self.scheduler.get_job(job_id):
# #                 self.scheduler.remove_job(job_id)
            
# #             # Parse time
# #             time_parts = schedule_params['schedule_time'].split(':')
# #             hour = int(time_parts[0])
# #             minute = int(time_parts[1])
            
# #             # Create trigger based on schedule type
# #             if schedule_params['schedule_type'] == 'daily':
# #                 trigger = CronTrigger(hour=hour, minute=minute)
# #             elif schedule_params['schedule_type'] == 'weekly':
# #                 day_of_week = schedule_params.get('schedule_day_of_week', 0)
# #                 trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
# #             else:
# #                 raise ValueError(f"Unsupported schedule type: {schedule_params['schedule_type']}")
            
# #             # Add job to scheduler
# #             self.scheduler.add_job(
# #                 func=self.execute_mining_job,
# #                 trigger=trigger,
# #                 args=[schedule_id],
# #                 id=job_id,
# #                 name=f"Mining: {schedule_params['job_name']}",
# #                 replace_existing=True
# #             )
            
# #             logger.info(f"✓ Added job '{schedule_params['job_name']}' to scheduler")
            
# #         except Exception as e:
# #             logger.error(f"Failed to add job to scheduler: {str(e)}")
# #             raise
    
# #     def _calculate_next_run_time(self, schedule_type: str, schedule_time: str, day_of_week: Optional[int] = None) -> datetime:
# #         """Calculate the next run time for a schedule"""
# #         now = datetime.now()
# #         time_parts = schedule_time.split(':')
# #         hour = int(time_parts[0])
# #         minute = int(time_parts[1])
        
# #         if schedule_type == 'daily':
# #             next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
# #             if next_run <= now:
# #                 next_run += timedelta(days=1)
# #         elif schedule_type == 'weekly':
# #             if day_of_week is None:
# #                 day_of_week = 0  # Default to Monday
            
# #             days_ahead = day_of_week - now.weekday()
# #             if days_ahead <= 0:  # Target day already happened this week
# #                 days_ahead += 7
            
# #             next_run = (now + timedelta(days=days_ahead)).replace(
# #                 hour=hour, minute=minute, second=0, microsecond=0
# #             )
# #         else:
# #             raise ValueError(f"Unsupported schedule type: {schedule_type}")
        
# #         return next_run
    
# #     def _update_schedule_stats(self, schedule_id: int, success: bool, execution_time: int, rules_generated: int):
# #         """Update schedule statistics using the main database connection"""
# #         self._update_schedule_stats_with_connection(self.db_connection, schedule_id, success, execution_time, rules_generated)

# #     def _update_schedule_stats_with_connection(self, db_conn, schedule_id: int, success: bool, execution_time: int, rules_generated: int):
# #         """Update schedule statistics with a specific database connection"""
# #         try:
# #             if success:
# #                 stats_query = """
# #                     UPDATE mining_schedule_stats 
# #                     SET total_executions = total_executions + 1,
# #                         successful_executions = successful_executions + 1,
# #                         last_success_at = NOW(),
# #                         avg_execution_time_seconds = (
# #                             (avg_execution_time_seconds * successful_executions + %s) / (successful_executions + 1)
# #                         ),
# #                         total_rules_generated = total_rules_generated + %s
# #                     WHERE schedule_id = %s
# #                 """
# #                 db_conn.cursor.execute(stats_query, (execution_time, rules_generated, schedule_id))
# #             else:
# #                 stats_query = """
# #                     UPDATE mining_schedule_stats 
# #                     SET total_executions = total_executions + 1,
# #                         failed_executions = failed_executions + 1,
# #                         last_failure_at = NOW()
# #                     WHERE schedule_id = %s
# #                 """
# #                 db_conn.cursor.execute(stats_query, (schedule_id,))
            
# #         except Exception as e:
# #             logger.error(f"Failed to update schedule stats: {str(e)}")
    
# #     def _row_to_schedule_dict(self, row) -> Dict[str, Any]:
# #         """Convert database row to schedule dictionary"""
# #         return {
# #             'id': row[0],
# #             'job_name': row[1],
# #             'job_description': row[2],
# #             'schedule_type': row[3],
# #             'schedule_time': str(row[4]),
# #             'schedule_day_of_week': row[5],
# #             'min_support': float(row[6]),
# #             'min_confidence': float(row[7]),
# #             'min_lift': float(row[8]),
# #             'max_recommendations': row[9],
# #             'decay_rate': float(row[10]),
# #             'output_table': row[11],
# #             'is_active': bool(row[12]),
# #             'created_at': row[13],
# #             'updated_at': row[14],
# #             'last_run_at': row[15],
# #             'next_run_at': row[16],
# #             'created_by': row[17]
# #         }
    
# #     def get_job_logs(self, schedule_id: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
# #         """Get job execution logs"""
# #         try:
# #             self.db_connection.connect()
            
# #             if schedule_id:
# #                 query = """
# #                     SELECT * FROM mining_job_logs 
# #                     WHERE schedule_id = %s 
# #                     ORDER BY started_at DESC 
# #                     LIMIT %s
# #                 """
# #                 self.db_connection.cursor.execute(query, (schedule_id, limit))
# #             else:
# #                 query = """
# #                     SELECT * FROM mining_job_logs 
# #                     ORDER BY started_at DESC 
# #                     LIMIT %s
# #                 """
# #                 self.db_connection.cursor.execute(query, (limit,))
            
# #             results = self.db_connection.cursor.fetchall()
            
# #             logs = []
# #             for row in results:
# #                 log = {
# #                     'id': row[0],
# #                     'schedule_id': row[1],
# #                     'job_name': row[2],
# #                     'started_at': row[3].isoformat() if row[3] else None,
# #                     'completed_at': row[4].isoformat() if row[4] else None,
# #                     'execution_status': row[5],
# #                     'rules_generated': row[6],
# #                     'records_processed': row[7],
# #                     'execution_time_seconds': row[8],
# #                     'error_message': row[9],
# #                     'error_details': json.loads(row[10]) if row[10] else None,
# #                     'execution_parameters': json.loads(row[11]) if row[11] else None
# #                 }
# #                 logs.append(log)
            
# #             return logs
            
# #         except Exception as e:
# #             logger.error(f"Failed to get job logs: {str(e)}")
# #             raise
# #         finally:
# #             self.db_connection.disconnect()

# # # Global scheduler instance
# # scheduler_service = None

# # def get_scheduler_service(db_config=None) -> SchedulerService:
# #     """Get or create the global scheduler service instance"""
# #     global scheduler_service
# #     if scheduler_service is None:
# #         scheduler_service = SchedulerService(db_config)
# #     return scheduler_service

# import json
# import logging
# from datetime import datetime, timedelta
# from typing import List, Dict, Optional, Any

# from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.triggers.cron import CronTrigger
# from apscheduler.jobstores.memory import MemoryJobStore
# from apscheduler.executors.pool import ThreadPoolExecutor

# from app.shared.database.connection import DatabaseConnection

# logger = logging.getLogger(__name__)


# class SchedulerService:
#     def __init__(self, db_config=None):
#         self.db_config = db_config
#         self.db_connection = DatabaseConnection(db_config)

#         jobstores = {'default': MemoryJobStore()}
#         executors = {'default': ThreadPoolExecutor(10)}
#         job_defaults = {
#             'coalesce': False,
#             'max_instances': 1,
#             'misfire_grace_time': 300
#         }

#         self.scheduler = BackgroundScheduler(
#             jobstores=jobstores,
#             executors=executors,
#             job_defaults=job_defaults,
#             timezone='UTC'
#         )

#         self.is_running = False

#     # --------------------------------------------------
#     # Scheduler lifecycle
#     # --------------------------------------------------
#     def start(self):
#         if not self.is_running:
#             self.scheduler.start()
#             self.is_running = True
#             logger.info("✓ Scheduler started")
#             self._load_schedules_from_database()

#     def stop(self):
#         if self.is_running:
#             self.scheduler.shutdown(wait=False)
#             self.is_running = False
#             logger.info("✓ Scheduler stopped")

#     # --------------------------------------------------
#     # APScheduler job entry (FIXED)
#     # --------------------------------------------------
#     def execute_mining_job(self, schedule_id: int):
#         """
#         APScheduler already runs this in a worker thread.
#         DO NOT create additional threads here.
#         """
#         logger.info(f"🎯 Executing mining job (schedule_id={schedule_id})")
#         self._execute_mining_job_async(schedule_id)

#     # --------------------------------------------------
#     # Actual mining execution
#     # --------------------------------------------------
#     def _execute_mining_job_async(self, schedule_id: int):
#         start_time = datetime.utcnow()
#         log_id = None
#         db = DatabaseConnection(self.db_config)

#         try:
#             db.connect()

#             db.cursor.execute(
#                 "SELECT * FROM mining_schedules WHERE id = %s",
#                 (schedule_id,)
#             )
#             row = db.cursor.fetchone()
#             if not row:
#                 raise ValueError(f"Schedule {schedule_id} not found")

#             schedule = self._row_to_schedule_dict(row)

#             # Create log
#             db.cursor.execute("""
#                 INSERT INTO mining_job_logs
#                 (schedule_id, job_name, execution_parameters, started_at)
#                 VALUES (%s, %s, %s, %s)
#             """, (
#                 schedule_id,
#                 schedule['job_name'],
#                 json.dumps(schedule),
#                 start_time
#             ))
#             log_id = db.cursor.lastrowid
#             db.connection.commit()

#             logger.info(f"🚀 Mining started: {schedule['job_name']}")

#             from app.modules.association_mining.api.endpoints import run_mining_task
#             import app.modules.association_mining.api.endpoints as endpoints_module

#             class SchedulerTaskManager:
#                 def __init__(self):
#                     self.result = None
#                     self.error = None

#                 def start_task(self, *_): pass
#                 def update_progress(self, *_): pass
#                 def complete_task(self, _, result=None, __=""):
#                     self.result = result
#                 def fail_task(self, _, error_msg):
#                     self.error = error_msg

#             task_manager = SchedulerTaskManager()
#             original_task_manager = endpoints_module.task_manager
#             endpoints_module.task_manager = task_manager

#             try:
#                 run_mining_task(
#                     task_id=f"scheduled_{schedule_id}_{int(start_time.timestamp())}",
#                     days_back=schedule.get('days_back', 365),
#                     min_support=schedule['min_support'],
#                     min_confidence=schedule['min_confidence'],
#                     min_lift=schedule['min_lift'],
#                     max_recommendations=schedule['max_recommendations'],
#                     decay_rate=schedule['decay_rate'],
#                     use_enhanced_mining=schedule.get('use_enhanced_mining', True),
#                     time_weighting_method=schedule.get('time_weighting_method', 'exponential_decay'),
#                     time_segmentation=schedule.get('time_segmentation', 'weekly'),
#                     db_config={'recommendations_table': schedule['output_table']}
#                 )
#             finally:
#                 endpoints_module.task_manager = original_task_manager

#             end_time = datetime.utcnow()
#             duration = int((end_time - start_time).total_seconds())

#             rules = 0
#             if task_manager.result:
#                 rules = task_manager.result.get('recommendations_count', 0)

#             db.cursor.execute("""
#                 UPDATE mining_job_logs
#                 SET completed_at=%s,
#                     execution_status='success',
#                     rules_generated=%s,
#                     execution_time_seconds=%s
#                 WHERE id=%s
#             """, (end_time, rules, duration, log_id))

#             self._update_schedule_stats_with_connection(
#                 db, schedule_id, True, duration, rules
#             )

#             db.connection.commit()
#             logger.info(f"✅ Mining completed: {schedule['job_name']} ({rules} rules)")

#         except Exception as e:
#             logger.error(f"❌ Mining failed (schedule_id={schedule_id}): {e}")
#             if log_id:
#                 db.cursor.execute("""
#                     UPDATE mining_job_logs
#                     SET completed_at=%s,
#                         execution_status='failed',
#                         error_message=%s
#                     WHERE id=%s
#                 """, (datetime.utcnow(), str(e), log_id))
#                 self._update_schedule_stats_with_connection(
#                     db, schedule_id, False, 0, 0
#                 )
#                 db.connection.commit()

#         finally:
#             db.disconnect()

#     # --------------------------------------------------
#     # Scheduler helpers
#     # --------------------------------------------------
#     def _add_job_to_scheduler(self, schedule_id: int, schedule: Dict[str, Any]):
#         job_id = f"mining_job_{schedule_id}"

#         if self.scheduler.get_job(job_id):
#             self.scheduler.remove_job(job_id)

#         hour, minute = map(int, schedule['schedule_time'].split(':'))

#         if schedule['schedule_type'] == 'daily':
#             trigger = CronTrigger(hour=hour, minute=minute)
#         else:
#             trigger = CronTrigger(
#                 day_of_week=schedule.get('schedule_day_of_week', 0),
#                 hour=hour,
#                 minute=minute
#             )

#         self.scheduler.add_job(
#             func=self.execute_mining_job,
#             trigger=trigger,
#             args=[schedule_id],
#             id=job_id,
#             replace_existing=True
#         )

#     def _load_schedules_from_database(self):
#         schedules = self.get_schedules()
#         for s in schedules:
#             if s['is_active']:
#                 self._add_job_to_scheduler(s['id'], s)

#     # --------------------------------------------------
#     # Utils
#     # --------------------------------------------------
#     def _calculate_next_run_time(self, schedule_type, schedule_time, day_of_week=None):
#         now = datetime.utcnow()
#         hour, minute = map(int, schedule_time.split(':'))

#         if schedule_type == 'daily':
#             run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
#             return run + timedelta(days=1) if run <= now else run

#         days = (day_of_week - now.weekday()) % 7 or 7
#         return (now + timedelta(days=days)).replace(
#             hour=hour, minute=minute, second=0, microsecond=0
#         )

#     def _update_schedule_stats_with_connection(self, db, schedule_id, success, time, rules):
#         if success:
#             db.cursor.execute("""
#                 UPDATE mining_schedule_stats
#                 SET total_executions=total_executions+1,
#                     successful_executions=successful_executions+1,
#                     avg_execution_time_seconds=
#                       (avg_execution_time_seconds*successful_executions + %s)
#                       /(successful_executions+1),
#                     total_rules_generated=total_rules_generated+%s
#                 WHERE schedule_id=%s
#             """, (time, rules, schedule_id))
#         else:
#             db.cursor.execute("""
#                 UPDATE mining_schedule_stats
#                 SET total_executions=total_executions+1,
#                     failed_executions=failed_executions+1
#                 WHERE schedule_id=%s
#             """, (schedule_id,))

#     def _row_to_schedule_dict(self, r):
#         return {
#             'id': r[0],
#             'job_name': r[1],
#             'schedule_type': r[3],
#             'schedule_time': str(r[4]),
#             'schedule_day_of_week': r[5],
#             'min_support': float(r[6]),
#             'min_confidence': float(r[7]),
#             'min_lift': float(r[8]),
#             'max_recommendations': r[9],
#             'decay_rate': float(r[10]),
#             'output_table': r[11],
#             'is_active': bool(r[12]),
#             'days_back': r[18],
#             'use_enhanced_mining': r[21],
#             'time_weighting_method': r[22],
#             'time_segmentation': r[23],
#         }

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore

from app.shared.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Production-safe APScheduler service.
    - No manual threading
    - max_instances=1 is respected
    - Safe with FastAPI + Uvicorn reload
    """

    def __init__(self, db_config=None):
        self.db_config = db_config

        jobstores = {"default": MemoryJobStore()}
        executors = {"default": ThreadPoolExecutor(max_workers=10)}
        job_defaults = {
            "coalesce": False,
            "max_instances": 1,
            "misfire_grace_time": 300,
        }

        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone="UTC",
        )

        self.is_running = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self):
        if self.is_running:
            return

        try:
            self.scheduler.start()
            self.is_running = True
            logger.info("✓ Scheduler started")

            self._load_schedules_from_database()
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
            self.is_running = False
            if self.scheduler.running:
                self.scheduler.shutdown(wait=False)
            raise

    def stop(self):
        if not self.is_running:
            return

        self.scheduler.shutdown(wait=False)
        self.is_running = False
        logger.info("✓ Scheduler stopped")

    # ------------------------------------------------------------------
    # Schedule CRUD operations
    # ------------------------------------------------------------------
    def get_schedules(self):
        """Get all schedules from database"""
        db = DatabaseConnection(self.db_config)
        try:
            db.connect()
            
            query = """
            SELECT 
                s.id, s.job_name, s.job_description, s.schedule_type, s.schedule_time,
                s.schedule_day_of_week, s.is_active, s.next_run_at, s.last_run_at,
                s.created_at, s.updated_at, s.created_by, s.min_support, s.min_confidence,
                s.min_lift, s.max_recommendations, s.decay_rate, s.output_table,
                s.days_back, s.max_items, s.min_item_frequency, s.use_enhanced_mining,
                s.time_weighting_method, s.time_segmentation,
                st.total_executions, st.successful_executions, st.failed_executions,
                st.avg_execution_time_seconds, st.total_rules_generated
            FROM mining_schedules s
            LEFT JOIN mining_schedule_stats st ON s.id = st.schedule_id
            ORDER BY s.created_at DESC
            """
            
            db.cursor.execute(query)
            schedules = db.cursor.fetchall()
            
            def safe_isoformat(dt):
                if dt is None:
                    return None
                if isinstance(dt, str):
                    return dt
                if isinstance(dt, timedelta):
                    return str(dt)
                if hasattr(dt, 'isoformat'):
                    return dt.isoformat()
                return str(dt)
            
            result = []
            for schedule in schedules:
                stats = None
                if schedule[24] is not None or schedule[25] is not None:
                    stats = {
                        'total_executions': schedule[24],
                        'successful_executions': schedule[25],
                        'failed_executions': schedule[26],
                        'average_execution_time': float(schedule[27]) if schedule[27] else None,
                        'total_rules_generated': schedule[28]
                    }
                
                result.append({
                    'id': schedule[0],
                    'job_name': schedule[1],
                    'job_description': schedule[2],
                    'schedule_type': schedule[3],
                    'schedule_time': safe_isoformat(schedule[4]),
                    'schedule_day_of_week': schedule[5],
                    'is_active': bool(schedule[6]),
                    'next_run_at': safe_isoformat(schedule[7]),
                    'last_run_at': safe_isoformat(schedule[8]),
                    'created_at': safe_isoformat(schedule[9]),
                    'updated_at': safe_isoformat(schedule[10]),
                    'created_by': schedule[11] if schedule[11] else 'system',
                    'min_support': float(schedule[12]) if schedule[12] else None,
                    'min_confidence': float(schedule[13]) if schedule[13] else None,
                    'min_lift': float(schedule[14]) if schedule[14] else None,
                    'max_recommendations': int(schedule[15]) if schedule[15] else None,
                    'decay_rate': float(schedule[16]) if schedule[16] else None,
                    'output_table': schedule[17],
                    'days_back': schedule[18],
                    'max_items': schedule[19],
                    'min_item_frequency': schedule[20],
                    'use_enhanced_mining': bool(schedule[21]) if schedule[21] is not None else True,
                    'time_weighting_method': schedule[22],
                    'time_segmentation': schedule[23],
                    'stats': stats
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get schedules: {str(e)}")
            raise
        finally:
            db.disconnect()

    def create_schedule(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new schedule"""
        db = DatabaseConnection(self.db_config)
        try:
            db.connect()
            
            # Calculate next run time
            next_run = self._calculate_next_run_time(
                schedule_data['schedule_type'],
                schedule_data['schedule_time'],
                schedule_data.get('schedule_day_of_week')
            )
            
            # Insert schedule
            insert_query = """
                INSERT INTO mining_schedules (
                    job_name, job_description, schedule_type, schedule_time, 
                    schedule_day_of_week, min_support, min_confidence, min_lift,
                    max_recommendations, decay_rate, output_table, is_active,
                    created_by, next_run_at, days_back, max_items, min_item_frequency,
                    use_enhanced_mining, time_weighting_method, time_segmentation
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            db.cursor.execute(insert_query, (
                schedule_data['job_name'],
                schedule_data['job_description'],
                schedule_data['schedule_type'],
                schedule_data['schedule_time'],
                schedule_data.get('schedule_day_of_week'),
                schedule_data['min_support'],
                schedule_data['min_confidence'],
                schedule_data['min_lift'],
                schedule_data['max_recommendations'],
                schedule_data['decay_rate'],
                schedule_data['output_table'],
                schedule_data.get('is_active', True),
                schedule_data.get('created_by', 'system'),
                next_run,
                schedule_data.get('days_back', 365),
                schedule_data.get('max_items', 200),
                schedule_data.get('min_item_frequency', 5),
                schedule_data.get('use_enhanced_mining', True),
                schedule_data.get('time_weighting_method', 'exponential_decay'),
                schedule_data.get('time_segmentation', 'weekly')
            ))
            
            schedule_id = db.cursor.lastrowid
            
            # Initialize stats
            db.cursor.execute(
                "INSERT INTO mining_schedule_stats (schedule_id) VALUES (%s)",
                (schedule_id,)
            )
            
            db.connection.commit()
            
            # Add to scheduler if active
            if schedule_data.get('is_active', True):
                self._add_job_to_scheduler(schedule_id, schedule_data)
            
            logger.info(f"✓ Created schedule '{schedule_data['job_name']}' with ID {schedule_id}")
            
            return {
                'schedule_id': schedule_id,
                'job_name': schedule_data['job_name'],
                'next_run_at': next_run.isoformat() if next_run else None,
                'status': 'created'
            }
            
        except Exception as e:
            logger.error(f"Failed to create schedule: {str(e)}")
            if db.connection:
                db.connection.rollback()
            raise
        finally:
            db.disconnect()

    def update_schedule(self, schedule_id: int, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing schedule"""
        db = DatabaseConnection(self.db_config)
        try:
            db.connect()
            
            # Remove job from scheduler first
            job_id = f"mining_job_{schedule_id}"
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # Build update query
            update_fields = []
            values = []
            
            for field in ['job_name', 'job_description', 'schedule_type', 'schedule_time',
                         'schedule_day_of_week', 'min_support', 'min_confidence', 'min_lift',
                         'max_recommendations', 'decay_rate', 'output_table', 'is_active',
                         'days_back', 'max_items', 'min_item_frequency', 'use_enhanced_mining',
                         'time_weighting_method', 'time_segmentation']:
                if field in schedule_data:
                    update_fields.append(f"{field} = %s")
                    values.append(schedule_data[field])
            
            values.append(schedule_id)
            
            query = f"UPDATE mining_schedules SET {', '.join(update_fields)} WHERE id = %s"
            db.cursor.execute(query, values)
            db.connection.commit()
            
            # Re-add to scheduler if active
            if schedule_data.get('is_active', True):
                # Fetch updated schedule
                db.cursor.execute("SELECT * FROM mining_schedules WHERE id = %s", (schedule_id,))
                row = db.cursor.fetchone()
                schedule = self._row_to_schedule_dict(row)
                self._add_job_to_scheduler(schedule_id, schedule)
            
            logger.info(f"✓ Updated schedule {schedule_id}")
            return {'status': 'updated', 'schedule_id': schedule_id}
            
        except Exception as e:
            logger.error(f"Failed to update schedule: {str(e)}")
            if db.connection:
                db.connection.rollback()
            raise
        finally:
            db.disconnect()

    def delete_schedule(self, schedule_id: int):
        """Delete a schedule"""
        db = DatabaseConnection(self.db_config)
        try:
            db.connect()
            
            # Remove from scheduler
            job_id = f"mining_job_{schedule_id}"
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # Delete from database
            db.cursor.execute("DELETE FROM mining_schedules WHERE id = %s", (schedule_id,))
            db.connection.commit()
            
            logger.info(f"✓ Deleted schedule {schedule_id}")
            return {'status': 'deleted', 'schedule_id': schedule_id}
            
        except Exception as e:
            logger.error(f"Failed to delete schedule: {str(e)}")
            if db.connection:
                db.connection.rollback()
            raise
        finally:
            db.disconnect()

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
                day_of_week = 0
            
            days_ahead = day_of_week - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            
            next_run = (now + timedelta(days=days_ahead)).replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
        else:
            raise ValueError(f"Unsupported schedule type: {schedule_type}")
        
        return next_run

    # ------------------------------------------------------------------
    # APScheduler job entry (IMPORTANT: no threading here)
    # ------------------------------------------------------------------
    def execute_mining_job(self, schedule_id: int):
        """
        APScheduler already runs this in a worker thread.
        DO NOT create new threads inside this method.
        """
        logger.info(f"🎯 Executing mining job for schedule_id={schedule_id}")
        self._execute_mining_job(schedule_id)

    # ------------------------------------------------------------------
    # Actual mining execution
    # ------------------------------------------------------------------
    def _execute_mining_job(self, schedule_id: int):
        start_time = datetime.now()
        log_id = None
        db = DatabaseConnection(self.db_config)

        try:
            db.connect()

            db.cursor.execute(
                "SELECT * FROM mining_schedules WHERE id=%s",
                (schedule_id,),
            )
            row = db.cursor.fetchone()
            if not row:
                raise ValueError(f"Schedule {schedule_id} not found")

            schedule = self._row_to_schedule_dict(row)

            # Create job log with JSON-serializable execution parameters
            execution_params = {
                'min_support': schedule['min_support'],
                'min_confidence': schedule['min_confidence'],
                'min_lift': schedule['min_lift'],
                'max_recommendations': schedule['max_recommendations'],
                'decay_rate': schedule['decay_rate'],
                'days_back': schedule.get('days_back', 365),
                'use_enhanced_mining': schedule.get('use_enhanced_mining', True),
                'time_weighting_method': schedule.get('time_weighting_method', 'exponential_decay'),
                'time_segmentation': schedule.get('time_segmentation', 'weekly'),
                'output_table': schedule.get('output_table', 'sku_recommendations')
            }
            
            db.cursor.execute(
                """
                INSERT INTO mining_job_logs
                (schedule_id, job_name, execution_parameters, started_at)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    schedule_id,
                    schedule["job_name"],
                    json.dumps(execution_params),
                    start_time,
                ),
            )
            log_id = db.cursor.lastrowid
            db.connection.commit()

            logger.info(f"🚀 Mining started: {schedule['job_name']}")

            # --- Call shared mining logic ---
            from app.modules.association_mining.api.endpoints import run_mining_task
            import app.modules.association_mining.api.endpoints as endpoints_module

            class SchedulerTaskManager:
                def __init__(self):
                    self.result = None
                    self.error = None

                def start_task(self, *args, **kwargs): 
                    logger.info("SchedulerTaskManager.start_task called")
                
                def update_progress(self, *args, **kwargs): 
                    logger.info("SchedulerTaskManager.update_progress called")
                
                def complete_task(self, task_id=None, result=None, message="", **kwargs):
                    logger.info(f"SchedulerTaskManager.complete_task called with result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                    logger.info(f"Result recommendations_count: {result.get('recommendations_count') if isinstance(result, dict) else 'N/A'}")
                    self.result = result
                    logger.info(f"self.result set to: {self.result is not None}")

                def fail_task(self, task_id=None, error_msg=None, **kwargs):
                    logger.info(f"SchedulerTaskManager.fail_task called with: {error_msg}")
                    self.error = error_msg

            task_manager = SchedulerTaskManager()
            original_task_manager = endpoints_module.task_manager
            endpoints_module.task_manager = task_manager

            try:
                # Build complete db_config with all connection parameters
                from app.shared.config.config import Config
                config = Config()
                
                complete_db_config = {
                    'host': config.DB_HOST,
                    'port': config.DB_PORT,
                    'user': config.DB_USER,
                    'password': config.DB_PASSWORD,
                    'database': config.DB_NAME,
                    'order_table': config.ORDER_TABLE,
                    'sku_master_table': config.SKU_MASTER_TABLE,
                    'recommendations_table': schedule["output_table"]
                }
                
                run_mining_task(
                    task_id=f"scheduled_{schedule_id}_{int(start_time.timestamp())}",
                    days_back=schedule.get("days_back", 365),
                    min_support=schedule["min_support"],
                    min_confidence=schedule["min_confidence"],
                    min_lift=schedule["min_lift"],
                    max_recommendations=schedule["max_recommendations"],
                    decay_rate=schedule["decay_rate"],
                    use_enhanced_mining=schedule.get("use_enhanced_mining", True),
                    time_weighting_method=schedule.get(
                        "time_weighting_method", "exponential_decay"
                    ),
                    time_segmentation=schedule.get("time_segmentation", "weekly"),
                    db_config=complete_db_config,
                    skip_logging=True  # Scheduler already created log entry
                )
            finally:
                endpoints_module.task_manager = original_task_manager

            end_time = datetime.now()
            execution_time = int((end_time - start_time).total_seconds())

            rules_generated = 0
            records_processed = 0
            
            logger.info(f"========== DEBUG: Extracting results ==========")
            logger.info(f"task_manager.result is None: {task_manager.result is None}")
            logger.info(f"task_manager.error: {task_manager.error}")
            
            if task_manager.result:
                logger.info(f"Task result type: {type(task_manager.result)}")
                logger.info(f"Task result keys: {list(task_manager.result.keys()) if isinstance(task_manager.result, dict) else 'Not a dict'}")
                logger.info(f"Full result: {task_manager.result}")
                
                # Try to get from recommendations_count first
                rules_generated = task_manager.result.get("recommendations_count", 0)
                logger.info(f"recommendations_count: {rules_generated}")
                
                # If not found, try database_stats (from save_recommendations)
                if rules_generated == 0:
                    db_stats = task_manager.result.get("database_stats", {})
                    logger.info(f"database_stats: {db_stats}")
                    if db_stats:
                        rules_generated = db_stats.get("total_written", 0)
                        logger.info(f"total_written from database_stats: {rules_generated}")
                
                # Get records_processed from stats
                stats = task_manager.result.get("stats", {})
                logger.info(f"stats dict: {stats}")
                records_processed = stats.get("total_orders", 0)
                logger.info(f"total_orders: {records_processed}")
                
            logger.info(f"========== FINAL VALUES ==========")
            logger.info(f"rules_generated: {rules_generated}")
            logger.info(f"records_processed: {records_processed}")
            logger.info(f"====================================")

            db.cursor.execute(
                """
                UPDATE mining_job_logs
                SET completed_at=%s,
                    execution_status='success',
                    rules_generated=%s,
                    records_processed=%s,
                    execution_time_seconds=%s
                WHERE id=%s
                """,
                (
                    end_time,
                    rules_generated,
                    records_processed,
                    execution_time,
                    log_id,
                ),
            )

            self._update_schedule_stats(
                db, schedule_id, True, execution_time, rules_generated
            )

            db.connection.commit()
            logger.info(
                f"✅ Mining completed: {schedule['job_name']} "
                f"({rules_generated} rules, {execution_time}s)"
            )

        except Exception as e:
            logger.error(f"❌ Mining failed for schedule {schedule_id}: {e}")

            if log_id:
                db.cursor.execute(
                    """
                    UPDATE mining_job_logs
                    SET completed_at=%s,
                        execution_status='failed',
                        error_message=%s
                    WHERE id=%s
                    """,
                    (datetime.now(), str(e), log_id),
                )

                self._update_schedule_stats(
                    db, schedule_id, False, 0, 0
                )
                db.connection.commit()

        finally:
            db.disconnect()

    def get_job_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent job execution logs"""
        db = DatabaseConnection(self.db_config)
        try:
            db.connect()
            
            query = """
            SELECT id, schedule_id, job_name, started_at, completed_at,
                   execution_status, rules_generated, records_processed,
                   execution_time_seconds, error_message, execution_parameters, error_details
            FROM mining_job_logs
            ORDER BY started_at DESC
            LIMIT %s
            """
            
            db.cursor.execute(query, (limit,))
            logs = db.cursor.fetchall()
            
            result = []
            for log in logs:
                # Parse JSON fields
                import json
                execution_params = None
                if log[10]:
                    try:
                        execution_params = json.loads(log[10]) if isinstance(log[10], str) else log[10]
                    except:
                        execution_params = {}
                
                error_details = None
                if log[11]:
                    try:
                        error_details = json.loads(log[11]) if isinstance(log[11], str) else log[11]
                    except:
                        error_details = {}
                
                result.append({
                    'id': log[0],
                    'schedule_id': log[1],
                    'job_name': log[2],
                    'started_at': log[3].isoformat() if log[3] else None,
                    'completed_at': log[4].isoformat() if log[4] else None,
                    'execution_status': log[5],
                    'rules_generated': log[6],
                    'records_processed': log[7],
                    'execution_time_seconds': log[8],
                    'error_message': log[9],
                    'execution_parameters': execution_params,
                    'error_details': error_details
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get job logs: {str(e)}")
            raise
        finally:
            db.disconnect()

    def delete_all_schedules(self):
        """Delete all schedules and remove from scheduler"""
        db = DatabaseConnection(self.db_config)
        try:
            db.connect()
            
            # Get all schedule IDs
            db.cursor.execute("SELECT id FROM mining_schedules")
            schedule_ids = [row[0] for row in db.cursor.fetchall()]
            
            # Remove all jobs from scheduler
            for schedule_id in schedule_ids:
                job_id = f"mining_job_{schedule_id}"
                if self.scheduler.get_job(job_id):
                    self.scheduler.remove_job(job_id)
            
            # Delete all schedules from database
            db.cursor.execute("DELETE FROM mining_schedules")
            db.connection.commit()
            
            logger.info(f"✓ Deleted all {len(schedule_ids)} schedules")
            return {'status': 'deleted', 'count': len(schedule_ids)}
            
        except Exception as e:
            logger.error(f"Failed to delete all schedules: {str(e)}")
            if db.connection:
                db.connection.rollback()
            raise
        finally:
            db.disconnect()

    # ------------------------------------------------------------------
    # Scheduler helpers
    # ------------------------------------------------------------------
    def _add_job_to_scheduler(self, schedule_id: int, schedule: Dict[str, Any]):
        job_id = f"mining_job_{schedule_id}"

        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        time_parts = schedule["schedule_time"].split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1])

        if schedule["schedule_type"] == "daily":
            trigger = CronTrigger(hour=hour, minute=minute)
        else:
            trigger = CronTrigger(
                day_of_week=schedule.get("schedule_day_of_week", 0),
                hour=hour,
                minute=minute,
            )

        self.scheduler.add_job(
            func=self.execute_mining_job,
            trigger=trigger,
            args=[schedule_id],
            id=job_id,
            name=f"Mining: {schedule['job_name']}",
            replace_existing=True,
        )

    def _load_schedules_from_database(self):
        db = DatabaseConnection(self.db_config)
        try:
            db.connect()

            db.cursor.execute("SELECT * FROM mining_schedules WHERE is_active=1")
            rows = db.cursor.fetchall()

            for row in rows:
                try:
                    schedule = self._row_to_schedule_dict(row)
                    self._add_job_to_scheduler(schedule["id"], schedule)
                    logger.info(f"✓ Loaded schedule {schedule['id']}: {schedule['job_name']}")
                except Exception as e:
                    logger.error(f"Failed to load schedule {row[0]}: {str(e)}")
                    # Continue loading other schedules even if one fails
                    continue
        except Exception as e:
            logger.error(f"Failed to load schedules from database: {str(e)}")
            raise
        finally:
            db.disconnect()

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------
    def _update_schedule_stats(
        self,
        db,
        schedule_id: int,
        success: bool,
        execution_time: int,
        rules_generated: int,
    ):
        if success:
            db.cursor.execute(
                """
                UPDATE mining_schedule_stats
                SET total_executions = total_executions + 1,
                    successful_executions = successful_executions + 1,
                    avg_execution_time_seconds =
                      (avg_execution_time_seconds * successful_executions + %s)
                      / (successful_executions + 1),
                    total_rules_generated = total_rules_generated + %s
                WHERE schedule_id=%s
                """,
                (execution_time, rules_generated, schedule_id),
            )
        else:
            db.cursor.execute(
                """
                UPDATE mining_schedule_stats
                SET total_executions = total_executions + 1,
                    failed_executions = failed_executions + 1
                WHERE schedule_id=%s
                """,
                (schedule_id,),
            )

    # ------------------------------------------------------------------
    # Utils
    # ------------------------------------------------------------------
    def _row_to_schedule_dict(self, r) -> Dict[str, Any]:
        return {
            "id": r[0],
            "job_name": r[1],
            "job_description": r[2],
            "schedule_type": r[3],
            "schedule_time": str(r[4]),
            "schedule_day_of_week": r[5],
            "min_support": float(r[6]),
            "min_confidence": float(r[7]),
            "min_lift": float(r[8]),
            "max_recommendations": r[9],
            "decay_rate": float(r[10]),
            "output_table": r[11],
            "is_active": bool(r[12]),
            "created_at": r[13],
            "updated_at": r[14],
            "last_run_at": r[15],
            "next_run_at": r[16],
            "created_by": r[17],
            "days_back": r[18],
            "max_items": r[19],
            "min_item_frequency": r[20],
            "use_enhanced_mining": bool(r[21]),
            "time_weighting_method": r[22],
            "time_segmentation": r[23],
        }


# ------------------------------------------------------------------
# GLOBAL SINGLETON (CRITICAL FOR FASTAPI + UVICORN)
# ------------------------------------------------------------------

_scheduler_service: Optional[SchedulerService] = None


def get_scheduler_service(db_config=None) -> SchedulerService:
    """
    Singleton accessor.
    Prevents multiple schedulers when Uvicorn reloads.
    """
    global _scheduler_service

    if _scheduler_service is None:
        _scheduler_service = SchedulerService(db_config)

    return _scheduler_service
