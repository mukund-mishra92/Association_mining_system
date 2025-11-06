# 🚀 Bin Velocity Analysis System - Complete Setup & Execution Guide

## 📋 System Overview
The Bin Velocity Analysis System calculates SKU velocities (1=Low, 2=Medium, 3=High) based on order patterns and provides bin-level velocity recommendations for warehouse optimization.

## ✅ Prerequisites Checklist

### 1. Database Requirements
- ✅ MySQL database running and accessible
- ✅ Required tables exist:
  - `sku_master` (with SKU_ID, VELOCITY columns)
  - `wms_to_wcs_order_line_request_data` (with ARTICLE_ID, INSERTED_TIMESTAMP)
  - `velocity_calculation_config`
  - `sku_velocity_history`
  - `bin_configuration`
  - `bin_velocity_scores`

### 2. Python Environment
- ✅ Python 3.8+ installed
- ✅ Virtual environment activated
- ✅ Required packages installed

---

## 🔧 Step 1: Environment Setup

### Activate Virtual Environment
```bash
# Navigate to project directory
cd C:\Users\Balmukund.Mishra\Desktop\NEO\association_mining_system

# Activate virtual environment
.\venv\Scripts\activate
```

### Verify Required Packages
```bash
pip install -r requirements.txt
```

---

## 🗄️ Step 2: Database Configuration

### Check Database Connection
```python
# Test database connectivity
python -c "
from app.shared.config.config import Config
config = Config()
print(f'Database: {config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}')
print(f'User: {config.DB_USER}')
"
```

### Verify Required Tables
```python
# Run table verification
python -c "
import sys
sys.path.insert(0, '.')
from app.modules.velocity_analysis.services.velocity_service import VelocityAnalysisService
from app.shared.config.config import Config

config = Config()
db_config = {
    'host': config.DB_HOST,
    'port': config.DB_PORT,
    'user': config.DB_USER,
    'password': config.DB_PASSWORD,
    'database': config.DB_NAME
}

service = VelocityAnalysisService(db_config)
service.connect_database()

# Check required tables
tables = ['sku_master', 'wms_to_wcs_order_line_request_data', 'velocity_calculation_config']
cursor = service.connection.cursor()

for table in tables:
    cursor.execute(f'SELECT COUNT(*) FROM {table}')
    count = cursor.fetchone()[0]
    print(f'✅ {table}: {count:,} records')

cursor.close()
service.disconnect_database()
"
```

---

## ⚙️ Step 3: Configuration Setup

### Check/Update Velocity Calculation Parameters
```python
# View current configuration
python -c "
import sys
sys.path.insert(0, '.')
from app.modules.velocity_analysis.services.velocity_service import VelocityAnalysisService
from app.shared.config.config import Config

config = Config()
db_config = {
    'host': config.DB_HOST,
    'port': config.DB_PORT,
    'user': config.DB_USER,
    'password': config.DB_PASSWORD,
    'database': config.DB_NAME
}

service = VelocityAnalysisService(db_config)
service.connect_database()
params = service.get_calculation_parameters()
print('Current Velocity Calculation Parameters:')
for key, value in params.items():
    print(f'  {key}: {value}')
service.disconnect_database()
"
```

### Default Configuration Values
- `time_decay_rate`: 0.05 (5% decay per day)
- `high_velocity_threshold`: 0.8 (80th percentile)
- `medium_velocity_threshold`: 0.5 (50th percentile)
- `analysis_period_days`: 90 (3 months)
- `min_orders_for_calculation`: 5 (minimum orders to qualify)

---

## 🚀 Step 4: Running the Velocity Analysis

### Method 1: Direct Python Execution

#### A. Run SKU Velocity Analysis
```python
# Execute SKU velocity calculation
python -c "
import sys
sys.path.insert(0, '.')
from app.modules.velocity_analysis.services.velocity_service import VelocityAnalysisService
from app.shared.config.config import Config

config = Config()
db_config = {
    'host': config.DB_HOST,
    'port': config.DB_PORT,
    'user': config.DB_USER,
    'password': config.DB_PASSWORD,
    'database': config.DB_NAME
}

print('🔄 Starting SKU Velocity Analysis...')
service = VelocityAnalysisService(db_config)
service.connect_database()

result = service.calculate_sku_velocities()
if result['success']:
    stats = result['statistics']
    print('✅ SKU Velocity Analysis Completed!')
    print(f'   📊 Total SKUs Updated: {stats[\"total_skus_updated\"]}')
    print(f'   🔴 High Velocity (3): {stats[\"high_velocity\"]} SKUs')
    print(f'   🟡 Medium Velocity (2): {stats[\"medium_velocity\"]} SKUs')
    print(f'   🟢 Low Velocity (1): {stats[\"low_velocity\"]} SKUs')
else:
    print(f'❌ Error: {result[\"message\"]}')

service.disconnect_database()
"
```

