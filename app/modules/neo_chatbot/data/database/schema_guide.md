# NEO Warehouse Management System - Database Schema Guide

## Purpose
This document helps the SQL Assistant understand complex table relationships, business logic, and common query patterns for the NEO WMS database.

---

## Core Table Relationships

### 1. Orders & SKUs
**Business Logic:** Track what items (SKUs) were ordered

**Tables:**
- `wms_to_wcs_order_line_request_data` - Main order line data
- `sku_master` - SKU/Article master data

**Key Columns:**
- `wms_to_wcs_order_line_request_data.ARTICLE_ID` → `sku_master.SKU_ID`
- Date field: `INSERTED_TIMESTAMP`

**Common Queries:**
```sql
-- Orders with SKU details
SELECT 
    ord.ORDER_ID,
    ord.ORDER_LINE_ID,
    sm.SKU_NAME,
    ord.QUANTITY,
    ord.INSERTED_TIMESTAMP
FROM wms_to_wcs_order_line_request_data ord
JOIN sku_master sm ON ord.ARTICLE_ID = sm.SKU_ID
WHERE ord.INSERTED_TIMESTAMP >= DATE_SUB(NOW(), INTERVAL 7 DAY);
```

---

### 2. Bins & Locations
**Business Logic:** Track physical bin locations and their configurations

**Tables:**
- `bin_info_master` - Bin metadata (BIN_ID is INT, primary key)
- `bin_configuration` - Bin location details (bin_id is VARCHAR)
- `order_bin_mapping` - Links orders to bins

**Key Columns:**
- `bin_info_master.BIN_ID` (INT) - Primary key
- `bin_info_master.BIN_BARCODE` (VARCHAR) - Links to bin_configuration
- `bin_configuration.bin_id` (VARCHAR) - Physical bin identifier
- `bin_configuration.bin_location` - Physical location (e.g., "Aisle-1-Rack-3")
- `bin_configuration.zone` - Zone identifier

**Important Notes:**
- ⚠️ `bin_info_master.BIN_ID` is INT
- ⚠️ `bin_configuration.bin_id` is VARCHAR
- Use `BIN_BARCODE` to link them

**Common Queries:**
```sql
-- Bins with location details
SELECT 
    bim.BIN_ID,
    bim.BIN_BARCODE,
    bc.bin_location,
    bc.zone,
    bc.current_sku_count
FROM bin_info_master bim
JOIN bin_configuration bc ON bim.BIN_BARCODE = bc.bin_id;
```

---

### 3. Orders → Bins (Multi-table JOIN)
**Business Logic:** Track which bins were used for which orders

**Table Chain:**
`order_bin_mapping` → `bin_info_master` → `bin_configuration`

**Join Path:**
1. `order_bin_mapping.BIN_ID` = `bin_info_master.BIN_ID` (INT to INT)
2. `bin_info_master.BIN_BARCODE` = `bin_configuration.bin_id` (VARCHAR to VARCHAR)

**Common Queries:**
```sql
-- Locations with most order activity
SELECT 
    bc.bin_location,
    bc.zone,
    COUNT(obm.ORDER_BIN_ID) AS order_count,
    COUNT(DISTINCT obm.BOT_ID) AS bot_count
FROM order_bin_mapping obm
JOIN bin_info_master bim ON obm.BIN_ID = bim.BIN_ID
JOIN bin_configuration bc ON bim.BIN_BARCODE = bc.bin_id
WHERE obm.INSERTED_TIMESTAMP >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY bc.bin_location, bc.zone
ORDER BY order_count DESC;
```

---

### 4. SKU Recommendations
**Business Logic:** Association mining results showing frequently ordered together items

**Tables:**
- `sku_recommendations` - Recommendation pairs

**Key Columns:**
- Columns vary, but typically: `source_sku`, `target_sku`, `support`, `confidence`, `lift`
- Check actual schema: May use different column names

