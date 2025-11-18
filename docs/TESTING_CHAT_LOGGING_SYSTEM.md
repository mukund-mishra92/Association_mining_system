# Testing the Chat Logging & Analytics System

## Quick Start Testing Guide

### 1. Restart the Server

The new chat history tables will be created automatically on first use.

```bash
# Stop servers if running
.\stop_servers.bat

# Start fresh
.\quick_start.bat
```

### 2. Test Basic Query Logging

**Make a SQL query:**
```bash
curl -X POST http://localhost:8000/api/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "how many orders do we have today",
    "chatbot_type": "sql_assistant",
    "session_id": "test-session-1"
  }'
```

**Check if it was logged:**
```bash
curl http://localhost:8000/api/chatbot/history/test-session-1
```

### 3. Test Analytics Endpoints

**View query analytics:**
```bash
# Last 7 days
curl http://localhost:8000/api/chatbot/analytics/sql-queries?days=7

# Last 30 days
curl http://localhost:8000/api/chatbot/analytics/sql-queries?days=30
```

**View learned patterns:**
```bash
curl http://localhost:8000/api/chatbot/analytics/learned-patterns?limit=20
```

**View column mappings:**
```bash
curl http://localhost:8000/api/chatbot/analytics/column-mappings?min_frequency=2
```

**Get improvement suggestions:**
```bash
curl http://localhost:8000/api/chatbot/analytics/improvement-suggestions
```

### 4. Test Auto-Correction Logging

**Make a query with a column name typo:**
```bash
curl -X POST http://localhost:8000/api/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "show me orders where ArticleId = 12345",
    "chatbot_type": "sql_assistant",
    "session_id": "test-session-2"
  }'
```

**Check if correction was logged:**
```bash
curl http://localhost:8000/api/chatbot/analytics/column-mappings?min_frequency=1
```

You should see the auto-correction from `ArticleId` to `ARTICLE_ID`.

### 5. Test Feedback Submission

**First, get a chat_id from history:**
```bash
curl http://localhost:8000/api/chatbot/history/test-session-1
# Copy one of the chat_id values
```

**Submit positive feedback:**
```bash
curl -X POST http://localhost:8000/api/chatbot/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "YOUR_CHAT_ID_HERE",
    "session_id": "test-session-1",
    "feedback_type": "positive",
    "rating": 5,
    "comment": "Perfect results!"
  }'
```

**Submit negative feedback with correction:**
```bash
curl -X POST http://localhost:8000/api/chatbot/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "YOUR_CHAT_ID_HERE",
    "session_id": "test-session-1",
    "feedback_type": "negative",
    "rating": 2,
    "comment": "Should use order_master table instead"
  }'
```

### 6. Verify Database Tables

**Connect to MySQL and check tables:**
```sql
-- Show all chat history tables
SHOW TABLES LIKE 'chatbot_%';

-- View recent chat history
SELECT * FROM chatbot_chat_history 
ORDER BY timestamp DESC 
LIMIT 10;

-- View SQL query logs
SELECT 
    chat_id,
    user_query,
    execution_status,
    rows_returned,
    timestamp
FROM chatbot_sql_queries 
ORDER BY timestamp DESC 
LIMIT 10;

-- View column corrections
SELECT 
    table_name,
    wrong_column,
    correct_column,
    correction_type,
    COUNT(*) as frequency
FROM chatbot_column_corrections
GROUP BY table_name, wrong_column, correct_column, correction_type
ORDER BY frequency DESC;

-- View learned patterns
SELECT 
    pattern_type,
    pattern_key,
    frequency,
    success_rate,
    avg_confidence
FROM chatbot_query_patterns
ORDER BY frequency DESC
LIMIT 20;

-- View feedback
SELECT 
    feedback_type,
    rating,
    comment,
    timestamp
FROM chatbot_feedback
ORDER BY timestamp DESC
LIMIT 10;
```

### 7. Test Multiple Queries to Build Data

Run 10-20 queries to build up analytics data:

```bash
# Query 1: Count query
curl -X POST http://localhost:8000/api/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "how many SKUs do we have", "chatbot_type": "sql_assistant", "session_id": "test-batch-1"}'

# Query 2: Retrieve query
curl -X POST http://localhost:8000/api/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "show me all bins in zone A", "chatbot_type": "sql_assistant", "session_id": "test-batch-1"}'

# Query 3: Aggregate query
curl -X POST http://localhost:8000/api/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "total quantity of all orders", "chatbot_type": "sql_assistant", "session_id": "test-batch-1"}'

# Query 4: With typo (for auto-correction)
curl -X POST http://localhost:8000/api/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "orders where SkuId = 100", "chatbot_type": "sql_assistant", "session_id": "test-batch-1"}'

# Query 5: Metadata query
curl -X POST http://localhost:8000/api/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "show me all column names in sku_master", "chatbot_type": "sql_assistant", "session_id": "test-batch-1"}'
```

