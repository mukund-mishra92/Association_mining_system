-- Scheduler tables for association mining automation

-- Main table for storing scheduled jobs
CREATE TABLE IF NOT EXISTS mining_schedules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_name VARCHAR(255) NOT NULL,
    job_description TEXT,
    schedule_type ENUM('daily', 'weekly') NOT NULL,
    schedule_time TIME NOT NULL,
    schedule_day_of_week INT(1) NULL, -- 0=Monday, 1=Tuesday, ... 6=Sunday (for weekly schedules)
    
    -- Mining parameters (JSON format for flexibility)
    min_support DECIMAL(4,3) DEFAULT 0.300,
    min_confidence DECIMAL(4,3) DEFAULT 0.300,
    min_lift DECIMAL(4,2) DEFAULT 1.00,
    max_recommendations INT DEFAULT 10,
    decay_rate DECIMAL(4,3) DEFAULT 0.050,
    
    -- Job configuration
    output_table VARCHAR(255) DEFAULT 'sku_recommendations',
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_run_at TIMESTAMP NULL,
    next_run_at TIMESTAMP NULL,
    
    -- Job metadata
    created_by VARCHAR(255) DEFAULT 'system',
    
    INDEX idx_schedule_type (schedule_type),
    INDEX idx_is_active (is_active),
    INDEX idx_next_run (next_run_at),
    UNIQUE KEY unique_job_name (job_name)
);

-- Table for logging job execution history
CREATE TABLE IF NOT EXISTS mining_job_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    schedule_id INT NOT NULL,
    job_name VARCHAR(255) NOT NULL,
    
    -- Execution details
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    execution_status ENUM('running', 'success', 'failed', 'cancelled') DEFAULT 'running',
    
    -- Results
    rules_generated INT DEFAULT 0,
    records_processed INT DEFAULT 0,
    execution_time_seconds INT DEFAULT 0,
    
    -- Error handling
    error_message TEXT NULL,
    error_details JSON NULL,
    
    -- Execution parameters (snapshot at runtime)
    execution_parameters JSON NULL,
    
    INDEX idx_schedule_id (schedule_id),
    INDEX idx_execution_status (execution_status),
    INDEX idx_started_at (started_at),
    FOREIGN KEY (schedule_id) REFERENCES mining_schedules(id) ON DELETE CASCADE
);

-- Table for storing execution statistics
CREATE TABLE IF NOT EXISTS mining_schedule_stats (
    schedule_id INT PRIMARY KEY,
    total_executions INT DEFAULT 0,
    successful_executions INT DEFAULT 0,
    failed_executions INT DEFAULT 0,
    last_success_at TIMESTAMP NULL,
    last_failure_at TIMESTAMP NULL,
    avg_execution_time_seconds DECIMAL(10,2) DEFAULT 0,
    total_rules_generated INT DEFAULT 0,
    
    -- Timestamps
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (schedule_id) REFERENCES mining_schedules(id) ON DELETE CASCADE
);

-- Insert some example schedules
INSERT INTO mining_schedules (
    job_name, 
    job_description,
    schedule_type, 
    schedule_time, 
    schedule_day_of_week,
    min_support,
    min_confidence,
    min_lift,
    max_recommendations,
    decay_rate,
    is_active
) VALUES 
(
    'Daily Morning Mining',
    'Daily association rule mining at 6:00 AM with balanced parameters',
    'daily',
    '06:00:00',
    NULL,
    0.300,
    0.300,
    1.0,
    10,
    0.050,
    FALSE
),
(
    'Weekly Report Mining',
    'Comprehensive weekly mining every Monday at 9:00 AM',
    'weekly',
    '09:00:00',
    0, -- Monday
    0.250,
    0.250,
    1.0,
    15,
    0.030,
    FALSE
);