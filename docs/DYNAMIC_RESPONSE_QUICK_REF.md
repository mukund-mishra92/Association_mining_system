# Dynamic Response Formatting - Quick Reference

## Overview
The diagnostic system now adapts its response format based on what the user actually wants, instead of always using the same rigid format.

---

## 5 Response Formats

### 1. 📊 DATA_QUERY
**When:** User wants to see raw data or query results  
**Trigger Words:** "show me", "list", "what are", "how many"  
**Format:** Brief answer + data table/list  
**Example:**
```
Query: "show me all tasks for BOT-001"

Response:
Here are the tasks for BOT-001:

| Task ID | Status | Created |
|---------|--------|---------|
| T-123   | ACTIVE | 14:23   |
| T-124   | DONE   | 15:01   |
```

---

### 2. 🔍 EXPLAIN_CRITERIA
**When:** User wants to understand how system checks/determines something  
**Trigger Words:** "what is your criteria", "how do you check", "how do you determine"  
**Format:** Explanation of logic + SQL query  
**Example:**
```
Query: "what is your criteria to check active bots"

Response:
The system checks active bots using this criteria:

```sql
SELECT COUNT(*) as total_bots,
       SUM(CASE WHEN STATUS='ACTIVE' THEN 1 ELSE 0 END) as active_bots
FROM bot_master;
```

How it works:
1. Queries the bot_master table
2. Counts total bots in the system
3. Filters for STATUS = 'ACTIVE' to get active count
4. A bot is "active" when STATUS field is 'ACTIVE'
```

---

### 3. 🔧 TROUBLESHOOT
**When:** User has a problem and needs diagnosis  
**Trigger Words:** "why", "stuck", "not working", "issue", "problem"  
**Format:** Full diagnostic (Root Cause → What I Found → Solution → Next Steps)  
**Example:**
```
Query: "why bots are not coming to the station"

Response:
## Root Cause
The bots are not coming because there are no active bots available.

## What I Found
- Total bots: 48, active_bots: 0
- 2 tasks in PROCESSING status
- Pending bin assignments may be blocking

## Solution
1. Check order_bin_mapping for pending bins
2. Verify bot allocation logic
3. Review system logs

## Next Steps
1. Run: SELECT * FROM order_bin_mapping WHERE STATUS='PENDING'
2. Investigate bot activation process
```

---

### 4. 💡 RECOMMENDATION
**When:** User wants advice or best practices  
**Trigger Words:** "what should I check", "how can I prevent", "best practices"  
**Format:** Actionable recommendations + preventive measures  
**Example:**
```
Query: "what should I check to prevent bots getting stuck"

Response:
To prevent bots getting stuck, regularly monitor:

1. Task Allocation
   - Run: SELECT STATUS, COUNT(*) FROM task_master GROUP BY STATUS
   - Alert if IN_PROGRESS count grows

2. Station Bin Mappings
   - Check: SELECT * FROM order_bin_mapping WHERE STATUS='PENDING'
   - Clear stale PENDING mappings

3. Bot Health
   - Monitor battery levels (alert <20%)
   - Check connectivity every 5 minutes

Best Practices:
- Implement task timeout (1 hour max)
- Add bot heartbeat monitoring
- Set up alerts for anomalies
```

---

### 5. 📝 SHOW_QUERY
**When:** User wants to see the actual SQL query  
**Trigger Words:** "show me the query", "what query", "which SQL"  
**Format:** SQL query + explanation  
**Example:**
```
Query: "show me the SQL query you use to check bot status"

Response:
Here's the SQL query used to check bot status:

```sql
SELECT BOT_ID, STATUS, LAST_UPDATED
FROM bot_master
WHERE BOT_ID = ?
ORDER BY LAST_UPDATED DESC;
```

What it does:
- Retrieves bot status from bot_master table
- Filters by specific BOT_ID
- Shows last updated timestamp
- Orders by most recent first
```

---

## How It Works

```
User Question
    ↓
Intent Classification (using LLM)
    ↓
Select Appropriate Format
    ↓
Gather Data (SQL + Historical + Docs)
    ↓
Generate Response (using matched format)
    ↓
Return Contextually Appropriate Answer
```

---

## Configuration

Located in `intelligent_diagnostic_service.py`:

```python
def _classify_user_intent(self, query: str) -> Dict[str, Any]:
    # Uses LLM with temp=0.2 for consistent classification
    # Returns: {
    #   "intent_type": "DATA_QUERY|EXPLAIN_CRITERIA|TROUBLESHOOT|RECOMMENDATION|SHOW_QUERY",
    #   "show_sql_query": bool,
    #   "show_data_table": bool,
    #   "show_analysis": bool,
    #   "show_solution": bool,
    #   "response_style": "data_focused|explanation|diagnostic|advisory",
    #   "reasoning": "why this intent was chosen"
    # }
```

---

## Testing

```bash
python test_dynamic_response_format.py
```

Tests all 5 intent types and shows classification results.

---

## Benefits

✅ **Natural responses** - Get what you asked for  
✅ **Less cognitive load** - No need to parse irrelevant sections  
✅ **Faster answers** - Concise for simple queries  
✅ **Detailed when needed** - Full diagnostics for problems  
✅ **Context-aware** - Feels more intelligent  

---

## Monitoring

Check logs for intent classification:

```
🎯 Intent classified: EXPLAIN_CRITERIA - User is asking about how system determines active bots
🎯 Response format: explanation
```

---

## Fallback

If intent classification fails, defaults to **TROUBLESHOOT** (full diagnostic) - safest option.

---

## Examples by Intent

| User Question | Old Format | New Format |
|---------------|------------|------------|
| "show me tasks for BOT-001" | Root Cause → Solution | Data table |
| "what is your criteria for active bots" | Root Cause → Solution | SQL query + logic |
| "why bots stuck" | Root Cause → Solution | Root Cause → Solution ✓ |
| "what should I check to prevent" | Root Cause → Solution | Recommendations |
| "show me the query you use" | Root Cause → Solution | SQL query |

---

## Key Improvement

**Before:** Same format for every question (rigid, often inappropriate)  
**After:** Format adapts to user intent (flexible, contextually appropriate)

The system is now **context-aware** and provides **the right type of answer** for each question.