**Common Queries:**
```sql
-- Top SKU recommendations
SELECT 
    source_sku,
    target_sku,
    confidence,
    lift
FROM sku_recommendations
WHERE confidence > 0.8
ORDER BY lift DESC
LIMIT 20;
```

---

### 5. Mining Jobs & Logs
**Business Logic:** Track association mining job execution

**Tables:**
- `mining_schedules` - Job configurations
- `mining_job_logs` - Execution history

**Key Columns:**
- `mining_schedules.id` → `mining_job_logs.schedule_id`
- Status values: `'PENDING'`, `'RUNNING'`, `'COMPLETED'`, `'FAILED'`

**Common Queries:**
```sql
-- Failed jobs with schedule details
SELECT 
    ms.schedule_name,
    mjl.started_at,
    mjl.completed_at,
    mjl.execution_status,
    mjl.error_message,
    mjl.records_processed
FROM mining_job_logs mjl
JOIN mining_schedules ms ON mjl.schedule_id = ms.id
WHERE mjl.execution_status = 'FAILED'
ORDER BY mjl.started_at DESC;
```

---

### 6. Bin Velocity & Performance
**Business Logic:** Track bin picking performance metrics

**Tables:**
- `bin_velocity_scores` - Composite velocity metrics
- `bin_velocity_history` - Historical velocity data
- `sku_velocity_scores` - SKU-level velocity

**Key Metrics:**
- `composite_velocity_score` - Overall bin performance
- Higher scores = more frequently accessed

**Common Queries:**
```sql
-- High-velocity bins in specific zone
SELECT 
    bvs.bin_id,
    bvs.composite_velocity_score,
    bc.bin_location,
    bc.zone
FROM bin_velocity_scores bvs
JOIN bin_configuration bc ON bvs.bin_id = bc.bin_id
WHERE bc.zone = 'ZONE_A'
ORDER BY bvs.composite_velocity_score DESC
LIMIT 10;
```

---

## Common Query Patterns

### Pattern 1: Time-based Aggregations
Use `DATE_SUB()` and `NOW()` for date filtering:
```sql
WHERE INSERTED_TIMESTAMP >= DATE_SUB(NOW(), INTERVAL 7 DAY)    -- Last 7 days
WHERE INSERTED_TIMESTAMP >= DATE_SUB(NOW(), INTERVAL 1 MONTH)  -- Last month
WHERE INSERTED_TIMESTAMP >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) -- Last year
```

### Pattern 2: Top N Results
Always include ORDER BY and LIMIT:
```sql
ORDER BY total_qty DESC LIMIT 10;  -- Top 10
ORDER BY score DESC LIMIT 5;       -- Top 5
```

### Pattern 3: Grouping with Multiple Dimensions
```sql
GROUP BY 
    DATE(order_date),
    zone,
    sku_category
```

### Pattern 4: Status Filtering
Check enum values in schema:
```sql
WHERE order_status IN ('COMPLETED', 'ORDERLINE_COMPLETED')
WHERE execution_status = 'FAILED'
WHERE TYPE = 'STATION_PICK'
```

---

## Date/Timestamp Fields Reference

| Table | Date Column | Use For |
|-------|-------------|---------|
| `wms_to_wcs_order_line_request_data` | `INSERTED_TIMESTAMP` | When order was created |
| `wms_to_wcs_order_line_request_data` | `UPDATED_TIMESTAMP` | Last modification |
| `order_bin_mapping` | `INSERTED_TIMESTAMP` | When bin was assigned |
| `mining_job_logs` | `started_at` | Job start time |
| `mining_job_logs` | `completed_at` | Job completion time |
| `bin_configuration` | `created_date` | Bin creation date |
| `bin_configuration` | `last_updated` | Last config change |

---

## Troubleshooting Common Errors

### Error: "Unknown column in 'on clause'"
**Cause:** Incorrect join column or table alias
**Solution:** 
1. Check actual column names in schema (case-sensitive!)
2. Verify data types match (INT vs VARCHAR)
3. Use correct table aliases

