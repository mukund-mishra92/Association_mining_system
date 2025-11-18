# SQL Query Fix Summary - Maintenance Tasks

**Date:** 2025-11-12  
**Issue:** Column name error in maintenance task query  
**Status:** ✅ Fixed and Documented

---

## The Problem

**User Question:**
> "I need to find out the bots involved and task id for which the bots have assigned the task but not able to complete it. need to add the date as well"

**Chatbot Generated (INCORRECT):**
```sql
SELECT dlm.BOT_ID, dlm.MAINTENANCE_TASK_ID, dlm.INSERTED_TIMESTAMP
FROM dashboard_log_maintenance_task_master dlm
WHERE dlm.TASK_DONE = 0
ORDER BY dlm.INSERTED_TIMESTAMP DESC
LIMIT 100;
```

**Error:**
```
pymysql.err.OperationalError: (1054, "Unknown column 'dlm.BOT_ID' in 'field list'")
```

---

## Root Cause

The table `dashboard_log_maintenance_task_master` does **NOT** have a column named `BOT_ID`.

**Actual Column Names:**
- ✅ `MAINTENANCE_POINT_BOT_ID` (varchar 100) - Primary bot assigned to task
- ✅ `MAINTENANCE_PICK_POINT_BOT_ID` (varchar 100) - Secondary bot (if needed)
- ❌ `BOT_ID` - **Does not exist!**

---

## The Fix

**Corrected Query:**
```sql
SELECT 
    MAINTENANCE_POINT_BOT_ID AS bot_id,
    MAINTENANCE_TASK_ID AS task_id,
    INSERTED_TIMESTAMP AS task_assigned_date,
    TASK_DONE,
    MAINTENANCE_ID
FROM dashboard_log_maintenance_task_master
WHERE TASK_DONE = 0  -- 0 = incomplete, 1 = complete
ORDER BY INSERTED_TIMESTAMP DESC
LIMIT 100;
```

**Result:** ✅ Query executes successfully (returns 0 rows currently, meaning no incomplete tasks)

---

## Full Table Structure

**Table:** `dashboard_log_maintenance_task_master`

| Column Name | Type | Notes |
|-------------|------|-------|
| `MAINTENANCE_TASK_ID` | bigint | Primary key, unique task identifier |
| `MAINTENANCE_ID` | int | References maintenance configuration |
| `MAINTENANCE_POINT_BOT_ID` | varchar(100) | ⚠️ **PRIMARY bot** (use this!) |
| `MAINTENANCE_PICK_POINT_BOT_ID` | varchar(100) | Secondary bot if needed |
| `BIN_BARCODE_SCANNED` | varchar(50) | Bin involved in maintenance |
| `MAINTENANCE_POINT_BARCODE_SCANNED` | tinyint(1) | Whether barcode was scanned |
| `IS_MP_BOT_HEALTHY` | tinyint(1) | Bot health status (0/1) |
| `TASK_DONE` | tinyint(1) | **0 = incomplete, 1 = complete** |
| `INSERTED_TIMESTAMP` | datetime(3) | When task was assigned |
| `UPDATED_TIMESTAMP` | datetime(3) | Last update time |
| `LOGGED_TIMESTAMP` | datetime(3) | When logged to this table |

---

## Documentation Updates

To prevent this error from happening again, I've updated:

### 1. ✅ `quick_reference.md`
- Added Template 5: Maintenance Tasks with correct column names
- Added to "Common Mistakes" section:
  - ❌ `dashboard_log_maintenance_task_master.BOT_ID` → ✅ `MAINTENANCE_POINT_BOT_ID`
- Highlighted that `TASK_DONE`: 0 = incomplete, 1 = complete

### 2. ✅ `schema_guide.md`
- Added Section 7: "Bot Maintenance Tasks"
- Documented full table structure
- Provided 3 example queries:
  - Incomplete tasks by bot
  - Count incomplete tasks per bot
  - Maintenance task completion rate over time