### 8. Check Analytics After Multiple Queries

```bash
# View updated analytics
curl http://localhost:8000/api/chatbot/analytics/sql-queries?days=1

# Should show:
# - Total queries: 5+
# - Success rate: XX%
# - Top tables used
# - Common intents
# - Any errors encountered
```

### 9. Test Improvement Suggestions

After running several queries (especially some with errors):

```bash
curl http://localhost:8000/api/chatbot/analytics/improvement-suggestions
```

Should return suggestions like:
- Column mappings to add
- Entity-table mappings to review
- Common errors to fix
- Performance optimization tips

## Expected Behavior

### ✅ Successful Test Indicators

1. **Chat History Endpoint**: Returns list of your queries
2. **Analytics Show Data**: Non-zero query counts and success rates
3. **Patterns Are Learned**: Repeated query types show up in patterns
4. **Corrections Are Tracked**: Auto-corrected columns appear in mappings
5. **Feedback Is Stored**: Submitted feedback appears in database
6. **Suggestions Generated**: System provides actionable improvement tips

### ⚠️ If Something Doesn't Work

**No chat history tables:**
```
Check server logs for table creation errors
Verify database permissions (CREATE TABLE)
```

**Analytics endpoints return empty data:**
```
Make sure you've run some queries first
Check that days parameter is appropriate (default: 7)
Verify session_id is correct for history endpoint
```

**Chat history service not available error:**
```
Check database connection in config
Verify sql_service.chat_history_service is initialized
Look for initialization errors in server logs
```

## Monitoring in Production

### 1. Daily Analytics Check

```bash
# Morning dashboard - check yesterday's stats
curl http://localhost:8000/api/chatbot/analytics/sql-queries?days=1

# Weekly review - check trends
curl http://localhost:8000/api/chatbot/analytics/sql-queries?days=7
```

### 2. Weekly Improvement Review

```bash
# Check for new suggestions every week
curl http://localhost:8000/api/chatbot/analytics/improvement-suggestions

# Review learned patterns
curl http://localhost:8000/api/chatbot/analytics/learned-patterns?limit=50

# Check column mappings to add
curl http://localhost:8000/api/chatbot/analytics/column-mappings?min_frequency=5
```

### 3. Performance Monitoring

Watch for:
- **Success rate trends**: Should improve over time
- **Avg execution time**: Should stay low (< 500ms)
- **Common errors**: Should decrease as fixes are applied
- **Pattern diversity**: Should increase as system learns

### 4. Database Maintenance

```sql
-- Check database size
SELECT 
    table_name,
    table_rows,
    ROUND(data_length / 1024 / 1024, 2) as size_mb
FROM information_schema.tables
WHERE table_schema = DATABASE()
    AND table_name LIKE 'chatbot_%'
ORDER BY data_length DESC;

-- Archive old data (optional, after 6+ months)
-- DELETE FROM chatbot_chat_history WHERE timestamp < DATE_SUB(NOW(), INTERVAL 6 MONTH);
```

## Troubleshooting

### Error: "Chat history service not available"

**Solution:**
```python
# Check database config in .env
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=your_database

# Restart server after config changes
```

### Error: "Table doesn't exist"

**Solution:**
```
Tables are created automatically on first use.
If creation failed, check database permissions.
User needs CREATE TABLE privilege.
```

### No data in analytics

**Solution:**
```
Run at least 5-10 queries first
Wait a few seconds for async logging
Check chatbot_sql_queries table directly in database
```

### High execution times

**Solution:**
```sql
-- Add indexes if missing
CREATE INDEX idx_session_timestamp ON chatbot_chat_history(session_id, timestamp);
CREATE INDEX idx_status_timestamp ON chatbot_sql_queries(execution_status, timestamp);
```

## Success Metrics

After running the system for a week, you should see:

- **90%+ success rate** for SQL queries
- **< 300ms average** response time
- **50+ learned patterns** 
- **10+ column mappings** identified
- **Decreasing error rates** over time
- **Specific improvement suggestions** based on real data

---

**Happy Testing! 🚀**

The system is now automatically learning from every interaction and will continuously improve based on real usage patterns.