### Error: "Table doesn't exist"
**Cause:** Using assumed table name instead of actual
**Solution:** 
- Use `wms_to_wcs_order_line_request_data` NOT `order_history`
- Use `sku_master` NOT `products` or `items`

### Error: "Ambiguous column"
**Cause:** Same column name in multiple tables without alias
**Solution:** Always use table aliases:
```sql
-- BAD:
SELECT SKU_ID FROM sku_master JOIN ...

-- GOOD:
SELECT sm.SKU_ID FROM sku_master sm JOIN ...
```

---

## Business Logic Rules

### 1. Order Status Flow
```
PENDING → ORDER_CANCELLED
PENDING → ORDERLINE_COMPLETED
PENDING → ORDERLINETAKEN
```

### 2. Bin Status Flow
```
PENDING → TASK_ALLOCATED → BIN_PICKED → ON_STATION → TASK_COMPLETED → OPERATION_COMPLETED
```

### 3. Mining Job Status
```
PENDING → RUNNING → COMPLETED
PENDING → RUNNING → FAILED
```

---

## 7. Bot Maintenance Tasks
**Business Logic:** Track maintenance tasks assigned to bots and their completion status

**Tables:**
- `dashboard_log_maintenance_task_master` - Logs all maintenance task assignments

**Key Columns:**
- `MAINTENANCE_TASK_ID` (bigint) - Unique task identifier
- `MAINTENANCE_POINT_BOT_ID` (varchar) - **PRIMARY bot assigned** ⚠️ NOT BOT_ID!
- `MAINTENANCE_PICK_POINT_BOT_ID` (varchar) - Secondary bot (if needed)
- `MAINTENANCE_ID` (int) - References maintenance configuration
- `TASK_DONE` (tinyint) - 0 = incomplete, 1 = complete
- `INSERTED_TIMESTAMP` (datetime) - When task was assigned
- `UPDATED_TIMESTAMP` (datetime) - Last update
- `BIN_BARCODE_SCANNED` (varchar) - Bin involved in maintenance
- `IS_MP_BOT_HEALTHY` (tinyint) - Bot health status

**Common Queries:**
```sql
-- Find incomplete maintenance tasks by bot
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

-- Count incomplete tasks per bot
SELECT 
    MAINTENANCE_POINT_BOT_ID AS bot_id,
    COUNT(*) AS incomplete_tasks,
    MIN(INSERTED_TIMESTAMP) AS oldest_task,
    MAX(INSERTED_TIMESTAMP) AS newest_task
FROM dashboard_log_maintenance_task_master
WHERE TASK_DONE = 0
GROUP BY MAINTENANCE_POINT_BOT_ID
ORDER BY incomplete_tasks DESC;

-- Maintenance task completion rate
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

**Important Notes:**
- ⚠️ **Column name is `MAINTENANCE_POINT_BOT_ID`, NOT `BOT_ID`**
- `TASK_DONE`: 0 = incomplete/pending, 1 = complete
- Multiple bots can be involved: check both `MAINTENANCE_POINT_BOT_ID` and `MAINTENANCE_PICK_POINT_BOT_ID`

**Related Bot Tables:**
- `bot_master` - Bot configuration and master data
- `bot_master_log` - Bot status change logs
- `dashboard_bot_master` - Dashboard bot information
- `bot_alarm_log` - Bot alarm/error logs
- `bot_charging_bit_log` - Bot charging status logs
- `dashboard_log_bot_charging` - Charging activity logs
- `robot_charge_log` - Robot charging history
- `pseudo_bot_alarm_log` - Simulated bot alarms (testing)

---

## 8. Bot Information & Status
**Business Logic:** Track all bots in the system, their configurations, status, and activity

**Primary Table:**
- `bot_master` - **⚠️ ALWAYS START HERE for bot queries** (main bot registry)

**Key Columns:**
- `BOT_ID` (varchar) - **Primary key**, unique bot identifier
- `BOT_IP` (varchar) - Bot IP address
- `BOT_TYPE` (varchar) - Type/model of bot
- `STATUS` (varchar) - Current operational status (e.g., 'ACTIVE', 'IDLE', 'ERROR')
- `IS_ACTIVE` (tinyint) - 1 = active/online, 0 = inactive/offline

**Common Queries:**
```sql
-- Count total bots in system
SELECT COUNT(*) AS total_bots 
FROM bot_master;

