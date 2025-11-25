# 🚀 Service Setup Guide
## Association Mining System - Windows Service & Database Configuration

This document covers two major features:
1. **Primary Keys in All Database Tables**
2. **Windows Service for Background Execution**

---

## 📊 Feature 1: Primary Keys in All Database Tables

### Overview
All tables created by the Association Mining System now have proper primary keys to ensure data integrity, improve query performance, and support proper database relationships.

### Tables with Primary Keys

#### 1. **Scheduler Tables**

**mining_schedules**
```sql
CREATE TABLE mining_schedules (
    id INT AUTO_INCREMENT PRIMARY KEY,  -- ✅ Auto-incrementing primary key
    job_name VARCHAR(255) NOT NULL,
    schedule_type ENUM('daily', 'weekly') NOT NULL,
    schedule_time TIME NOT NULL,
    -- ... other fields
    UNIQUE KEY unique_job_name (job_name)
)
```

**mining_job_logs**
```sql
CREATE TABLE mining_job_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,  -- ✅ Auto-incrementing primary key
    schedule_id INT NOT NULL,
    job_name VARCHAR(255) NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- ... other fields
    FOREIGN KEY (schedule_id) REFERENCES mining_schedules(id) ON DELETE CASCADE
)
```

**mining_schedule_stats**
```sql
CREATE TABLE mining_schedule_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,  -- ✅ Auto-incrementing primary key
    schedule_id INT NOT NULL,
    total_executions INT DEFAULT 0,
    -- ... other fields
    FOREIGN KEY (schedule_id) REFERENCES mining_schedules(id) ON DELETE CASCADE
)
```

#### 2. **Recommendation Tables**

**my_recommendation & sku_recommendations**
```sql
CREATE TABLE my_recommendation (
    SCORE_ID BIGINT NOT NULL AUTO_INCREMENT,
    PARENT_ARTICLE_ID VARCHAR(200) NOT NULL,
    CHILD_ARTICLE_ID VARCHAR(200) NOT NULL,
    PROXIMITY_SCORE DECIMAL(10,3) NULL,
    PRIMARY KEY (PARENT_ARTICLE_ID, CHILD_ARTICLE_ID),  -- ✅ Composite primary key
    KEY SCORE_ID_INDEX (SCORE_ID)
)
```

**Benefits:**
- Composite primary key ensures unique product pair combinations
- Auto-increment SCORE_ID for easy sequential access
- Indexed for fast lookups and joins

### Why Primary Keys Matter

✅ **Data Integrity**: Prevents duplicate records  
✅ **Performance**: Automatically indexed for faster queries  
✅ **Relationships**: Enables foreign key constraints  
✅ **Updates & Deletes**: Efficient row-level operations  
✅ **Replication**: Required for database replication  

---

## 🔧 Feature 2: Windows Service for Background Execution

### Overview
Run the Association Mining System as a Windows background service that:
- Starts automatically with Windows
- Runs without user login
- Auto-restarts if crashes
- Monitors and manages FastAPI + Flask servers
- Logs all activity to `logs/service.log`

### Files Created

```
association_mining_system/
├── windows_service.py          # Python service implementation
├── install_service.bat         # Install the Windows service
├── start_service.bat           # Start the service
├── stop_service.bat            # Stop the service  
├── uninstall_service.bat       # Remove the service
├── check_service.bat           # Check service status
└── logs/
    └── service.log             # Service activity log
```

---

## 📦 Installation

### Prerequisites

1. **Administrator Access Required**
   - All service operations need admin privileges
   - Right-click batch files → "Run as administrator"

2. **Python Requirements**
   ```bash
   pip install pywin32
   ```
   This package is required for Windows service integration.

### Step-by-Step Installation

#### Step 1: Install the Service

1. Right-click `install_service.bat` → **Run as administrator**

The script will:
- ✅ Check for admin privileges
- ✅ Activate virtual environment
- ✅ Install `pywin32` if missing
- ✅ Register the Windows service

**Expected Output:**
```
========================================
Installing Association Mining Service
========================================

Running with administrator privileges...
Activating virtual environment...
Installing service...

========================================
Service Installed Successfully!
========================================

Service Name: AssociationMiningService
Display Name: Association Mining System Service

To start the service, run: start_service.bat
```

