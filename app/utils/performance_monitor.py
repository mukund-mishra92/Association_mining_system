"""
Performance Monitoring Utility for Association Mining System
Collects CPU, memory, and mining-specific performance metrics
"""

import psutil
import time
import threading
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from datetime import datetime
import logging

class PerformanceMonitor:
    def __init__(self):
        """Initialize performance monitor"""
        self.logger = logging.getLogger(__name__)
        self.monitoring = False
        self.metrics = []
        self.start_time = None
        self.monitor_thread = None
        
    def start_monitoring(self, job_id: str, interval: float = 1.0):
        """Start monitoring system performance"""
        self.job_id = job_id
        self.interval = interval
        self.monitoring = True
        self.start_time = time.time()
        self.metrics = []
        
        # Start monitoring in separate thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.logger.info(f"Started performance monitoring for job: {job_id}")
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return aggregated metrics"""
        self.monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        
        return self._aggregate_metrics()
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=None)
                memory = psutil.virtual_memory()
                disk_io = psutil.disk_io_counters()
                net_io = psutil.net_io_counters()
                
                metric = {
                    'timestamp': time.time(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used_mb': memory.used / 1024 / 1024,
                    'memory_available_mb': memory.available / 1024 / 1024,
                    'disk_read_mb': disk_io.read_bytes / 1024 / 1024 if disk_io else 0,
                    'disk_write_mb': disk_io.write_bytes / 1024 / 1024 if disk_io else 0,
                    'net_sent_mb': net_io.bytes_sent / 1024 / 1024 if net_io else 0,
                    'net_recv_mb': net_io.bytes_recv / 1024 / 1024 if net_io else 0
                }
                
                self.metrics.append(metric)
                time.sleep(self.interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(self.interval)
    
    def _aggregate_metrics(self) -> Dict[str, Any]:
        """Aggregate collected metrics"""
        if not self.metrics:
            return {}
        
        try:
            df = pd.DataFrame(self.metrics)
            
            # Calculate duration
            total_duration = time.time() - self.start_time if self.start_time else 0
            
            # Aggregate metrics
            aggregated = {
                'duration_seconds': total_duration,
                'cpu_usage_avg': df['cpu_percent'].mean(),
                'cpu_usage_max': df['cpu_percent'].max(),
                'cpu_usage_min': df['cpu_percent'].min(),
                'memory_usage_avg': df['memory_used_mb'].mean(),
                'memory_usage_max': df['memory_used_mb'].max(),
                'memory_usage_min': df['memory_used_mb'].min(),
                'memory_percent_avg': df['memory_percent'].mean(),
                'memory_percent_max': df['memory_percent'].max(),
                'disk_io_total_mb': df['disk_read_mb'].iloc[-1] + df['disk_write_mb'].iloc[-1] if len(df) > 0 else 0,
                'network_io_total_mb': df['net_sent_mb'].iloc[-1] + df['net_recv_mb'].iloc[-1] if len(df) > 0 else 0,
                'sample_count': len(df),
                'monitoring_interval': self.interval
            }
            
            return aggregated
            
        except Exception as e:
            self.logger.error(f"Error aggregating metrics: {str(e)}")
            return {'duration_seconds': time.time() - self.start_time if self.start_time else 0}

class MiningMetricsCollector:
    """Collects mining-specific performance metrics"""
    
    @staticmethod
    def analyze_mining_results(rules_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze mining results and extract performance metrics"""
        if rules_df.empty:
            return {
                'rules_generated': 0,
                'rules_filtered': 0,
                'confidence_avg': 0,
                'confidence_max': 0,
                'confidence_min': 0,
                'support_avg': 0,
                'support_max': 0,
                'support_min': 0,
                'lift_avg': 0,
                'lift_max': 0,
                'lift_min': 0
            }
        
        try:
            metrics = {
                'rules_generated': len(rules_df),
                'rules_filtered': len(rules_df),  # Will be updated if filtering is applied
            }
            
            # Confidence metrics
            if 'confidence' in rules_df.columns:
                metrics.update({
                    'confidence_avg': float(rules_df['confidence'].mean()),
                    'confidence_max': float(rules_df['confidence'].max()),
                    'confidence_min': float(rules_df['confidence'].min()),
                })
            
            # Support metrics
            if 'support' in rules_df.columns:
                metrics.update({
                    'support_avg': float(rules_df['support'].mean()),
                    'support_max': float(rules_df['support'].max()),
                    'support_min': float(rules_df['support'].min()),
                })
            
            # Lift metrics
            if 'lift' in rules_df.columns:
                metrics.update({
                    'lift_avg': float(rules_df['lift'].mean()),
                    'lift_max': float(rules_df['lift'].max()),
                    'lift_min': float(rules_df['lift'].min()),
                })
            
            return metrics
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error analyzing mining results: {str(e)}")
            return {'rules_generated': len(rules_df) if not rules_df.empty else 0}
    
    @staticmethod
    def collect_database_metrics(connection, query_start_time: float) -> Dict[str, Any]:
        """Collect database performance metrics"""
        try:
            query_duration = (time.time() - query_start_time) * 1000  # Convert to milliseconds
            
            metrics = {
                'db_query_time_ms': query_duration,
                'db_connection_time_ms': 0  # Could be enhanced to measure connection time
            }
            
            # Could add more database-specific metrics here
            # e.g., query complexity, rows processed, etc.
            
            return metrics
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error collecting database metrics: {str(e)}")
            return {'db_query_time_ms': 0}
    
    @staticmethod
    def measure_processing_time(start_time: float) -> float:
        """Measure processing time in milliseconds"""
        return (time.time() - start_time) * 1000

class JobPerformanceTracker:
    """High-level performance tracker for mining jobs"""
    
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.start_time = time.time()
        self.performance_monitor = PerformanceMonitor()
        self.metrics = {}
        self.logger = logging.getLogger(__name__)
        
    def start(self):
        """Start performance tracking"""
        self.performance_monitor.start_monitoring(self.job_id)
        self.logger.info(f"Started performance tracking for job: {self.job_id}")
    
    def record_database_operation(self, operation_start_time: float):
        """Record database operation metrics"""
        db_metrics = MiningMetricsCollector.collect_database_metrics(None, operation_start_time)
        self.metrics.update(db_metrics)
    
    def record_processing_metrics(self, processing_start_time: float):
        """Record processing time metrics"""
        processing_time = MiningMetricsCollector.measure_processing_time(processing_start_time)
        self.metrics['processing_time_ms'] = processing_time
    
    def record_mining_results(self, rules_df: pd.DataFrame):
        """Record mining results metrics"""
        mining_metrics = MiningMetricsCollector.analyze_mining_results(rules_df)
        self.metrics.update(mining_metrics)
    
    def finish(self) -> Dict[str, Any]:
        """Finish tracking and return all metrics"""
        # Stop system monitoring
        system_metrics = self.performance_monitor.stop_monitoring()
        
        # Combine all metrics
        all_metrics = {
            **system_metrics,
            **self.metrics,
            'total_duration_seconds': time.time() - self.start_time
        }
        
        self.logger.info(f"Finished performance tracking for job: {self.job_id}")
        return all_metrics