-- Count active/online bots
SELECT COUNT(*) AS active_bots 
FROM bot_master 
WHERE IS_ACTIVE = 1;

-- Count bots by status
SELECT 
    STATUS,
    COUNT(*) AS bot_count
FROM bot_master 
GROUP BY STATUS
ORDER BY bot_count DESC;

-- List all bots with details
SELECT 
    BOT_ID,
    BOT_IP,
    BOT_TYPE,
    STATUS,
    IS_ACTIVE
FROM bot_master 
ORDER BY BOT_ID 
LIMIT 100;

-- Filter bots by type
SELECT 
    BOT_ID,
    BOT_IP,
    STATUS,
    IS_ACTIVE
FROM bot_master 
WHERE BOT_TYPE = 'AGV_STANDARD'  -- or specific type
ORDER BY STATUS, BOT_ID
LIMIT 50;

-- Active bots with specific status
SELECT BOT_ID, BOT_IP, BOT_TYPE 
FROM bot_master 
WHERE IS_ACTIVE = 1 
  AND STATUS = 'ACTIVE'
ORDER BY BOT_ID;
```

**Related Tables:**
- `dashboard_bot_master` - Dashboard-specific bot data
- `bot_master_log` - Historical status changes
- `bot_alarm_log` - Bot errors and alarms
- `bot_charging_bit_log` - Charging status logs
- `dashboard_log_bot_charging` - Charging activity
- `robot_charge_log` - Charging history
- `dashboard_log_maintenance_task_master` - Maintenance tasks (uses MAINTENANCE_POINT_BOT_ID)

**Important Notes:**
- ⚠️ **ALWAYS use `bot_master` as primary table for bot counts, lists, and status checks**
- Bot queries should start with `SELECT ... FROM bot_master`
- For maintenance tasks, use `MAINTENANCE_POINT_BOT_ID` (NOT BOT_ID) in `dashboard_log_maintenance_task_master`
- `STATUS` values vary by implementation - check actual data for valid values
- `IS_ACTIVE` is the reliable indicator for bot availability

---

## Performance Tips

1. **Always use LIMIT** - Default to 100, max 1000
2. **Index-friendly queries** - Filter on indexed columns (ID, TIMESTAMP)
3. **Avoid SELECT *** - Specify columns when possible
4. **Date range filters** - Use BETWEEN or >= comparison
5. **JOIN order** - Start with smallest result set

---

## Adding New Query Patterns

When you discover a new complex query pattern, document it here with:

1. **Business Question** - What user is asking
2. **Tables Involved** - All tables in the query
3. **Join Conditions** - How tables connect
4. **Filters** - Common WHERE conditions
5. **Expected Result** - What output looks like

**Example Template:**
```markdown
### Pattern: [Name]
**Question:** [User question]
**Tables:** table1, table2, table3
**SQL:**
```sql
[Your SQL here]
```
**Notes:** [Any special considerations]
```

---

## Update History

| Date | Updated By | Changes |
|------|------------|---------|
| 2025-11-12 | System | Initial schema guide created |

---

## Additional Resources

- Full schema HTML: `/app/modules/neo_chatbot/data/database/database_schema.htm`
- Schema parser: `/app/modules/neo_chatbot/utils/schema_parser.py`
- SQL Assistant service: `/app/modules/neo_chatbot/services/sql_assistant_service.py`
