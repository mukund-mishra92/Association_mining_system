-- Bin Velocity Analysis System - Database Schema
-- This schema supports SKU velocity calculation and bin optimization

-- Table 1: SKU Velocity Analysis
-- Stores calculated velocity scores (1, 2, 3) for each SKU based on order patterns
CREATE TABLE IF NOT EXISTS sku_velocity (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sku_code VARCHAR(100) NOT NULL,
    velocity_score INT NOT NULL CHECK (velocity_score IN (1, 2, 3)),
    order_frequency DECIMAL(10, 4) NOT NULL,           -- Orders per day
    total_orders INT NOT NULL,                          -- Total orders in analysis period
    weighted_score DECIMAL(10, 4) NOT NULL,           -- Time-decay weighted score
    analysis_period_days INT NOT NULL DEFAULT 90,      -- Days analyzed
    calculated_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_sku_code (sku_code),
    INDEX idx_velocity_score (velocity_score),
    INDEX idx_calculated_date (calculated_date),
    INDEX idx_active (is_active),
    UNIQUE KEY unique_sku_active (sku_code, calculated_date)
);

-- Table 2: Bin Configuration
-- Defines which SKUs are in each bin and bin capacity
CREATE TABLE IF NOT EXISTS bin_configuration (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bin_id VARCHAR(50) NOT NULL,
    sku_code VARCHAR(100) NOT NULL,
    bin_capacity INT NOT NULL CHECK (bin_capacity IN (1, 2, 4, 6)), -- Max SKUs per bin
    current_sku_count INT NOT NULL DEFAULT 1,                        -- Current SKUs in bin
    bin_location VARCHAR(100),                                        -- Warehouse location
    zone VARCHAR(50),                                                 -- Warehouse zone
    created_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    INDEX idx_bin_id (bin_id),
    INDEX idx_sku_code (sku_code),
    INDEX idx_bin_capacity (bin_capacity),
    INDEX idx_zone (zone),
    INDEX idx_active (is_active),
    UNIQUE KEY unique_bin_sku_active (bin_id, sku_code, is_active)
);

-- Table 3: Bin Velocity Scores
-- Stores calculated composite velocity scores for each bin (updated weekly)
CREATE TABLE IF NOT EXISTS bin_velocity_scores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bin_id VARCHAR(50) NOT NULL,
    composite_velocity_score DECIMAL(5, 2) NOT NULL,    -- Calculated composite score
    individual_sku_velocities JSON,                      -- Array of SKU velocities in bin
    sku_count INT NOT NULL,                             -- Number of SKUs in bin
    bin_capacity INT NOT NULL,                          -- Bin capacity (1,2,4,6)
    capacity_utilization DECIMAL(5, 2) NOT NULL,       -- % of bin capacity used
    optimization_recommendation TEXT,                    -- AI recommendation for bin placement
    priority_score INT NOT NULL CHECK (priority_score BETWEEN 1 AND 10), -- Placement priority
    calculation_date DATE NOT NULL,                     -- Weekly calculation date
    analysis_period_start DATE NOT NULL,               -- Start of data period analyzed
    analysis_period_end DATE NOT NULL,                 -- End of data period analyzed
    created_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_bin_id (bin_id),
    INDEX idx_composite_score (composite_velocity_score),
    INDEX idx_calculation_date (calculation_date),
    INDEX idx_priority_score (priority_score),
    INDEX idx_capacity_utilization (capacity_utilization),
    UNIQUE KEY unique_bin_week (bin_id, calculation_date)
);

-- Table 4: Velocity Calculation Parameters
-- Stores configuration parameters for velocity calculations
CREATE TABLE IF NOT EXISTS velocity_calculation_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    parameter_name VARCHAR(100) NOT NULL UNIQUE,
    parameter_value DECIMAL(10, 4) NOT NULL,
    description TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_parameter_name (parameter_name)
);

-- Insert default velocity calculation parameters
INSERT INTO velocity_calculation_config (parameter_name, parameter_value, description) VALUES
('time_decay_rate', 0.05, 'Rate of time decay for historical orders (same as association mining)'),
('high_velocity_threshold', 0.80, 'Percentile threshold for velocity score 3 (high)'),
('medium_velocity_threshold', 0.50, 'Percentile threshold for velocity score 2 (medium)'),
('analysis_period_days', 90, 'Number of days to analyze for velocity calculation'),
('min_orders_for_calculation', 5, 'Minimum orders required for velocity calculation'),
('weekly_calculation_day', 1, 'Day of week for weekly calculations (1=Monday)')
ON DUPLICATE KEY UPDATE 
    parameter_value = VALUES(parameter_value),
    description = VALUES(description);

