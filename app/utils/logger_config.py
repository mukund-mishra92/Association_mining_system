"""
Enhanced Logging Configuration for Association Mining System
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_detailed_logging():
    """Setup detailed logging for mining operations"""
    
    # Create logs directory
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create timestamp for session
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Setup different log files
    log_files = {
        'mining': os.path.join(logs_dir, f'mining_detailed_{timestamp}.log'),
        'api': os.path.join(logs_dir, f'api_detailed_{timestamp}.log'),
        'database': os.path.join(logs_dir, f'database_detailed_{timestamp}.log'),
        'performance': os.path.join(logs_dir, f'performance_{timestamp}.log')
    }
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s:%(lineno)d | %(funcName)s() | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler (less verbose)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File handlers for different components
    handlers = {}
    
    # Mining operations detailed log
    mining_handler = RotatingFileHandler(
        log_files['mining'], 
        maxBytes=50*1024*1024,  # 50MB
        backupCount=5
    )
    mining_handler.setLevel(logging.DEBUG)
    mining_handler.setFormatter(detailed_formatter)
    
    # API operations log
    api_handler = RotatingFileHandler(
        log_files['api'],
        maxBytes=20*1024*1024,  # 20MB
        backupCount=3
    )
    api_handler.setLevel(logging.DEBUG)
    api_handler.setFormatter(detailed_formatter)
    
    # Database operations log
    db_handler = RotatingFileHandler(
        log_files['database'],
        maxBytes=20*1024*1024,  # 20MB
        backupCount=3
    )
    db_handler.setLevel(logging.DEBUG)
    db_handler.setFormatter(detailed_formatter)
    
    # Performance log
    perf_handler = RotatingFileHandler(
        log_files['performance'],
        maxBytes=10*1024*1024,  # 10MB
        backupCount=2
    )
    perf_handler.setLevel(logging.INFO)
    perf_handler.setFormatter(detailed_formatter)
    
    # Configure specific loggers
    mining_logger = logging.getLogger('app.services')
    mining_logger.addHandler(mining_handler)
    mining_logger.setLevel(logging.DEBUG)
    
    api_logger = logging.getLogger('app.api')
    api_logger.addHandler(api_handler)
    api_logger.setLevel(logging.DEBUG)
    
    db_logger = logging.getLogger('app.database')
    db_logger.addHandler(db_handler)
    db_logger.setLevel(logging.DEBUG)
    
    perf_logger = logging.getLogger('performance')
    perf_logger.addHandler(perf_handler)
    perf_logger.setLevel(logging.INFO)
    
    # Log the setup
    logging.info("=" * 80)
    logging.info("ASSOCIATION MINING SYSTEM - DETAILED LOGGING STARTED")
    logging.info("=" * 80)
    logging.info(f"Session Timestamp: {timestamp}")
    logging.info(f"Logs Directory: {logs_dir}")
    for log_type, log_path in log_files.items():
        logging.info(f"{log_type.upper()} Log: {log_path}")
    logging.info("=" * 80)
    
    return log_files

def log_performance(operation, start_time, end_time, details=None):
    """Log performance metrics"""
    perf_logger = logging.getLogger('performance')
    duration = end_time - start_time
    
    message = f"PERFORMANCE | {operation} | Duration: {duration:.3f}s"
    if details:
        message += f" | Details: {details}"
    
    perf_logger.info(message)

def log_memory_usage(operation, stage):
    """Log current memory usage"""
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        perf_logger = logging.getLogger('performance')
        perf_logger.info(f"MEMORY | {operation} | {stage} | Memory: {memory_mb:.1f} MB")
        
    except ImportError:
        pass  # psutil not available

def log_data_info(operation, data, stage):
    """Log data information (shape, size, etc.)"""
    logger = logging.getLogger('app.services.mining_service')
    
    if hasattr(data, 'shape'):
        logger.debug(f"DATA_INFO | {operation} | {stage} | Shape: {data.shape}")
    elif hasattr(data, '__len__'):
        logger.debug(f"DATA_INFO | {operation} | {stage} | Length: {len(data)}")
    else:
        logger.debug(f"DATA_INFO | {operation} | {stage} | Type: {type(data)}")