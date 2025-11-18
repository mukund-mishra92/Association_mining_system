# Comprehensive Chat Logging & Learning System

## Overview

We've implemented a **comprehensive chat history and analytics system** that automatically logs every SQL assistant interaction and provides powerful analytics for continuous system improvement.

## What's Been Implemented

### 1. Chat History Service (`chat_history_service.py`)

A complete logging and analytics service that tracks:

#### Database Tables Created
- **`chatbot_chat_history`**: All chat interactions with timestamps, confidence scores
- **`chatbot_sql_queries`**: SQL query details (generated SQL, execution status, errors, tables/columns used)
- **`chatbot_column_corrections`**: All column name corrections (automatic and manual)
- **`chatbot_feedback`**: User feedback (positive/negative/neutral with ratings and comments)
- **`chatbot_query_patterns`**: Learned patterns with success rates and frequencies

#### Key Features

**Logging Methods:**
- `log_chat_interaction()` - Logs every chat with response time and confidence
- `log_sql_query()` - Logs SQL generation and execution details
- `log_column_correction()` - Tracks column name corrections
- `log_feedback()` - Records user feedback
- `update_query_pattern()` - Updates learned patterns

**Analytics Methods:**
- `get_query_analytics()` - Success rates, execution times, common tables/intents/errors
- `get_learned_column_mappings()` - Frequently corrected column names
- `get_common_query_patterns()` - High-success query patterns
- `get_improvement_suggestions()` - AI-generated improvement recommendations
- `get_session_history()` - Complete session history from database

### 2. SQL Assistant Integration

**Automatic Logging:**
- ✅ Every query attempt is logged (success or failure)
- ✅ Execution time and confidence scores tracked
- ✅ Auto-corrections logged with similarity scores
- ✅ Tables and columns extracted from SQL
- ✅ Intent and entities classified
- ✅ Query patterns updated for learning

**What Gets Logged:**
```python
# For successful queries:
- User query
- Generated SQL
- Execution status: 'success'
- Rows returned
- Execution time
- Tables used
- Columns used
- Intent (count, retrieve, aggregate, metadata)
- Entities (bin, order, sku, bot, etc.)
- Auto-corrections applied

# For failed queries:
- User query
- Generated SQL
- Execution status: 'failed'
- Error message (truncated to 500 chars)
- Tables attempted
- Intent and entities
```

### 3. API Endpoints for Analytics

New endpoints in `chatbot_endpoints.py`:

#### GET `/api/chatbot/analytics/sql-queries?days=7`
Get query analytics over time period:
```json
{
  "total_queries": 150,
  "successful_queries": 135,
  "failed_queries": 15,
  "success_rate": 90.0,
  "avg_execution_time_ms": 245.5,
  "avg_rows_returned": 12.3,
  "top_tables": [
    {"table_name": "sku_master", "usage_count": 45},
    {"table_name": "wms_to_wcs_order_line_request_data", "usage_count": 32}
  ],
  "common_intents": [
    {"intent": "count", "count": 50, "success_rate": 0.94},
    {"intent": "retrieve", "count": 80, "success_rate": 0.88}
  ],
  "common_errors": [
    {"error_message": "Unknown column 'ArticleId'", "error_count": 8}
  ]
}
```

#### GET `/api/chatbot/analytics/learned-patterns?limit=50`
Get successful query patterns:
```json
{
  "patterns_count": 35,
  "patterns": [
    {
      "pattern_type": "intent",
      "pattern_key": "count",
      "pattern_value": "how many orders",
      "frequency": 45,
      "success_rate": 0.95,
      "avg_confidence": 0.87
    }
  ]
}
```

#### GET `/api/chatbot/analytics/column-mappings?min_frequency=3`
Get learned column corrections:
```json
{
  "tables_count": 5,
  "mappings": {
    "sku_master": [
      {
        "wrong": "ArticleId",
        "correct": "ARTICLE_ID",
        "frequency": 12,
        "confidence": 0.85
      },
      {
        "wrong": "SkuId",
        "correct": "SKU_ID",
        "frequency": 8,
        "confidence": 0.92
      }
    ]
  }
}
```

#### GET `/api/chatbot/analytics/improvement-suggestions`
Get AI-generated improvement recommendations:
```json
{
  "total_suggestions": 15,
  "suggestions": {
    "column_mappings": [
      "Add mapping: sku_master.ArticleId → ARTICLE_ID (used 12 times)",
      "Add mapping: order_master.OrderId → ORDER_ID (used 9 times)"
    ],
    "entity_table_mappings": [
      "Review table mappings for entities: bin, location (success rate: 45.2%)"
    ],
    "common_errors": [
      "Frequent error (8x): Unknown column 'ArticleId' in 'where clause'"
    ],
    "optimization_tips": [
      "Overall success rate is low (65%). Consider reviewing table selection logic."
    ]
  }
}
```

