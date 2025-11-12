# SQL Assistant - Quick Reference for Complex Queries

## Fast Lookup: Table Relationships

### Orders → SKU Names
```
wms_to_wcs_order_line_request_data.ARTICLE_ID = sku_master.SKU_ID
```

### Orders → Bins → Locations (3-table)
```
order_bin_mapping.BIN_ID = bin_info_master.BIN_ID (INT)
bin_info_master.BIN_BARCODE = bin_configuration.bin_id (VARCHAR)
```

### Bins → Velocity
```
bin_velocity_scores.bin_id = bin_configuration.bin_id
```

### SKUs → Velocity
```
sku_velocity_scores.sku_id = sku_master.SKU_ID
```

### Mining Jobs → Schedules
```
mining_job_logs.schedule_id = mining_schedules.id
```

---

## Data Type Warnings ⚠️

| Table | Column | Type | Notes |
|-------|--------|------|-------|
| `bin_info_master` | `BIN_ID` | INT | Primary key |
| `bin_configuration` | `bin_id` | VARCHAR | Physical identifier |
| `order_bin_mapping` | `BIN_ID` | INT | Links to bin_info_master |
| `sku_master` | `SKU_ID` | VARCHAR | Primary key |
| `wms_to_wcs_order_line_request_data` | `ARTICLE_ID` | VARCHAR | Links to SKU_ID |

---

## Date Field Cheatsheet

**Orders:** `INSERTED_TIMESTAMP`, `UPDATED_TIMESTAMP`  
**Bins:** `created_date`, `last_updated`, `INSERTED_TIMESTAMP`  
**Mining Jobs:** `started_at`, `completed_at`

---

## Status Enum Values

**Order Status:**
- `PENDING`
- `ORDER_CANCELLED`
- `ORDERLINE_COMPLETED`
- `ORDERLINETAKEN`
- `DELETED`

**Bin Status:**
- `PENDING`
- `TASK_ALLOCATED`
- `BIN_PICKED`
- `ON_STATION`
- `TASK_COMPLETED`
- `OPERATION_COMPLETED`

**Mining Job Status:**
- `PENDING`
- `RUNNING`
- `COMPLETED`
- `FAILED`

---

## Common Mistakes to Avoid

❌ `order_history` → ✅ `wms_to_wcs_order_line_request_data`  
❌ `products` → ✅ `sku_master`  
❌ `items` → ✅ `sku_master`  
❌ `bc.ARTICLE_ID` → ✅ `bc` doesn't have ARTICLE_ID  
❌ `WHERE inserted_timestamp` → ✅ `WHERE INSERTED_TIMESTAMP` (case-sensitive)

---

## Query Templates

### Template 1: Orders with SKU info (Last N days)
```sql
SELECT 
    sm.SKU_ID,
    sm.SKU_NAME,
    SUM(ord.QUANTITY) AS total_qty,
    COUNT(DISTINCT ord.ORDER_ID) AS order_count
FROM wms_to_wcs_order_line_request_data ord
JOIN sku_master sm ON ord.ARTICLE_ID = sm.SKU_ID
WHERE ord.INSERTED_TIMESTAMP >= DATE_SUB(NOW(), INTERVAL [N] DAY)
GROUP BY sm.SKU_ID, sm.SKU_NAME
ORDER BY total_qty DESC
LIMIT 100;
```

### Template 2: Bin locations with order activity
```sql
SELECT 
    bc.bin_location,
    bc.zone,
    COUNT(obm.ORDER_BIN_ID) AS order_count
FROM order_bin_mapping obm
JOIN bin_info_master bim ON obm.BIN_ID = bim.BIN_ID
JOIN bin_configuration bc ON bim.BIN_BARCODE = bc.bin_id
WHERE obm.INSERTED_TIMESTAMP >= DATE_SUB(NOW(), INTERVAL [N] DAY)
GROUP BY bc.bin_location, bc.zone
ORDER BY order_count DESC
LIMIT 100;
```

### Template 3: Mining job analysis
```sql
SELECT 
    ms.schedule_name,
    mjl.execution_status,
    mjl.started_at,
    TIMESTAMPDIFF(MINUTE, mjl.started_at, mjl.completed_at) AS duration_minutes,
    mjl.records_processed,
    mjl.rules_generated
FROM mining_job_logs mjl
JOIN mining_schedules ms ON mjl.schedule_id = ms.id
WHERE mjl.started_at >= DATE_SUB(NOW(), INTERVAL [N] DAY)
ORDER BY mjl.started_at DESC;
```

### Template 4: High-velocity analysis
```sql
SELECT 
    bvs.bin_id,
    bvs.composite_velocity_score,
    bc.bin_location,
    bc.zone,
    bc.current_sku_count
FROM bin_velocity_scores bvs
JOIN bin_configuration bc ON bvs.bin_id = bc.bin_id
WHERE bvs.composite_velocity_score > [THRESHOLD]
ORDER BY bvs.composite_velocity_score DESC
LIMIT 50;
```

---

## When Adding New Complex Queries

Document in `schema_guide.md`:
1. User's question
2. Tables used
3. Join conditions
4. Expected output
5. Common filters

This helps future queries of similar type!