- Added warning about column name

### 3. ✅ `sql_assistant_service.py` (System Prompt)
- Added Section 5: BOT MAINTENANCE TASKS to CRITICAL TABLE RELATIONSHIPS
- Added example query to EXAMPLE QUERIES section
- Added Rule 7: "For maintenance tasks: Use MAINTENANCE_POINT_BOT_ID, NOT BOT_ID"

### 4. ✅ `CHANGELOG.md`
- Documented the error, root cause, fix, and all updates
- Included full table structure for future reference

---

## Useful Query Patterns

### Find incomplete tasks with bot details:
```sql
SELECT 
    MAINTENANCE_POINT_BOT_ID AS bot_id,
    MAINTENANCE_TASK_ID AS task_id,
    INSERTED_TIMESTAMP AS assigned_date,
    MAINTENANCE_ID,
    BIN_BARCODE_SCANNED,
    IS_MP_BOT_HEALTHY
FROM dashboard_log_maintenance_task_master
WHERE TASK_DONE = 0
ORDER BY INSERTED_TIMESTAMP DESC
LIMIT 100;
```

### Count incomplete tasks per bot:
```sql
SELECT 
    MAINTENANCE_POINT_BOT_ID AS bot_id,
    COUNT(*) AS incomplete_tasks,
    MIN(INSERTED_TIMESTAMP) AS oldest_task,
    MAX(INSERTED_TIMESTAMP) AS newest_task
FROM dashboard_log_maintenance_task_master
WHERE TASK_DONE = 0
GROUP BY MAINTENANCE_POINT_BOT_ID
ORDER BY incomplete_tasks DESC;
```

### Maintenance completion rate (last 7 days):
```sql
SELECT 
    DATE(INSERTED_TIMESTAMP) AS task_date,
    COUNT(*) AS total_tasks,
    SUM(TASK_DONE) AS completed_tasks,
    ROUND(SUM(TASK_DONE) * 100.0 / COUNT(*), 2) AS completion_rate
FROM dashboard_log_maintenance_task_master
WHERE INSERTED_TIMESTAMP >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY DATE(INSERTED_TIMESTAMP)
ORDER BY task_date DESC;
```

### Tasks for a specific bot:
```sql
SELECT 
    MAINTENANCE_TASK_ID,
    TASK_DONE,
    INSERTED_TIMESTAMP,
    BIN_BARCODE_SCANNED,
    IS_MP_BOT_HEALTHY
FROM dashboard_log_maintenance_task_master
WHERE MAINTENANCE_POINT_BOT_ID = 'BOT_123'
ORDER BY INSERTED_TIMESTAMP DESC
LIMIT 50;
```

---

## Testing Verification

✅ **Query tested successfully on actual database**
- Connects to MySQL neo database
- Executes without errors
- Returns proper result set (currently 0 rows, meaning no incomplete tasks)

✅ **Column names verified**
- Used `DESCRIBE dashboard_log_maintenance_task_master`
- Confirmed exact column names and data types
- Documented all 11 columns

✅ **Documentation updated**
- All 4 documentation files updated
- System prompt includes new pattern
- Common mistakes section updated

---

## Next Steps

When the chatbot encounters this question again, it should now:
1. Use the correct column name `MAINTENANCE_POINT_BOT_ID`
2. Include proper date field `INSERTED_TIMESTAMP`
3. Filter by `TASK_DONE = 0` for incomplete tasks
4. Return results ordered by date (newest first)

The feedback system will track positive responses and automatically add this pattern to the quick reference if users confirm it works well!

---

## Files Modified

1. `app/modules/neo_chatbot/data/database/quick_reference.md`
2. `app/modules/neo_chatbot/data/database/schema_guide.md`
3. `app/modules/neo_chatbot/data/database/CHANGELOG.md`
4. `app/modules/neo_chatbot/services/sql_assistant_service.py`
5. `QUERY_FIX_SUMMARY.md` (this file)
