# Schema Documentation Change Log

Track changes to schema documentation and new query patterns discovered.

## Format
```
### [Date] - [Your Name]
**Change Type:** [New Pattern | Fix | Update | Enhancement]
**Query Type:** [Description]
**Why:** [Reason for documentation]
**SQL Added:** [Yes/No]
**Tested:** [Yes/No]
```

---

## 2025-11-13 - System (Update 3)

### Change Type: Enhancement - Bot Query Optimization
**Query Type:** Bot Counts & Information
**Why:** Ensure all bot-related queries use the authoritative primary table `bot_master`
**SQL Added:** Yes
**Tested:** Yes

**User Request:** 
"For this bot related queries, we should start from bot master table"

**Context:**
- User successfully tested bot count query: "i need the count of total bots"
- Request to optimize by ensuring `bot_master` is always the starting point
- Multiple bot-related tables exist (bot_master, dashboard_bot_master, bot_master_log)
- Need to establish `bot_master` as the primary/authoritative source

**Documentation Updates:**

1. **sql_assistant_service.py** - Added Section 6 to system prompt
   - "BOT INFORMATION & COUNTS" section with bot_master mandate
   - Key columns: BOT_ID (varchar PK), BOT_IP, BOT_TYPE, STATUS, IS_ACTIVE
   - Added Rules 4-5: "ALWAYS start from bot_master table" for bot queries
   - Added 3 example queries:
     * Count total bots: `SELECT COUNT(*) FROM bot_master`
     * Count active bots: `SELECT COUNT(*) FROM bot_master WHERE IS_ACTIVE = 1`
     * List all bots: `SELECT BOT_ID, BOT_IP, BOT_TYPE, STATUS FROM bot_master LIMIT 100`

2. **quick_reference.md** - Added bot_master to Fast Lookup section
   - New section "⚠️ Bot Queries → ALWAYS START FROM bot_master"
   - Fast reference showing PRIMARY table and key columns
   - Template 6: Bot Information & Counts with 4 query examples

3. **schema_guide.md** - Added Section 8 "Bot Information & Status"
   - Complete bot_master table structure
   - 6 common query patterns (total count, active count, status breakdown, list all, filter by type, active with status)
   - Related tables listed with purposes
   - Important notes emphasizing bot_master as primary table

**Query Examples:**
```sql
-- Total bots
SELECT COUNT(*) AS total_bots FROM bot_master;

-- Active bots
SELECT COUNT(*) AS active_bots FROM bot_master WHERE IS_ACTIVE = 1;

-- Bot status breakdown
SELECT STATUS, COUNT(*) AS bot_count 
FROM bot_master 
GROUP BY STATUS;

-- List bots with details
SELECT BOT_ID, BOT_IP, BOT_TYPE, STATUS, IS_ACTIVE 
FROM bot_master 
ORDER BY BOT_ID 
LIMIT 100;
```

**Why This Matters:**
- `bot_master` is the authoritative registry for all bots
- Derivative tables (dashboard_bot_master, bot_master_log) should be used for joins, not primary queries
- Ensures consistent bot counts and status information
- Follows same pattern as maintenance task fix (using correct primary table)

---

## 2025-11-12 - System (Update 2)

### Change Type: Fix - Incorrect Column Name
**Query Type:** Bot Maintenance Tasks
**Why:** SQL Assistant generated query with wrong column name `BOT_ID` instead of `MAINTENANCE_POINT_BOT_ID`
**SQL Added:** Yes
**Tested:** Yes

**User Question:** 
"I need to find out the bots involved and task id for which the bots have assigned the task but not able to complete it. need to add the date as well"

**Error:** 
`Unknown column 'dlm.BOT_ID' in 'field list'`

**Root Cause:**
- Table `dashboard_log_maintenance_task_master` doesn't have `BOT_ID` column
- Actual column name is `MAINTENANCE_POINT_BOT_ID` (varchar 100)
- Secondary bot column is `MAINTENANCE_PICK_POINT_BOT_ID`

