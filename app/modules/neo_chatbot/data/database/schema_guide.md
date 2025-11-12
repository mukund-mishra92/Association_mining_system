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
