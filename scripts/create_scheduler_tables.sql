-- ============================================================
-- Association Mining System - Scheduler Tables
-- Execute this SQL script to create the required scheduler tables
-- ============================================================

-- 1. Mining Schedules Table
-- Stores schedule configurations
CREATE TABLE IF NOT EXISTS mining_schedules (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    job_name VARCHAR(255) NOT NULL,
    job_description TEXT,
    schedule_type ENUM('daily', 'weekly') NOT NULL,
    schedule_time TIME NOT NULL,
    schedule_day_of_week TINYINT DEFAULT NULL,
    min_support DECIMAL(6,4) NOT NULL DEFAULT 0.3000,
    min_confidence DECIMAL(6,4) NOT NULL DEFAULT 0.3000,
    min_lift DECIMAL(6,4) NOT NULL DEFAULT 1.0000,
    max_recommendations INT NOT NULL DEFAULT 10,
    decay_rate DECIMAL(5,4) NOT NULL DEFAULT 0.0500,
    output_table VARCHAR(255) NOT NULL DEFAULT 'sku_recommendations',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    last_run_at DATETIME DEFAULT NULL,
    next_run_at DATETIME DEFAULT NULL,
    created_by VARCHAR(100) NOT NULL DEFAULT 'system',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_job_name (job_name),
    KEY idx_is_active (is_active),
    KEY idx_next_run_at (next_run_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 2. Mining Schedule Stats Table
-- Tracks execution statistics for each schedule
CREATE TABLE IF NOT EXISTS mining_schedule_stats (
    schedule_id INT NOT NULL PRIMARY KEY,
    total_executions INT DEFAULT 0,
    successful_executions INT DEFAULT 0,
    failed_executions INT DEFAULT 0,
    avg_execution_time_seconds DECIMAL(10,2) DEFAULT 0.00,
    total_rules_generated INT DEFAULT 0,
    last_success_at DATETIME DEFAULT NULL,
    last_failure_at DATETIME DEFAULT NULL,
    KEY idx_schedule_id (schedule_id),
    CONSTRAINT mining_schedule_stats_ibfk_1 
        FOREIGN KEY (schedule_id) REFERENCES mining_schedules(id) 
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 3. Mining Job Logs Table
-- Records detailed logs for each schedule execution
CREATE TABLE IF NOT EXISTS mining_job_logs (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    schedule_id INT NOT NULL,
    job_name VARCHAR(255) NOT NULL,
    started_at DATETIME DEFAULT NULL,
    completed_at DATETIME DEFAULT NULL,
    execution_status ENUM('running', 'success', 'failed') NOT NULL DEFAULT 'running',
    rules_generated INT DEFAULT 0,
    records_processed INT DEFAULT 0,
    execution_time_seconds INT DEFAULT 0,
    error_message TEXT,
    error_details JSON DEFAULT NULL,
    execution_parameters JSON DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    KEY idx_schedule_id (schedule_id),
    KEY idx_started_at (started_at),
    CONSTRAINT mining_job_logs_ibfk_1 
        FOREIGN KEY (schedule_id) REFERENCES mining_schedules(id) 
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- Verification Query
-- Run this to confirm tables were created successfully
-- ============================================================
SELECT 
    'Tables created successfully!' AS status,
    (SELECT COUNT(*) FROM information_schema.tables 
     WHERE table_schema = DATABASE() 
     AND table_name = 'mining_schedules') AS mining_schedules_exists,
    (SELECT COUNT(*) FROM information_schema.tables 
     WHERE table_schema = DATABASE() 
     AND table_name = 'mining_schedule_stats') AS mining_schedule_stats_exists,
    (SELECT COUNT(*) FROM information_schema.tables 
     WHERE table_schema = DATABASE() 
     AND table_name = 'mining_job_logs') AS mining_job_logs_exists;
