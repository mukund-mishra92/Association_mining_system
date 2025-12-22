# Temporal Table Classification - Implementation Guide

## Overview
Implemented LLM-based classification to intelligently route queries between current state tables and historical log tables.

## Problem Solved
Previously, queries like "all tasks BOT-0010 has performed till now" would query `task_detail` (current tasks only) instead of `task_detail_log` (complete history), returning incomplete results.

## Solution Architecture

### 1. Temporal Scope Classification
**Method**: `_classify_temporal_scope(query: str)`

Analyzes query for temporal indicators and classifies as:
- **HISTORICAL**: Past events, complete history
- **CURRENT**: Active state, ongoing operations  
- **BOTH**: Requires both current and historical data

**Historical Indicators:**
- Explicit: "check the log", "historical", "from log"
- Past tense: "have done", "has performed", "were doing", "completed"
- Time range: "till now", "till today", "since", "between", "all time"
- Aggregate: "complete history", "how many times", "total"

**Current Indicators:**
- Present tense: "is doing", "are performing", "is running"
- Current state: "current", "currently", "now", "right now", "active"
- Assignment: "assigned to", "working on"
- Latest: "latest", "most recent", "newest"

### 2. Table Mapping

| Query Type | Tables Used |
|-----------|-------------|
| Historical | `task_detail_log`, `bot_master_log`, `bin_info_master_log`, `order_line_log`, `alarm_log`, `charge_log` |
| Current | `task_detail`, `bot_master`, `bin_info_master`, `live_inventory_master` |

### 3. Enhanced System Prompt
**Method**: `_build_temporal_table_guidance(temporal_info, query)`

Generates prominent guidance in the LLM prompt:
```
🕐 TEMPORAL SCOPE DETECTED: HISTORICAL/PAST QUERY
⚠️⚠️⚠️ CRITICAL TABLE SELECTION RULE ⚠️⚠️⚠️
✅ USE LOG/HISTORICAL TABLES for this query:
   - task_detail_log (NOT task_detail) → For ALL tasks performed till now
   ...
```

## Example Behavior

### Historical Query
**Input**: "can you give me all the task BOT-0010 this bot has performed till now"

**Detection**:
- Indicators: "have performed", "till now"
- Scope: HISTORICAL (95% confidence)
- Table preference: LOG

**Generated SQL**:
```sql
SELECT * FROM task_detail_log WHERE BOT_ID = 'BOT-0010' ORDER BY END_TIME DESC
```
✅ Correct - uses `task_detail_log` for complete history

### Current Query
**Input**: "what task is BOT-0023 doing now"

**Detection**:
- Indicators: "is doing", "now"
- Scope: CURRENT (90% confidence)
- Table preference: CURRENT

**Generated SQL**:
```sql
SELECT * FROM task_detail WHERE BOT_ID = 'BOT-0023' AND STATUS = 'PROCESSING'
```
✅ Correct - uses `task_detail` for current active tasks

## Testing

### Manual Test
```powershell
# Terminal 1: Start server
.\quick_start.py

# Terminal 2: Run temporal classification tests
.\.venv\Scripts\python.exe test_temporal_classification.py
```

### Test Coverage
- ✅ Historical queries with explicit log references
- ✅ Historical queries with past tense verbs
- ✅ Historical queries with time ranges
- ✅ Current queries with present tense
- ✅ Current queries with "now"/"currently"
- ✅ Current queries for latest/active state

## Configuration

### Confidence Thresholds
- **High confidence** (>0.6): Strong temporal guidance shown
- **Medium confidence** (0.4-0.6): Basic guidance
- **Low confidence** (<0.4): Default to current tables

### Extensibility
To add new table mappings:

```python
# In _build_temporal_table_guidance()
if preference == 'log':
    guidance_parts.append("   • your_table → your_table_log")
```

## Integration Points

### SQL Assistant Service
1. `_classify_query_intent()` - Calls temporal classifier
2. `_get_system_prompt()` - Injects temporal guidance
3. `_build_temporal_table_guidance()` - Formats guidance text

### Key Files Modified
- `app/modules/neo_chatbot/services/sql_assistant_service.py`
  - Added `_classify_temporal_scope()` method
  - Added `_build_temporal_table_guidance()` method
  - Enhanced `_classify_query_intent()` to include temporal scope
  - Modified `_get_system_prompt()` to inject temporal guidance

## Monitoring

Check server logs for temporal classification:
```
INFO: Temporal scope: historical, confidence: 0.95, indicators: ['have performed', 'till now']
INFO: Using table preference: LOG
```

## Known Limitations

1. **Ambiguous queries**: Queries like "show me tasks" without temporal indicators default to current tables
2. **Mixed queries**: Queries needing both current and historical data may need manual refinement
3. **Language variations**: Non-English queries not supported

## Future Enhancements

1. **Smart UNION**: Automatically combine current + log tables for "both" scope
2. **Performance optimization**: Add hints for log table queries (indexes, time ranges)
3. **Multi-language**: Support temporal indicators in other languages
4. **Learning**: Track which table choices led to successful queries

## Validation

Run validation suite:
```powershell
.\.venv\Scripts\python.exe test_temporal_classification.py
```

Expected output:
```
✅ Passed: 10/10
🎉 ALL TESTS PASSED - Temporal classification working correctly!
```