**Corrected Query:**
```sql
SELECT 
    MAINTENANCE_POINT_BOT_ID AS bot_id,
    MAINTENANCE_TASK_ID AS task_id,
    INSERTED_TIMESTAMP AS task_assigned_date
FROM dashboard_log_maintenance_task_master
WHERE TASK_DONE = 0
ORDER BY INSERTED_TIMESTAMP DESC
LIMIT 100;
```

**Documentation Updates:**
1. Added Section 7 "Bot Maintenance Tasks" to `schema_guide.md`
   - Table structure and key columns
   - 3 example queries (incomplete tasks, counts per bot, completion rate)
   - Warning about correct column names

2. Added Template 5 "Maintenance Tasks" to `quick_reference.md`
   - Column name clarification (MAINTENANCE_POINT_BOT_ID NOT BOT_ID)
   - TASK_DONE status values (0=incomplete, 1=complete)

3. Updated "Common Mistakes" section in `quick_reference.md`
   - Added: ❌ `dashboard_log_maintenance_task_master.BOT_ID` → ✅ `MAINTENANCE_POINT_BOT_ID`

**Table Columns:**
- `MAINTENANCE_TASK_ID` (bigint, primary key)
- `MAINTENANCE_ID` (int)
- `MAINTENANCE_POINT_BOT_ID` (varchar 100) ⚠️
- `MAINTENANCE_PICK_POINT_BOT_ID` (varchar 100)
- `BIN_BARCODE_SCANNED` (varchar 50)
- `TASK_DONE` (tinyint, 0=incomplete 1=complete)
- `INSERTED_TIMESTAMP` (datetime)
- `IS_MP_BOT_HEALTHY` (tinyint)

---

## 2025-11-12 - System

### Change Type: Initial Documentation
**Query Type:** Multi-table JOINs for Orders, SKUs, and Bins
**Why:** SQL Assistant was generating incorrect queries with non-existent table names
**SQL Added:** Yes
**Tested:** Yes

**Changes Made:**
1. Created `schema_guide.md` with:
   - Orders ↔ SKUs relationship
   - Bins ↔ Locations multi-table JOIN
   - Mining jobs ↔ Schedules
   - Common query patterns
   - Troubleshooting guide

2. Created `quick_reference.md` with:
   - Fast lookup table relationships
   - Data type warnings (INT vs VARCHAR for bin_id)
   - Status enum values
   - Query templates
   - Common mistakes

3. Updated SQL Assistant system prompt with:
   - Critical table relationships
   - JOIN examples
   - Data type warnings

**Verified Working Queries:**
- ✅ Top SKUs ordered last week (2-table JOIN)
- ✅ Bin locations with most orders (3-table JOIN)
- ✅ Top bins by velocity score
- ✅ Failed mining jobs

**Known Issues:**
- ⚠️ `sku_recommendations` table column names need verification
- ⚠️ Some queries show 50% confidence due to empty result sets (expected behavior)

---

## Template for Future Entries

### [YYYY-MM-DD] - [Your Name]
**Change Type:** [New Pattern | Fix | Update | Enhancement]
**Query Type:** [Brief description]
**Why:** [Reason for change]
**SQL Added:** [Yes/No]
**Tested:** [Yes/No]

**Changes Made:**
- [List what was added/changed]

**Verified Queries:**
- ✅ [Query description]
- ✅ [Query description]

**Issues Found:**
- ⚠️ [Any problems discovered]

---

## Guidelines for Adding Entries

1. **New Pattern** - When you discover a new complex query requiring 3+ tables
2. **Fix** - When you correct an existing documented pattern
3. **Update** - When schema changes require documentation updates
4. **Enhancement** - When you improve existing documentation

Always include:
- The actual user question that triggered the discovery
- The working SQL query
- Any gotchas or warnings
- Test results (does it run? does it return data?)