#### B. Run Bin Velocity Analysis (if bin_configuration data exists)
```python
# Execute bin velocity calculation
python -c "
import sys
sys.path.insert(0, '.')
from app.modules.velocity_analysis.services.velocity_service import VelocityAnalysisService
from app.shared.config.config import Config

config = Config()
db_config = {
    'host': config.DB_HOST,
    'port': config.DB_PORT,
    'user': config.DB_USER,
    'password': config.DB_PASSWORD,
    'database': config.DB_NAME
}

print('🔄 Starting Bin Velocity Analysis...')
service = VelocityAnalysisService(db_config)
service.connect_database()

result = service.calculate_bin_velocities()
if result['success']:
    print('✅ Bin Velocity Analysis Completed!')
    print(f'   📊 Analysis: {result.get(\"message\", \"Completed successfully\")}')
else:
    print(f'❌ Error: {result[\"message\"]}')

service.disconnect_database()
"
```

### Method 2: Using Test Script
```bash
# Run comprehensive test
python quick_velocity_test.py
```

### Method 3: Using Debug Scripts
```bash
# Test SKU velocity only
python debug_sku_velocity.py

# Test with detailed tracing
python debug_sku_trace.py
```

---

## 📊 Step 5: Verify Results

### Check Updated SKU Velocities
```python
python -c "
import sys
sys.path.insert(0, '.')
from app.modules.velocity_analysis.services.velocity_service import VelocityAnalysisService
from app.shared.config.config import Config

config = Config()
db_config = {
    'host': config.DB_HOST,
    'port': config.DB_PORT,
    'user': config.DB_USER,
    'password': config.DB_PASSWORD,
    'database': config.DB_NAME
}

service = VelocityAnalysisService(db_config)
service.connect_database()
cursor = service.connection.cursor()

# Check velocity distribution
cursor.execute('''
    SELECT VELOCITY, COUNT(*) as count 
    FROM sku_master 
    WHERE VELOCITY IS NOT NULL 
    GROUP BY VELOCITY 
    ORDER BY VELOCITY DESC
''')

print('📊 SKU Velocity Distribution:')
for row in cursor.fetchall():
    velocity_name = {3: 'High', 2: 'Medium', 1: 'Low'}.get(row[0], 'Unknown')
    print(f'   Velocity {row[0]} ({velocity_name}): {row[1]:,} SKUs')

cursor.close()
service.disconnect_database()
"
```

### Check Velocity History
```python
python -c "
import sys
sys.path.insert(0, '.')
from app.modules.velocity_analysis.services.velocity_service import VelocityAnalysisService
from app.shared.config.config import Config

config = Config()
db_config = {
    'host': config.DB_HOST,
    'port': config.DB_PORT,
    'user': config.DB_USER,
    'password': config.DB_PASSWORD,
    'database': config.DB_NAME
}

service = VelocityAnalysisService(db_config)
service.connect_database()
cursor = service.connection.cursor()

# Check recent velocity changes
cursor.execute('''
    SELECT COUNT(*) as total_changes,
           MAX(changed_at) as latest_change
    FROM sku_velocity_history 
    WHERE changed_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
''')

result = cursor.fetchone()
print(f'📈 Recent Velocity Changes: {result[0]} changes')
print(f'🕐 Latest Update: {result[1]}')

cursor.close()
service.disconnect_database()
"
```

---

## 🔄 Step 6: Automated Scheduling (Optional)

### Using Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., Weekly on Monday)
4. Set action to run Python script:
   - Program: `C:\Users\Balmukund.Mishra\Desktop\NEO\association_mining_system\venv\Scripts\python.exe`
   - Arguments: `debug_sku_velocity.py`
   - Start in: `C:\Users\Balmukund.Mishra\Desktop\NEO\association_mining_system`