-- Table 5: Velocity Calculation Jobs
-- Tracks weekly velocity calculation jobs for monitoring
CREATE TABLE IF NOT EXISTS velocity_calculation_jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_id VARCHAR(100) NOT NULL UNIQUE,
    job_type ENUM('sku_velocity', 'bin_velocity', 'full_analysis') NOT NULL,
    status ENUM('pending', 'running', 'completed', 'failed') NOT NULL DEFAULT 'pending',
    start_time DATETIME,
    end_time DATETIME,
    duration_seconds INT,
    records_processed INT DEFAULT 0,
    records_updated INT DEFAULT 0,
    error_message TEXT,
    calculation_date DATE NOT NULL,
    created_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_job_id (job_id),
    INDEX idx_status (status),
    INDEX idx_job_type (job_type),
    INDEX idx_calculation_date (calculation_date),
    INDEX idx_created_date (created_date)
);

-- Trigger to update bin configuration when SKUs are added/removed
DELIMITER //
CREATE TRIGGER update_bin_sku_count 
AFTER INSERT ON bin_configuration 
FOR EACH ROW 
BEGIN
    UPDATE bin_configuration 
    SET current_sku_count = (
        SELECT COUNT(*) 
        FROM bin_configuration 
        WHERE bin_id = NEW.bin_id AND is_active = TRUE
    )
    WHERE bin_id = NEW.bin_id;
END//
DELIMITER ;

-- Create views for easier data access
CREATE VIEW v_current_sku_velocities AS
SELECT 
    sv.sku_code,
    sv.velocity_score,
    sv.order_frequency,
    sv.total_orders,
    sv.weighted_score,
    sv.analysis_period_days,
    sv.calculated_date,
    CASE 
        WHEN sv.velocity_score = 3 THEN 'High'
        WHEN sv.velocity_score = 2 THEN 'Medium'
        WHEN sv.velocity_score = 1 THEN 'Low'
    END as velocity_category
FROM sku_velocity sv
WHERE sv.is_active = TRUE
AND sv.calculated_date = (
    SELECT MAX(calculated_date) 
    FROM sku_velocity sv2 
    WHERE sv2.sku_code = sv.sku_code AND sv2.is_active = TRUE
);

CREATE VIEW v_current_bin_scores AS
SELECT 
    bvs.bin_id,
    bvs.composite_velocity_score,
    bvs.sku_count,
    bvs.bin_capacity,
    bvs.capacity_utilization,
    bvs.priority_score,
    bvs.optimization_recommendation,
    bc.zone,
    bc.bin_location,
    GROUP_CONCAT(bc.sku_code ORDER BY bc.sku_code) as sku_list,
    bvs.calculation_date
FROM bin_velocity_scores bvs
JOIN bin_configuration bc ON bvs.bin_id = bc.bin_id
WHERE bvs.calculation_date = (
    SELECT MAX(calculation_date) 
    FROM bin_velocity_scores bvs2 
    WHERE bvs2.bin_id = bvs.bin_id
)
AND bc.is_active = TRUE
GROUP BY bvs.bin_id, bvs.composite_velocity_score, bvs.sku_count, 
         bvs.bin_capacity, bvs.capacity_utilization, bvs.priority_score,
         bvs.optimization_recommendation, bc.zone, bc.bin_location, bvs.calculation_date;

-- Create stored procedure for velocity calculation status
DELIMITER //
CREATE PROCEDURE GetVelocitySystemStatus()
BEGIN
    SELECT 
        'SKU Velocities' as metric_type,
        COUNT(*) as total_count,
        MAX(calculated_date) as last_update
    FROM sku_velocity 
    WHERE is_active = TRUE
    
    UNION ALL
    
    SELECT 
        'Bin Configurations' as metric_type,
        COUNT(*) as total_count,
        MAX(last_updated) as last_update
    FROM bin_configuration 
    WHERE is_active = TRUE
    
    UNION ALL
    
    SELECT 
        'Bin Velocity Scores' as metric_type,
        COUNT(*) as total_count,
        MAX(calculation_date) as last_update
    FROM bin_velocity_scores;
END//
DELIMITER ;