#### Step 2: Start the Service

1. Right-click `start_service.bat` → **Run as administrator**

The service will:
- ✅ Start FastAPI on port 8080
- ✅ Start Flask UI on port 5000
- ✅ Enable auto-restart on failure
- ✅ Log all activity

**Expected Output:**
```
========================================
Service Started Successfully!
========================================

The Association Mining System is now running in background

  FastAPI Server:  http://localhost:8080
  Flask UI:        http://localhost:5000
  API Docs:        http://localhost:8080/docs
```

---

## 🎮 Service Management

### Check Service Status
```cmd
check_service.bat
```
OR use Windows Services Manager:
```cmd
services.msc
```
Look for "Association Mining System Service"

### Stop the Service
```cmd
stop_service.bat  (Run as admin)
```

### Restart the Service
```cmd
stop_service.bat  (Run as admin)
start_service.bat (Run as admin)
```

### Uninstall the Service
```cmd
uninstall_service.bat  (Run as admin)
```

---

## 🔍 Monitoring & Logs

### View Service Logs
```
logs/service.log
```

**Log Contents:**
- Service start/stop events
- Server process IDs
- Error messages and stack traces
- Auto-restart notifications
- Performance metrics

**Example Log:**
```
2025-11-25 10:30:15 - INFO - ============================================================
2025-11-25 10:30:15 - INFO - Association Mining Service Starting
2025-11-25 10:30:15 - INFO - ============================================================
2025-11-25 10:30:15 - INFO - Starting FastAPI server on port 8080...
2025-11-25 10:30:15 - INFO - ✓ FastAPI server started (PID: 12345)
2025-11-25 10:30:18 - INFO - Starting Flask UI server on port 5000...
2025-11-25 10:30:18 - INFO - ✓ Flask UI server started (PID: 12346)
2025-11-25 10:30:18 - INFO - ============================================================
2025-11-25 10:30:18 - INFO - All servers started successfully!
```

### Monitor via Windows Event Viewer
1. Open Event Viewer: `eventvwr.msc`
2. Navigate to: **Windows Logs → Application**
3. Filter by Source: **Python Service**

---

## ⚙️ Service Configuration

### Configure Auto-Start

**Option 1: Services Manager (GUI)**
1. Open `services.msc`
2. Find "Association Mining System Service"
3. Right-click → Properties
4. Startup type: **Automatic**
5. Click OK

**Option 2: Command Line**
```cmd
sc config AssociationMiningService start= auto
```

### Change Service Recovery Options
1. Open `services.msc`
2. Find service → Properties → Recovery tab
3. Configure:
   - First failure: **Restart the Service**
   - Second failure: **Restart the Service**
   - Subsequent failures: **Restart the Service**
   - Restart service after: **1 minute**

---

## 🚨 Troubleshooting

### Service Won't Install

**Problem:** "Access Denied" or permission errors

**Solution:**
- Run `install_service.bat` as Administrator
- Disable antivirus temporarily
- Check Python and pywin32 are installed:
  ```cmd
  python -c "import win32serviceutil"
  ```

### Service Won't Start

**Problem:** Service starts then immediately stops

**Possible Causes:**
1. **Port already in use** (8080 or 5000)
   ```cmd
   netstat -ano | findstr :8080
   netstat -ano | findstr :5000
   ```
   Kill conflicting process or change ports

2. **Missing dependencies**
   ```cmd
   pip install -r requirements.txt
   ```

3. **Database connection issues**
   - Check `.env` file configuration
   - Verify database is running
   - Test connection: `python utils/database/check_table.py`

4. **Check logs**
   ```
   logs/service.log
   ```

### Service Crashes Repeatedly

**Problem:** Service keeps restarting

**Solution:**
1. Check `logs/service.log` for errors
2. Verify all dependencies installed
3. Test manual startup:
   ```cmd
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
   python -m flask --app app.web.main:app run
   ```
4. Fix any errors, then restart service

### Can't Access Web UI

**Problem:** Cannot reach http://localhost:5000

