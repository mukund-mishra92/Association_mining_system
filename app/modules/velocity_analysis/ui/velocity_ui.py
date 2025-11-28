"""
Bin Velocity Analysis - Web Interface
Enhanced web interface integrated with the existing association mining system
"""

VELOCITY_ANALYSIS_HTML = '''
<!-- Velocity Analysis Section -->
<div class="velocity-analysis-section mt-5" id="velocityAnalysisSection" style="display: none;">
    <div class="card border-primary">
        <div class="card-header bg-primary text-white">
            <h4 class="mb-0">
                <i class="fas fa-tachometer-alt me-2"></i>
                Bin Velocity Analysis System
                <span class="badge bg-light text-primary ms-2">NEW</span>
            </h4>
            <small>SKU velocity calculation and bin optimization for warehouse management</small>
        </div>
        <div class="card-body">
            
            <!-- Step 1: Database Configuration -->
            <div class="velocity-config-section mb-4">
                <h5 class="text-primary">
                    <i class="fas fa-database me-2"></i>
                    Step 1: Database Configuration for Velocity Analysis
                </h5>
                
                <!-- Configuration Mode Selector -->
                <div class="mb-3">
                    <div class="form-check form-check-inline">
                        <input class="form-check-input" type="radio" name="configMode" id="sharedConfig" value="shared" checked>
                        <label class="form-check-label" for="sharedConfig">
                            <i class="fas fa-link me-1"></i>Use Shared Configuration
                        </label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input class="form-check-input" type="radio" name="configMode" id="customConfig" value="custom">
                        <label class="form-check-label" for="customConfig">
                            <i class="fas fa-cog me-1"></i>Custom Configuration
                        </label>
                    </div>
                </div>
                
                <div class="row">
                    <!-- Shared Configuration Info -->
                    <div class="col-md-8" id="sharedConfigSection">
                        <div class="card border-info">
                            <div class="card-body">
                                <div class="alert alert-info mb-3">
                                    <i class="fas fa-info-circle me-2"></i>
                                    <strong>Shared Database Configuration</strong><br>
                                    Velocity analysis uses the same database configuration as the main association mining system.
                                </div>
                                
                                <div class="d-grid gap-2 d-md-flex">
                                    <button class="btn btn-outline-primary" onclick="testVelocityConnection()">
                                        <i class="fas fa-plug me-2"></i>Test Connection (Shared Config)
                                    </button>
                                    <button class="btn btn-success" onclick="initializeVelocityDatabase()">
                                        <i class="fas fa-cogs me-2"></i>Initialize Velocity Tables
                                    </button>
                                    <button class="btn btn-info" onclick="checkVelocitySystemStatus()">
                                        <i class="fas fa-chart-line me-2"></i>System Status
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Custom Configuration Form -->
                    <div class="col-md-8" id="customConfigSection" style="display: none;">
                        <div class="card border-warning">
                            <div class="card-header bg-warning text-dark">
                                <h6 class="mb-0">
                                    <i class="fas fa-exclamation-triangle me-2"></i>
                                    Custom Database Configuration
                                </h6>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Database Host</label>
                                            <input type="text" class="form-control" id="velocityDbHost" value="localhost">
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Username</label>
                                            <input type="text" class="form-control" id="velocityDbUser" value="root">
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Port</label>
                                            <input type="number" class="form-control" id="velocityDbPort" value="3306">
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Password</label>
                                            <input type="password" class="form-control" id="velocityDbPassword" value="">
                                        </div>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Database Name</label>
                                            <input type="text" class="form-control" id="velocityDbName" value="neo">
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Orders Table</label>
                                            <input type="text" class="form-control" id="velocityOrdersTable" value="wms_to_wcs_order_line_request_data">
                                            <small class="text-muted">Table containing order data</small>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="d-grid gap-2 d-md-flex">
                                    <button class="btn btn-outline-primary" onclick="testVelocityConnectionCustom()">
                                        <i class="fas fa-plug me-2"></i>Test Custom Connection
                                    </button>
                                    <button class="btn btn-warning" onclick="saveVelocityConfig()">
                                        <i class="fas fa-save me-2"></i>Save Configuration
                                    </button>
                                    <button class="btn btn-success" onclick="initializeVelocityDatabase()">
                                        <i class="fas fa-cogs me-2"></i>Initialize Tables
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Status Panel -->
                    <div class="col-md-4">
                        <div class="card border-info">
                            <div class="card-header bg-info text-white">
                                <h6 class="mb-0">Connection Status</h6>
                            </div>
                            <div class="card-body">
                                <div id="velocityConnectionStatus">
                                    <span class="status-indicator status-disconnected"></span>
                                    <span>Ready to test connection</span>
                                </div>
                                <div id="velocitySystemInfo" class="mt-3" style="display: none;">
                                    <small class="text-muted">System Information</small>
                                    <div id="velocitySystemDetails"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div id="velocityConnectionResult" class="mt-3"></div>
            </div>

            <!-- Step 2: Velocity Analysis Operations -->
            <div class="velocity-operations-section mb-4">
                <h5 class="text-primary">
                    <i class="fas fa-calculator me-2"></i>
                    Step 2: Velocity Analysis Operations
                </h5>
                
                <div class="row">
                    <!-- SKU Velocity Calculation -->
                    <div class="col-md-6">
                        <div class="card border-warning">
                            <div class="card-header bg-warning text-dark">
                                <h6 class="mb-0">
                                    <i class="fas fa-box me-2"></i>SKU Velocity Calculation
                                </h6>
                            </div>
                            <div class="card-body">
                                <div class="mb-3">
                                    <label class="form-label">Analysis Period (Days)</label>
                                    <input type="number" class="form-control" id="velocityAnalysisDays" value="90" min="30" max="365">
                                    <small class="text-muted">Number of days to analyze for velocity calculation</small>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Time Decay Rate</label>
                                    <input type="number" class="form-control" id="velocityDecayRate" value="0.05" min="0.01" max="0.5" step="0.01">
                                    <small class="text-muted">Rate of time decay for historical orders (0.01-0.5)</small>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Minimum Orders Threshold</label>
                                    <input type="number" class="form-control" id="velocityMinOrders" value="5" min="1" max="50">
                                    <small class="text-muted">Minimum orders required for velocity calculation</small>
                                </div>
                                
                                <div class="d-grid">
                                    <button class="btn btn-warning" onclick="calculateSkuVelocities()">
                                        <i class="fas fa-play me-2"></i>Calculate SKU Velocities
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Bin Velocity Calculation -->
                    <div class="col-md-6">
                        <div class="card border-success">
                            <div class="card-header bg-success text-white">
                                <h6 class="mb-0">
                                    <i class="fas fa-archive me-2"></i>Bin Velocity Calculation
                                </h6>
                            </div>
                            <div class="card-body">
                                <div class="alert alert-info alert-sm">
                                    <i class="fas fa-info-circle me-2"></i>
                                    Calculate composite velocity scores for bins based on SKU composition (1, 2, 4, or 6 SKUs per bin)
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Calculation Date</label>
                                    <input type="date" class="form-control" id="binCalculationDate" value="">
                                </div>
                                
                                <div class="d-grid">
                                    <button class="btn btn-success" onclick="calculateBinVelocities()">
                                        <i class="fas fa-play me-2"></i>Calculate Bin Velocities
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Weekly Analysis -->
                <div class="row mt-3">
                    <div class="col-md-12">
                        <div class="card border-primary">
                            <div class="card-header bg-primary text-white">
                                <h6 class="mb-0">
                                    <i class="fas fa-calendar-week me-2"></i>Weekly Complete Analysis
                                </h6>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-8">
                                        <p>Run complete weekly analysis including both SKU velocities and bin composite scores. This is typically scheduled to run automatically every Monday.</p>
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" id="forceWeeklyRun">
                                            <label class="form-check-label" for="forceWeeklyRun">
                                                Force run (override schedule check)
                                            </label>
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="d-grid">
                                            <button class="btn btn-primary" onclick="runWeeklyAnalysis()">
                                                <i class="fas fa-calendar-check me-2"></i>Run Weekly Analysis
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Step 3: Results and Visualization -->
            <div class="velocity-results-section">
                <h5 class="text-primary">
                    <i class="fas fa-chart-bar me-2"></i>
                    Step 3: Results and Visualization
                </h5>
                
                <div class="row">
                    <div class="col-md-4">
                        <div class="card border-info">
                            <div class="card-header bg-info text-white">
                                <h6 class="mb-0">Quick Actions</h6>
                            </div>
                            <div class="card-body">
                                <div class="d-grid gap-2">
                                    <button class="btn btn-outline-info btn-sm" onclick="loadVelocityData('sku_velocities')">
                                        <i class="fas fa-list me-2"></i>View SKU Velocities
                                    </button>
                                    <button class="btn btn-outline-info btn-sm" onclick="loadVelocityData('bin_velocities')">
                                        <i class="fas fa-table me-2"></i>View Bin Scores
                                    </button>
                                    <button class="btn btn-outline-info btn-sm" onclick="loadVelocityData('both')">
                                        <i class="fas fa-eye me-2"></i>View All Data
                                    </button>
                                    <button class="btn btn-outline-success btn-sm" onclick="exportVelocityData()">
                                        <i class="fas fa-download me-2"></i>Export Data
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-8">
                        <!-- Results will be displayed here -->
                        <div id="velocityResults">
                            <div class="text-center text-muted py-5">
                                <i class="fas fa-chart-line fa-3x mb-3"></i>
                                <p>Run velocity analysis to see results here</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Progress and Status -->
            <div id="velocityProgress" style="display: none;" class="mt-4">
                <div class="card border-warning">
                    <div class="card-body">
                        <h6 class="text-warning">
                            <i class="fas fa-spinner fa-spin me-2"></i>Processing...
                        </h6>
                        <div class="progress">
                            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                                 role="progressbar" style="width: 0%" id="velocityProgressBar"></div>
                        </div>
                        <div id="velocityProgressText" class="mt-2 text-muted">Initializing...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
// Velocity Analysis JavaScript Functions

// Set today's date as default
document.addEventListener('DOMContentLoaded', function() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('binCalculationDate').value = today;
    
    // Load existing database config if available
    if (typeof USER_DB_CONFIG !== 'undefined') {
        document.getElementById('velocityDbHost').value = USER_DB_CONFIG.host || 'localhost';
        document.getElementById('velocityDbUser').value = USER_DB_CONFIG.user || 'root';
        document.getElementById('velocityDbPort').value = USER_DB_CONFIG.port || 3306;
        document.getElementById('velocityDbName').value = USER_DB_CONFIG.database || 'neo';
    }
});

function getVelocityDbConfig() {
    return {
        host: document.getElementById('velocityDbHost').value,
        user: document.getElementById('velocityDbUser').value,
        password: document.getElementById('velocityDbPassword').value,
        database: document.getElementById('velocityDbName').value,
        port: parseInt(document.getElementById('velocityDbPort').value),
        orders_table: document.getElementById('velocityOrdersTable').value
    };
}

function showVelocityProgress(text) {
    document.getElementById('velocityProgress').style.display = 'block';
    document.getElementById('velocityProgressText').textContent = text;
    document.getElementById('velocityProgressBar').style.width = '50%';
}

function hideVelocityProgress() {
    document.getElementById('velocityProgress').style.display = 'none';
    document.getElementById('velocityProgressBar').style.width = '0%';
}

function testVelocityConnection() {
    showVelocityProgress('Testing database connection with shared configuration...');
    
    fetch('/api/velocity/test-connection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}) // Empty body since using shared config
    })
    .then(response => response.json())
    .then(data => {
        hideVelocityProgress();
        
        const statusDiv = document.getElementById('velocityConnectionStatus');
        const resultDiv = document.getElementById('velocityConnectionResult');
        
        if (data.success) {
            statusDiv.innerHTML = '<span class="status-indicator status-connected"></span><span>Connected (Shared Config)</span>';
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle me-2"></i>
                    <strong>Connection Successful!</strong><br>
                    ${data.message}<br>
                    <small>Database: ${data.database_config ? data.database_config.database + ' on ' + data.database_config.host : 'Unknown'}</small><br>
                    <small>Timestamp: ${data.timestamp}</small>
                    ${data.tables_status ? '<br><small>Tables checked: ' + Object.keys(data.tables_status).length + '</small>' : ''}
                </div>
            `;
        } else {
            statusDiv.innerHTML = '<span class="status-indicator status-disconnected"></span><span>Failed</span>';
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Connection Failed!</strong><br>
                    ${data.message}
                </div>
            `;
        }
    })
    .catch(error => {
        hideVelocityProgress();
        console.error('Error:', error);
        document.getElementById('velocityConnectionStatus').innerHTML = 
            '<span class="status-indicator status-disconnected"></span><span>Error</span>';
        document.getElementById('velocityConnectionResult').innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Connection Error!</strong><br>
                ${error.message}
            </div>
        `;
    });
}

function initializeVelocityDatabase() {
    const dbConfig = getVelocityDbConfig();
    showVelocityProgress('Initializing velocity analysis tables...');
    
    fetch('/api/velocity/initialize-database', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({...dbConfig, create_tables: true})
    })
    .then(response => response.json())
    .then(data => {
        hideVelocityProgress();
        
        const resultDiv = document.getElementById('velocityConnectionResult');
        
        if (data.success) {
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle me-2"></i>
                    <strong>Database Initialized Successfully!</strong><br>
                    ${data.message}<br>
                    ${data.tables_created ? '<small>Tables created: ' + data.tables_created.join(', ') + '</small>' : ''}
                </div>
            `;
        } else {
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Initialization Failed!</strong><br>
                    ${data.message}
                </div>
            `;
        }
    })
    .catch(error => {
        hideVelocityProgress();
        console.error('Error:', error);
        document.getElementById('velocityConnectionResult').innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Initialization Error!</strong><br>
                ${error.message}
            </div>
        `;
    });
}

function checkVelocitySystemStatus() {
    const dbConfig = getVelocityDbConfig();
    showVelocityProgress('Checking system status...');
    
    fetch('/api/velocity/get-system-status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({db_config: dbConfig})
    })
    .then(response => response.json())
    .then(data => {
        hideVelocityProgress();
        
        if (data.success) {
            const systemInfo = document.getElementById('velocitySystemInfo');
            const systemDetails = document.getElementById('velocitySystemDetails');
            
            let statusHtml = '';
            for (const [key, value] of Object.entries(data.status)) {
                statusHtml += `
                    <div class="small">
                        <strong>${key}:</strong> ${value.count} records
                        <br><small class="text-muted">Last update: ${value.last_update || 'Never'}</small>
                    </div>
                    <hr class="my-1">
                `;
            }
            
            systemDetails.innerHTML = statusHtml;
            systemInfo.style.display = 'block';
        } else {
            document.getElementById('velocityConnectionResult').innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Status Check Failed!</strong><br>
                    ${data.message}
                </div>
            `;
        }
    })
    .catch(error => {
        hideVelocityProgress();
        console.error('Error:', error);
    });
}

function calculateSkuVelocities() {
    const dbConfig = getVelocityDbConfig();
    const parameters = {
        analysis_period_days: parseInt(document.getElementById('velocityAnalysisDays').value),
        time_decay_rate: parseFloat(document.getElementById('velocityDecayRate').value),
        min_orders_for_calculation: parseInt(document.getElementById('velocityMinOrders').value)
    };
    
    showVelocityProgress('Calculating SKU velocities...');
    
    fetch('/api/velocity/calculate-sku-velocities', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            db_config: dbConfig,
            parameters: parameters
        })
    })
    .then(response => response.json())
    .then(data => {
        hideVelocityProgress();
        
        const resultsDiv = document.getElementById('velocityResults');
        
        if (data.success) {
            const stats = data.statistics;
            resultsDiv.innerHTML = `
                <div class="alert alert-success">
                    <h6><i class="fas fa-check-circle me-2"></i>SKU Velocities Calculated Successfully!</h6>
                    <div class="row mt-3">
                        <div class="col-md-3">
                            <div class="text-center">
                                <h4 class="text-success">${stats.high_velocity}</h4>
                                <small>High Velocity (3)</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <h4 class="text-warning">${stats.medium_velocity}</h4>
                                <small>Medium Velocity (2)</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <h4 class="text-info">${stats.low_velocity}</h4>
                                <small>Low Velocity (1)</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <h4 class="text-primary">${stats.total_skus}</h4>
                                <small>Total SKUs</small>
                            </div>
                        </div>
                    </div>
                    <small class="text-muted">Calculation Date: ${data.calculation_date}</small>
                </div>
            `;
        } else {
            resultsDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>SKU Velocity Calculation Failed!</strong><br>
                    ${data.message}
                </div>
            `;
        }
    })
    .catch(error => {
        hideVelocityProgress();
        console.error('Error:', error);
        document.getElementById('velocityResults').innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Calculation Error!</strong><br>
                ${error.message}
            </div>
        `;
    });
}

function calculateBinVelocities() {
    const dbConfig = getVelocityDbConfig();
    const calculationDate = document.getElementById('binCalculationDate').value;
    
    showVelocityProgress('Calculating bin velocity scores...');
    
    fetch('/api/velocity/calculate-bin-velocities', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            db_config: dbConfig,
            calculation_date: calculationDate
        })
    })
    .then(response => response.json())
    .then(data => {
        hideVelocityProgress();
        
        const resultsDiv = document.getElementById('velocityResults');
        
        if (data.success) {
            const stats = data.statistics;
            resultsDiv.innerHTML = `
                <div class="alert alert-success">
                    <h6><i class="fas fa-check-circle me-2"></i>Bin Velocities Calculated Successfully!</h6>
                    <div class="row mt-3">
                        <div class="col-md-2">
                            <div class="text-center">
                                <h4 class="text-danger">${stats.high_priority_bins}</h4>
                                <small>High Priority</small>
                            </div>
                        </div>
                        <div class="col-md-2">
                            <div class="text-center">
                                <h4 class="text-warning">${stats.medium_priority_bins}</h4>
                                <small>Medium Priority</small>
                            </div>
                        </div>
                        <div class="col-md-2">
                            <div class="text-center">
                                <h4 class="text-info">${stats.low_priority_bins}</h4>
                                <small>Low Priority</small>
                            </div>
                        </div>
                        <div class="col-md-2">
                            <div class="text-center">
                                <h4 class="text-primary">${stats.total_bins}</h4>
                                <small>Total Bins</small>
                            </div>
                        </div>
                        <div class="col-md-2">
                            <div class="text-center">
                                <h4 class="text-success">${stats.average_composite_score}</h4>
                                <small>Avg Score</small>
                            </div>
                        </div>
                        <div class="col-md-2">
                            <div class="text-center">
                                <h4 class="text-secondary">${stats.average_utilization}%</h4>
                                <small>Avg Utilization</small>
                            </div>
                        </div>
                    </div>
                    <small class="text-muted">Calculation Date: ${data.calculation_date}</small>
                </div>
            `;
        } else {
            resultsDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Bin Velocity Calculation Failed!</strong><br>
                    ${data.message}
                </div>
            `;
        }
    })
    .catch(error => {
        hideVelocityProgress();
        console.error('Error:', error);
        document.getElementById('velocityResults').innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Calculation Error!</strong><br>
                ${error.message}
            </div>
        `;
    });
}

function runWeeklyAnalysis() {
    const dbConfig = getVelocityDbConfig();
    const forceRun = document.getElementById('forceWeeklyRun').checked;
    
    showVelocityProgress('Running weekly velocity analysis...');
    
    fetch('/api/velocity/run-weekly-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            db_config: dbConfig,
            force_run: forceRun
        })
    })
    .then(response => response.json())
    .then(data => {
        hideVelocityProgress();
        
        const resultsDiv = document.getElementById('velocityResults');
        
        if (data.overall_success) {
            resultsDiv.innerHTML = `
                <div class="alert alert-success">
                    <h6><i class="fas fa-check-circle me-2"></i>Weekly Analysis Completed Successfully!</h6>
                    <div class="row mt-3">
                        <div class="col-md-6">
                            <h7>SKU Analysis Results:</h7>
                            <ul class="list-unstyled mt-2">
                                <li><strong>High Velocity:</strong> ${data.sku_analysis.statistics.high_velocity} SKUs</li>
                                <li><strong>Medium Velocity:</strong> ${data.sku_analysis.statistics.medium_velocity} SKUs</li>
                                <li><strong>Low Velocity:</strong> ${data.sku_analysis.statistics.low_velocity} SKUs</li>
                                <li><strong>Total:</strong> ${data.sku_analysis.statistics.total_skus} SKUs</li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h7>Bin Analysis Results:</h7>
                            <ul class="list-unstyled mt-2">
                                <li><strong>High Priority:</strong> ${data.bin_analysis.statistics.high_priority_bins} bins</li>
                                <li><strong>Medium Priority:</strong> ${data.bin_analysis.statistics.medium_priority_bins} bins</li>
                                <li><strong>Low Priority:</strong> ${data.bin_analysis.statistics.low_priority_bins} bins</li>
                                <li><strong>Total:</strong> ${data.bin_analysis.statistics.total_bins} bins</li>
                            </ul>
                        </div>
                    </div>
                    <small class="text-muted">
                        Job ID: ${data.job_id} | Duration: ${data.duration} seconds
                    </small>
                </div>
            `;
        } else {
            resultsDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Weekly Analysis Failed!</strong><br>
                    ${data.error || 'Unknown error occurred'}
                </div>
            `;
        }
    })
    .catch(error => {
        hideVelocityProgress();
        console.error('Error:', error);
        document.getElementById('velocityResults').innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Analysis Error!</strong><br>
                ${error.message}
            </div>
        `;
    });
}

function loadVelocityData(dataType) {
    const dbConfig = getVelocityDbConfig();
    
    showVelocityProgress('Loading velocity data...');
    
    fetch('/api/velocity/get-velocity-data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            db_config: dbConfig,
            data_type: dataType,
            limit: 50
        })
    })
    .then(response => response.json())
    .then(data => {
        hideVelocityProgress();
        
        const resultsDiv = document.getElementById('velocityResults');
        
        if (data.success) {
            let resultsHtml = '';
            
            if (dataType === 'sku_velocities' || dataType === 'both') {
                if (data.data.sku_velocities.length > 0) {
                    resultsHtml += `
                        <h6><i class="fas fa-box me-2"></i>SKU Velocities (Latest ${data.data.sku_velocities.length} records)</h6>
                        <div class="table-responsive">
                            <table class="table table-striped table-sm">
                                <thead>
                                    <tr>
                                        <th>SKU Code</th>
                                        <th>Velocity</th>
                                        <th>Category</th>
                                        <th>Order Frequency</th>
                                        <th>Total Orders</th>
                                        <th>Weighted Score</th>
                                        <th>Date</th>
                                    </tr>
                                </thead>
                                <tbody>
                    `;
                    
                    data.data.sku_velocities.forEach(row => {
                        const velocityBadge = row.velocity_score === 3 ? 'badge-success' : 
                                            row.velocity_score === 2 ? 'badge-warning' : 'badge-info';
                        resultsHtml += `
                            <tr>
                                <td><code>${row.sku_code}</code></td>
                                <td><span class="badge ${velocityBadge}">${row.velocity_score}</span></td>
                                <td>${row.velocity_category}</td>
                                <td>${row.order_frequency}</td>
                                <td>${row.total_orders}</td>
                                <td>${row.weighted_score}</td>
                                <td>${row.calculated_date}</td>
                            </tr>
                        `;
                    });
                    
                    resultsHtml += '</tbody></table></div><hr>';
                }
            }
            
            if (dataType === 'bin_velocities' || dataType === 'both') {
                if (data.data.bin_velocities.length > 0) {
                    resultsHtml += `
                        <h6><i class="fas fa-archive me-2"></i>Bin Velocity Scores (Latest ${data.data.bin_velocities.length} records)</h6>
                        <div class="table-responsive">
                            <table class="table table-striped table-sm">
                                <thead>
                                    <tr>
                                        <th>Bin ID</th>
                                        <th>Composite Score</th>
                                        <th>SKU Count</th>
                                        <th>Capacity</th>
                                        <th>Utilization</th>
                                        <th>Priority</th>
                                        <th>Zone</th>
                                        <th>Recommendation</th>
                                    </tr>
                                </thead>
                                <tbody>
                    `;
                    
                    data.data.bin_velocities.forEach(row => {
                        const priorityBadge = row.priority_score >= 8 ? 'badge-danger' : 
                                            row.priority_score >= 5 ? 'badge-warning' : 'badge-info';
                        resultsHtml += `
                            <tr>
                                <td><code>${row.bin_id}</code></td>
                                <td><strong>${row.composite_velocity_score}</strong></td>
                                <td>${row.sku_count}/${row.bin_capacity}</td>
                                <td>${row.bin_capacity}</td>
                                <td>${row.capacity_utilization}%</td>
                                <td><span class="badge ${priorityBadge}">${row.priority_score}</span></td>
                                <td>${row.zone || 'N/A'}</td>
                                <td><small>${row.optimization_recommendation}</small></td>
                            </tr>
                        `;
                    });
                    
                    resultsHtml += '</tbody></table></div>';
                }
            }
            
            if (!resultsHtml) {
                resultsHtml = `
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>
                        No ${dataType.replace('_', ' ')} data found. Run analysis first.
                    </div>
                `;
            }
            
            resultsDiv.innerHTML = resultsHtml;
        } else {
            resultsDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Data Loading Failed!</strong><br>
                    ${data.message}
                </div>
            `;
        }
    })
    .catch(error => {
        hideVelocityProgress();
        console.error('Error:', error);
        document.getElementById('velocityResults').innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Loading Error!</strong><br>
                ${error.message}
            </div>
        `;
    });
}

function exportVelocityData() {
    const dbConfig = getVelocityDbConfig();
    
    // Show export options modal
    const exportOptions = confirm("Export SKU Velocities? (OK) or Bin Velocities? (Cancel)");
    const dataType = exportOptions ? 'sku_velocities' : 'bin_velocities';
    
    showVelocityProgress('Exporting velocity data...');
    
    fetch('/api/velocity/export-velocity-data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            db_config: dbConfig,
            data_type: dataType,
            format: 'csv'
        })
    })
    .then(response => {
        hideVelocityProgress();
        
        if (response.headers.get('content-type').includes('text/csv')) {
            // Download CSV file
            response.blob().then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${dataType}_${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            });
        } else {
            response.json().then(data => {
                if (!data.success) {
                    alert('Export failed: ' + data.message);
                }
            });
        }
    })
    .catch(error => {
        hideVelocityProgress();
        console.error('Error:', error);
        alert('Export error: ' + error.message);
    });
}

// Show velocity analysis section
function showVelocityAnalysis() {
    document.getElementById('velocityAnalysisSection').style.display = 'block';
    
    // Scroll to the section
    document.getElementById('velocityAnalysisSection').scrollIntoView({ 
        behavior: 'smooth', 
        block: 'start' 
    });
}
</script>

<style>
.velocity-analysis-section .card {
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.velocity-analysis-section .status-indicator {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 8px;
}

.velocity-analysis-section .status-connected {
    background-color: #28a745;
}

.velocity-analysis-section .status-disconnected {
    background-color: #dc3545;
}

.velocity-analysis-section .badge-success {
    background-color: #28a745;
}

.velocity-analysis-section .badge-warning {
    background-color: #ffc107;
    color: #212529;
}

.velocity-analysis-section .badge-info {
    background-color: #17a2b8;
}

.velocity-analysis-section .badge-danger {
    background-color: #dc3545;
}

.velocity-analysis-section .table-sm td {
    padding: 0.3rem;
    font-size: 0.875rem;
}

.velocity-analysis-section .alert-sm {
    padding: 0.5rem 0.75rem;
    font-size: 0.875rem;
}
</style>
'''

def get_velocity_analysis_section():
    """Return the velocity analysis HTML section"""
    return VELOCITY_ANALYSIS_HTML