### Using Python Scheduler (Alternative)
```python
# Create scheduled_velocity_analysis.py
import schedule
import time
import sys
sys.path.insert(0, '.')

from app.modules.velocity_analysis.services.velocity_service import VelocityAnalysisService
from app.shared.config.config import Config

def run_velocity_analysis():
    config = Config()
    db_config = {
        'host': config.DB_HOST,
        'port': config.DB_PORT,
        'user': config.DB_USER,
        'password': config.DB_PASSWORD,
        'database': config.DB_NAME
    }
    
    service = VelocityAnalysisService(db_config)
    service.connect_database()
    result = service.calculate_sku_velocities()
    service.disconnect_database()
    
    print(f"Velocity analysis completed: {result['success']}")

# Schedule every Monday at 9 AM
schedule.every().monday.at("09:00").do(run_velocity_analysis)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## 🔧 Step 7: Integration with Existing Systems

### API Integration (if needed)
The velocity service can be integrated with your existing API:

```python
# In your API endpoint
from app.modules.velocity_analysis.services.velocity_service import VelocityAnalysisService

@app.route('/api/velocity/calculate', methods=['POST'])
def calculate_velocities():
    service = VelocityAnalysisService(db_config)
    service.connect_database()
    result = service.calculate_sku_velocities()
    service.disconnect_database()
    return jsonify(result)
```

### Data Export (if needed)
```python
# Export velocity data to CSV
python -c "
import sys
import csv
sys.path.insert(0, '.')
from app.modules.velocity_analysis.services.velocity_service import VelocityAnalysisService
from app.shared.config.config import Config

config = Config()
db_config = {
    'host': config.DB_HOST,
    'port': config.DB_PORT,
    'user': config.DB_USER,
    'password': config.DB_PASSWORD,
    'database': config.DB_NAME
}

service = VelocityAnalysisService(db_config)
service.connect_database()
cursor = service.connection.cursor()

cursor.execute('''
    SELECT SKU_ID, VELOCITY, UPDATED_TIMESTAMP 
    FROM sku_master 
    WHERE VELOCITY IS NOT NULL 
    ORDER BY VELOCITY DESC, SKU_ID
''')

with open('sku_velocities.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['SKU_ID', 'VELOCITY', 'UPDATED_TIMESTAMP'])
    writer.writerows(cursor.fetchall())

print('✅ Velocity data exported to sku_velocities.csv')
cursor.close()
service.disconnect_database()
"
```

---

## 🚨 Troubleshooting

### Common Issues & Solutions

#### 1. Database Connection Error
```
Error: Can't connect to MySQL server
```
**Solution:** Check database credentials in config file and ensure MySQL is running.

#### 2. No SKUs Meet Minimum Threshold
```
Error: No SKUs meet minimum order criteria
```
**Solution:** Lower `min_orders_for_calculation` parameter or check order data date range.

#### 3. Trigger Definer Error
```
Error: The user specified as a definer does not exist
```
**Solution:** Run the trigger fix script: `python debug_fix_triggers.py`

#### 4. Column Not Found Error
```
Error: Unknown column 'sku_code' in 'field list'
```
**Solution:** Verify table structures match the expected schema.

### Debug Commands
```bash
# Test database connectivity
python debug_velocity_threshold.py

# Trace calculation step by step
python debug_sku_trace.py

# Fix trigger issues
python debug_fix_triggers.py
```

---

## 📈 Performance Optimization

### For Large Datasets
- Consider adding database indices on:
  - `wms_to_wcs_order_line_request_data.ARTICLE_ID`
  - `wms_to_wcs_order_line_request_data.INSERTED_TIMESTAMP`
  - `sku_master.VELOCITY`

### Monitoring
- Check velocity calculation logs in console output
- Monitor `sku_velocity_history` table for audit trail
- Track processing time for performance optimization

---

## 🎯 Expected Results

After successful execution, you should see:
- ✅ **609+ SKUs** with updated velocity scores
- ✅ **~20% High velocity (3)** SKUs
- ✅ **~30% Medium velocity (2)** SKUs  
- ✅ **~50% Low velocity (1)** SKUs
- ✅ **History records** in sku_velocity_history table
- ✅ **Updated timestamps** in sku_master table

---

## 📞 Support

If you encounter any issues:
1. Check the troubleshooting section above
2. Review database table structures
3. Verify configuration parameters
4. Run debug scripts for detailed error information

**System Status:** ✅ Ready for Production Use