**Solution:**
1. Check service is running: `check_service.bat`
2. Check firewall settings
3. Try http://127.0.0.1:5000
4. Check if port is listening:
   ```cmd
   netstat -ano | findstr :5000
   ```

---

## 📋 Service Details

| Property | Value |
|----------|-------|
| **Service Name** | AssociationMiningService |
| **Display Name** | Association Mining System Service |
| **Description** | Runs the Association Mining System FastAPI server and scheduler in background |
| **Startup Type** | Manual (change to Automatic for auto-start) |
| **Log File** | logs/service.log |
| **FastAPI Port** | 8080 |
| **Flask Port** | 5000 |

---

## 🔐 Security Considerations

### Running as Service

⚠️ **Important:**
- Service runs under **Local System** account by default
- Has full system access
- Consider creating dedicated service account:
  1. Create user: `serviceaccount`
  2. Grant permissions to project folder
  3. Configure service to use this account

### Network Access

- Service binds to `0.0.0.0` (all interfaces)
- Accessible from network if firewall allows
- For production:
  - Use reverse proxy (nginx, IIS)
  - Enable HTTPS
  - Configure authentication

---

## 📊 Performance Monitoring

### Check Resource Usage

**Using Task Manager:**
1. Open Task Manager (Ctrl+Shift+Esc)
2. Details tab
3. Find `python.exe` processes
4. Monitor CPU, Memory, Disk usage

**Using Performance Monitor:**
```cmd
perfmon
```

### Set Resource Limits

Modify `windows_service.py` to add:
```python
# Limit memory per process (example)
import resource
resource.setrlimit(resource.RLIMIT_AS, (2*1024*1024*1024, -1))  # 2GB limit
```

---

## 🔄 Updates & Maintenance

### Update Service After Code Changes

1. Stop the service:
   ```cmd
   stop_service.bat
   ```

2. Pull code changes / update files

3. Restart the service:
   ```cmd
   start_service.bat
   ```

### Reinstall Service (Clean Install)

1. Uninstall:
   ```cmd
   uninstall_service.bat
   ```

2. Reinstall:
   ```cmd
   install_service.bat
   ```

3. Start:
   ```cmd
   start_service.bat
   ```

---

## 🎯 Quick Reference

### Common Commands

```cmd
# Install service (as admin)
install_service.bat

# Start service (as admin)
start_service.bat

# Stop service (as admin)
stop_service.bat

# Check status
check_service.bat

# Uninstall service (as admin)
uninstall_service.bat

# View logs
notepad logs\service.log

# Check if ports are in use
netstat -ano | findstr :8080
netstat -ano | findstr :5000
```

### Access URLs

- **Flask UI:** http://localhost:5000
- **FastAPI:** http://localhost:8080
- **API Docs:** http://localhost:8080/docs
- **Scheduler UI:** http://localhost:5000/velocity-analysis

---

## ✅ Verification Checklist

After installation, verify:

- [ ] Service installed: `sc query AssociationMiningService`
- [ ] Service running: `check_service.bat`
- [ ] FastAPI accessible: http://localhost:8080/docs
- [ ] Flask UI accessible: http://localhost:5000
- [ ] Logs being written: `logs/service.log` exists
- [ ] Scheduler working: Create test schedule
- [ ] Database connected: Run test query
- [ ] Auto-restart works: Kill process, check if restarts

---

## 📞 Support

**Issues?**
1. Check `logs/service.log`
2. Review troubleshooting section
3. Verify all prerequisites
4. Test manual startup before service

**Database Issues?**
- Run: `python utils/setup/database_setup_checker.py`
- Check `.env` configuration
- Verify MySQL/database is running

---

## 🎉 Summary

### Primary Keys ✅
- All tables have proper primary keys
- Composite keys for relationship tables
- Auto-increment IDs for sequential tables
- Foreign key constraints enforced

### Windows Service ✅
- Background execution without user login
- Auto-start with Windows (configurable)
- Auto-restart on crashes
- Comprehensive logging
- Easy management with batch scripts

**You're all set!** The Association Mining System is now enterprise-ready with proper database integrity and background service capabilities. 🚀