#### GET `/api/chatbot/history/{session_id}?limit=50`
Get persistent session history:
```json
{
  "session_id": "abc-123",
  "message_count": 15,
  "history": [
    {
      "chat_id": "xyz-789",
      "user_query": "how many orders today",
      "assistant_response": "Found 45 orders...",
      "confidence_score": 0.92,
      "timestamp": "2025-11-17T10:30:00",
      "generated_sql": "SELECT COUNT(*) FROM...",
      "execution_status": "success",
      "rows_returned": 1
    }
  ]
}
```

#### POST `/api/chatbot/feedback`
Submit user feedback:
```json
{
  "chat_id": "xyz-789",
  "session_id": "abc-123",
  "feedback_type": "positive",
  "rating": 5,
  "comment": "Perfect! Got exactly what I needed."
}
```

## How It Improves the System

### 1. **Automatic Column Name Learning**
- Tracks which column name typos users make
- After 3+ occurrences, suggests adding permanent mapping
- Example: "ArticleId" → "ARTICLE_ID" used 12 times → add to fuzzy matcher

### 2. **Entity-Table Mapping Optimization**
- Learns which tables are actually used for each entity
- Identifies low-success entities that need better table mappings
- Example: "bin" queries fail 55% → review bin-related table mappings

### 3. **Common Error Pattern Detection**
- Identifies recurring error messages
- Helps prioritize fixes for most impactful issues
- Example: "Unknown column" errors → focus on column name matching

### 4. **Query Pattern Recognition**
- Learns successful query patterns with high confidence
- Can pre-generate SQL for common questions
- Example: "how many X" patterns → optimize COUNT query generation

### 5. **Performance Monitoring**
- Tracks execution times and identifies slow queries
- Monitors success rates over time
- Example: Avg execution time > 1s → add query optimization hints

## Usage Examples

### View Analytics Dashboard
```bash
# Get last 30 days of analytics
curl http://localhost:8000/api/chatbot/analytics/sql-queries?days=30

# Get top 100 learned patterns
curl http://localhost:8000/api/chatbot/analytics/learned-patterns?limit=100

# Get improvement suggestions
curl http://localhost:8000/api/chatbot/analytics/improvement-suggestions
```

### Submit Feedback
```bash
curl -X POST http://localhost:8000/api/chatbot/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "xyz-789",
    "session_id": "abc-123",
    "feedback_type": "negative",
    "rating": 2,
    "comment": "Wrong table used for inventory query"
  }'
```

### Review Session History
```bash
# Get last 50 interactions for a session
curl http://localhost:8000/api/chatbot/history/abc-123?limit=50
```

## Data Flow

```
User Query
    ↓
SQL Assistant (process_query)
    ↓
Log Chat Interaction → chatbot_chat_history
    ↓
Generate SQL
    ↓
Execute Query
    ↓
Log SQL Query → chatbot_sql_queries
    ↓
Log Corrections → chatbot_column_corrections
    ↓
Update Patterns → chatbot_query_patterns
    ↓
Return Response
    ↓
User Feedback (optional)
    ↓
Log Feedback → chatbot_feedback
    ↓
Analytics & Learning
```

## Benefits

### For Users
- ✅ Better responses over time (system learns from past queries)
- ✅ Fewer column name errors (automatic corrections)
- ✅ Faster query execution (optimized patterns)
- ✅ More accurate results (improved table selection)

### For Developers
- ✅ Data-driven improvement decisions
- ✅ Clear visibility into system performance
- ✅ Automated pattern discovery
- ✅ Proactive error detection
- ✅ Training data for future ML models

### For System
- ✅ Continuous self-improvement
- ✅ Persistent learning across sessions
- ✅ No manual configuration needed
- ✅ Automatic optimization suggestions

## Database Storage

All data is stored in MySQL database with proper indexes for fast queries:

- **Indexes on**: session_id, timestamp, execution_status, table_name, column_name
- **Foreign keys**: Ensure referential integrity
- **JSON columns**: Flexible storage for arrays (tables_used, entities)
- **Automatic timestamps**: created_at, updated_at

## Integration with Existing Systems

- **Works alongside RLHF**: Both systems complement each other
- **No breaking changes**: Existing functionality unchanged
- **Graceful degradation**: If chat history unavailable, system continues normally
- **Backward compatible**: All existing APIs still work

## Next Steps

1. **Test the system**: Try some queries and check the analytics
2. **Review suggestions**: Use `/analytics/improvement-suggestions` to identify improvements
3. **Apply learnings**: Implement suggested column mappings and table optimizations
4. **Monitor trends**: Track success rates over time
5. **Iterate**: Continuous improvement based on data

## Performance Considerations

- Logging is **async** and doesn't slow down responses
- Failed logs are caught and logged as warnings
- Analytics queries are optimized with indexes
- Large result sets are paginated (limit parameters)
- Old data can be archived/cleaned periodically

---

**Implementation Complete! 🎉**

The system is now automatically logging all interactions and learning from every query, correction, and feedback to continuously improve the SQL assistant's performance.
