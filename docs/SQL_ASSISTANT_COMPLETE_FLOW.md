# SQL Assistant Complete Flow Documentation

## Overview

This document provides a complete end-to-end flow of how the SQL Assistant processes user queries, generates SQL, executes queries, learns from interactions, and provides responses.

---

## High-Level Flow

```
User Query → Intent Classification → Context Extraction → SQL Generation → 
Query Execution → Result Validation → Response Formatting → Logging → Response
```

---

## Detailed Flow with Code References

### 1. **User Sends Query** 
**Endpoint**: `POST /api/chatbot/chat`  
**File**: `app/modules/neo_chatbot/api/chatbot_endpoints.py`

```python
# Line ~38
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Route to SQL assistant
    if request.chatbot_type == ChatbotType.SQL_ASSISTANT:
        response = sql_service.process_query(request)
```

**Input**:
```json
{
  "message": "how many orders do we have today",
  "chatbot_type": "sql_assistant",
  "session_id": "user-session-123",
  "conversation_history": [...]  // Optional
}
```

---

### 2. **Entry Point: process_query()**
**File**: `app/modules/neo_chatbot/services/sql_assistant_service.py`  
**Line**: ~868

```python
def process_query(self, chat_request: ChatRequest) -> ChatResponse:
    start_time = datetime.now()  # For timing
    chat_id = None
```

**Initial Steps**:
1. ✅ Start timer for performance tracking
2. ✅ Check database availability
3. ✅ Initialize chat_id for logging

---

### 3. **User Correction Detection**
**File**: `sql_assistant_service.py`  
**Method**: `_detect_user_correction()`  
**Line**: ~420

```python
# Line ~886
is_correction = self._detect_user_correction(
    chat_request.message, 
    chat_request.session_id
)
```

**What it does**:
- Checks if user is providing a correction
- Patterns: "actually use X", "X is wrong", "should be Y", "use Y instead"
- Stores correction in `session_corrections` dict

**Example**:
```
User: "show orders where ArticleId = 123"
Bot: [wrong result]
User: "actually use ARTICLE_ID instead"  ← Detected as correction
```

---

### 4. **Auto-Correct Column Names (Fuzzy Matching)**
**File**: `sql_assistant_service.py`  
**Method**: `_extract_and_correct_column_names()`  
**Line**: ~1160

```python
# Line ~889
corrected_message, auto_corrections = self._extract_and_correct_column_names(
    chat_request.message
)
```

**Process**:
1. Extract potential column names from query using regex
2. Find mentioned tables in the query
3. For each column, use fuzzy matching with `difflib.SequenceMatcher`
4. If similarity > 0.6, auto-correct the column name
5. Return corrected message and list of corrections

**Example**:
```python
Input:  "show orders where ArticleId = 123"
        ↓ (fuzzy match finds ARTICLE_ID with 0.85 similarity)
Output: "show orders where ARTICLE_ID = 123"
Corrections: [{'table': 'sku_master', 'wrong': 'ArticleId', 'correct': 'ARTICLE_ID'}]
```

**Logged to**: `session_corrections` + `chatbot_column_corrections` table

---

### 5. **Extract Conversation Context**
**File**: `sql_assistant_service.py`  
**Method**: `_extract_conversation_context()`  
**Line**: ~440

```python
# Line ~907
conversation_context = self._extract_conversation_context(
    chat_request.conversation_history,
    chat_request.session_id
)
```

**What it extracts**:
```python
{
    'tables_mentioned': [],        # Tables from past queries
    'corrections': [],             # User corrections in this session
    'successful_queries': [],      # Past successful SQL queries
    'recent_topics': [],           # Recent discussion topics
    'rlhf_corrections': []         # Cross-session learnings from RLHF
}
```

**Sources**:
1. `conversation_history` - last 10 messages from current chat
2. `session_corrections` - corrections in this session
3. `session_query_cache` - successful queries in this session
4. `rlhf_service.get_sql_corrections()` - corrections from other sessions

---

### 6. **Classify Query Intent**
**File**: `sql_assistant_service.py`  
**Method**: `_classify_query_intent()`  
**Line**: ~68

```python
# Line ~953 (inside loop)
intent_info = self._classify_query_intent(chat_request.message)
```

**What it detects**:
```python
{
    'intent': 'count' | 'retrieve' | 'aggregate' | 'metadata',
    'entities': ['bin', 'order', 'sku', 'bot', 'alarm', ...],
    'operations': ['count', 'sum', 'average', ...],
    'time_filter': True/False,
    'join_needed': True/False,
    'is_metadata_query': True/False  # e.g., "show columns"
}
```

**Intent Detection Logic**:
- **count**: Keywords like "how many", "count", "total"
- **aggregate**: Keywords like "sum", "average", "total quantity"
- **retrieve**: Default for SELECT queries
- **metadata**: Keywords like "column names", "show columns", "table structure"

**Entity Detection**:
- Checks for domain entities: bin, order, sku, bot, alarm, maintenance, velocity, configuration

**Time Filter Detection**:
- Keywords: "today", "yesterday", "last week", "past 7 days"

---

### 7. **Map Entities to Tables**
**File**: `sql_assistant_service.py`  
**Method**: `_get_tables_for_entities()`  
**Line**: ~155

```python
# Called within _build_query_guidance()
tables = self._get_tables_for_entities(entities)
```

**Entity → Table Mappings**:
```python
{
    'bin': ['bin_master', 'bin_config', 'bin_stock_details', 'bin_velocity_analysis'],
    'order': ['order_master', 'order_line', 'wms_to_wcs_order_line_request_data'],
    'sku': ['sku_master', 'sku_velocity_analysis'],
    'bot': ['bot_master_log', 'bot_alarm_log', 'bot_charging_bit_log'],
    'alarm': ['bot_alarm_log', 'bot_manual_alarm_log'],
    'maintenance': ['dashboard_log_maintenance_task_master'],
    'velocity': ['bin_velocity_analysis', 'sku_velocity_analysis'],
    'configuration': ['bin_config', 'wcs_config']
}
```

---

### 8. **Detect Required JOINs**
**File**: `sql_assistant_service.py`  
**Method**: `_get_join_paths()`  
**Line**: ~237

```python
# Called within _build_query_guidance()
join_hints = self._get_join_paths(entities, tables)
```

**Known JOIN Relationships**:
```python
[
    {
        'tables': ['order_master', 'sku_master'],
        'condition': 'order_master.SKU_ID = sku_master.SKU_ID'
    },
    {
        'tables': ['bin_master', 'bin_config'],
        'condition': 'bin_master.BIN_ID = bin_config.BIN_ID'
    },
    {
        'tables': ['bot_master_log', 'bot_alarm_log'],
        'condition': 'bot_master_log.BOT_ID = bot_alarm_log.BOT_ID'
    },
    # ... 3 more relationships
]
```

---

### 9. **Build Query Guidance for LLM**
**File**: `sql_assistant_service.py`  
**Method**: `_build_query_guidance()`  
**Line**: ~273

```python
guidance = self._build_query_guidance(intent_info, context)
```

**Generates context-specific guidance**:
```python
# For COUNT queries:
"For counting queries, use COUNT(*) or COUNT(DISTINCT column_name). 
Include appropriate WHERE clauses..."

# For METADATA queries:
"Use INFORMATION_SCHEMA.COLUMNS. Filter with TABLE_SCHEMA = DATABASE() 
and TABLE_NAME = 'table_name'. Use DISTINCT to avoid duplicates."

# For multi-entity queries:
"Multiple entities detected. Consider using JOIN:
- order_master.SKU_ID = sku_master.SKU_ID"
```

---

### 10. **Get Dynamic Schema**
**File**: `sql_assistant_service.py`  
**Method**: `_get_system_prompt()`  
**Line**: ~324

```python
system_prompt = self._get_system_prompt(question, context)
```

**What it includes**:
1. **Relevant schema only** (not all 183 tables!)
2. **Table names** matching entities
3. **Column details** for those tables
4. **Conversation context** (corrections, past queries)
5. **Query-specific guidance** (from step 9)

**Example Schema**:
```
Relevant tables for your query:
1. sku_master (ARTICLE_ID, SKU_ID, QUANTITY, ...)
2. order_master (ORDER_ID, SKU_ID, STATUS, ...)

Past corrections:
- Use ARTICLE_ID not ArticleId in sku_master

Successful query pattern:
- Similar query used: SELECT COUNT(*) FROM order_master WHERE...
```

---

### 11. **Retry Loop with Multiple Strategies**
**File**: `sql_assistant_service.py`  
**Line**: ~912

```python
max_attempts = 3
strategies = ['direct', 'with_context', 'simplified']

for attempt in range(max_attempts):
    strategy = strategies[min(attempt, len(strategies) - 1)]
    
    # Step 11.1: Generate SQL
    sql_query = self._generate_sql_with_strategy(...)
    
    # Step 11.2: Execute SQL
    results, error = self._execute_query_safe(sql_query)
    
    # Step 11.3: Validate results
    confidence, validation_msg = self._validate_results(...)
    
    # Step 11.4: If confident enough, return
    if confidence >= 0.75:
        break  # Success!
```

**Strategy Details**:

#### **Strategy 1: Direct** (attempt 1)
```python
prompt = f"Convert to SQL: {question}"
```
- Simplest approach
- Let LLM figure it out with schema

#### **Strategy 2: With Context** (attempt 2)
```python
prompt = f"""User question: {question}

Generate MySQL query to answer this question. Return ONLY the SQL."""
```
- More explicit instructions
- Include conversation context

#### **Strategy 3: Simplified** (attempt 3)
```python
prompt = f"Generate simple SQL for: {question}. Keep it basic with proper table names."
```
- Fallback to basics
- Focus on correct table/column names

---

### 12. **SQL Generation**
**File**: `sql_assistant_service.py`  
**Method**: `_generate_sql_with_strategy()`  
**Line**: ~1240

```python
response = self.llm_service.generate_response(
    messages=[{"role": "user", "content": prompt}],
    system_prompt=system_prompt,  # With schema + context
    max_tokens=300,
    temperature=0.1  # Low temperature for consistency
)
```

**LLM receives**:
- System prompt with relevant schema
- Conversation context and corrections
- Query-specific guidance
- User's question

**LLM returns**:
```sql
SELECT COUNT(*) 
FROM order_master 
WHERE DATE(CREATED_AT) = CURDATE()
```

---

### 13. **Extract SQL from LLM Response**
**File**: `sql_assistant_service.py`  
**Method**: `_extract_sql_query()`  
**Line**: ~1145

```python
sql_query = self._extract_sql_query(response)
```

**Extraction logic**:
1. Look for SQL code blocks: \`\`\`sql ... \`\`\`
2. Look for SQL keywords: SELECT, INSERT, UPDATE, DELETE, WITH
3. Extract until semicolon or end
4. Clean and return

---

### 14. **Execute Query Safely**
**File**: `sql_assistant_service.py`  
**Method**: `_execute_query_safe()`  
**Line**: ~1276

```python
results, error = self._execute_query_safe(sql_query)
```

**Safety checks**:
```python
# 1. Block dangerous operations
dangerous_patterns = [
    r'\bDROP\s+TABLE\b',
    r'\bDROP\s+DATABASE\b',
    r'\bDELETE\s+FROM\b',
    r'\bTRUNCATE\b',
    r'\bALTER\s+TABLE\b',
    r'\bINSERT\s+INTO\b',
    r'\bUPDATE\s+\w+\s+SET\b'
]

# 2. Execute with timeout (5 seconds)
conn = pymysql.connect(**self.db_config, connect_timeout=5)

# 3. Use pandas for safe execution
df = pd.read_sql(sql_query, conn)
results = df.to_dict('records')
```

**Returns**:
```python
# On success:
(results, None)  # results = list of dicts

# On error:
([], error_message)  # error = string
```

**If error occurs**:
- Log to chat history on final attempt
- Continue to next strategy attempt

---

### 15. **Validate Results**
**File**: `sql_assistant_service.py`  
**Method**: `_validate_results()`  
**Line**: ~1321

```python
confidence, validation_msg = self._validate_results(
    results, 
    chat_request.message, 
    sql_query
)
```

**Validation criteria**:
```python
confidence_score = 0.5  # Base confidence

# Boost confidence if:
if results is not None:
    confidence_score += 0.2
    
if results and len(results) > 0:
    confidence_score += 0.1
    
# Check if intent matches results
if intent == 'count' and len(results) == 1:
    confidence_score += 0.15  # Good!
    
if intent == 'retrieve' and len(results) > 1:
    confidence_score += 0.1  # Expected multiple rows
    
# Validate column names exist
if expected_columns_found:
    confidence_score += 0.1
```

**Returns**:
```python
(0.92, "Query returned expected count result")
# OR
(0.45, "Results don't match query intent")
```

---

### 16. **Decision: Return or Retry?**

```python
if confidence >= 0.75:
    # ✅ SUCCESS PATH - Go to step 17
    response_text = self._format_results_with_confidence(...)
    
else:
    # ⚠️ RETRY PATH - Go back to step 11 with next strategy
    continue
```

**Confidence thresholds**:
- ≥ 0.75: Return to user ✅
- < 0.75: Try next strategy 🔄
- After 3 attempts: Return low-confidence response ⚠️

---

### 17. **Format Response (Success Path)**
**File**: `sql_assistant_service.py`  
**Method**: `_format_results_with_confidence()`  
**Line**: ~1503

```python
response_text = self._format_results_with_confidence(
    results, 
    sql_query, 
    original_message,
    confidence,
    validation_msg
)
```

**Response includes**:
```
✅ Found 45 orders today

**Results:**
| ORDER_ID | SKU_ID | QUANTITY | STATUS |
|----------|--------|----------|--------|
| 12345    | 100    | 50       | ACTIVE |
| 12346    | 101    | 30       | PENDING|

**SQL Query Used:**
```sql
SELECT ORDER_ID, SKU_ID, QUANTITY, STATUS 
FROM order_master 
WHERE DATE(CREATED_AT) = CURDATE()
LIMIT 100
```

**Confidence:** 92%
```

**Auto-correction note** (if applicable):
```
ℹ️ Auto-corrected column names: 'ArticleId' → 'ARTICLE_ID'
```

---

### 18. **Comprehensive Logging** ⭐ NEW
**File**: `sql_assistant_service.py`  
**Line**: ~968-1041

#### **18.1: Calculate Metrics**
```python
response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
intent_info = self._classify_query_intent(chat_request.message)
tables_used = self._extract_tables_from_sql(sql_query)
columns_used = self._extract_columns_from_sql(sql_query)
```

#### **18.2: Log Chat Interaction**
```python
chat_id = self.chat_history_service.log_chat_interaction(
    session_id=chat_request.session_id,
    chatbot_type="sql_assistant",
    user_query=chat_request.message,
    assistant_response=response_text,
    confidence_score=confidence,
    response_time_ms=response_time_ms
)
```
**Stored in**: `chatbot_chat_history` table

#### **18.3: Log SQL Query Details**
```python
self.chat_history_service.log_sql_query(
    chat_id=chat_id,
    session_id=chat_request.session_id,
    user_query=chat_request.message,
    generated_sql=sql_query,
    execution_status='success',
    rows_returned=len(results),
    execution_time_ms=response_time_ms,
    tables_used=tables_used,
    columns_used=columns_used,
    intent=intent_info.get('intent'),
    entities=intent_info.get('entities')
)
```
**Stored in**: `chatbot_sql_queries` table

#### **18.4: Log Auto-Corrections**
```python
for corr in auto_corrections:
    self.chat_history_service.log_column_correction(
        session_id=chat_request.session_id,
        table_name=corr.get('table', 'unknown'),
        wrong_column=corr['wrong'],
        correct_column=corr['correct'],
        correction_type='automatic',
        similarity_score=corr.get('similarity', 0.0),
        chat_id=chat_id
    )
```
**Stored in**: `chatbot_column_corrections` table

#### **18.5: Update Query Patterns**
```python
# Log intent pattern
self.chat_history_service.update_query_pattern(
    pattern_type='intent',
    pattern_key=intent_info.get('intent', 'unknown'),
    pattern_value=chat_request.message[:200],
    success=True,
    confidence=confidence
)

# Log entity-table patterns
for entity in intent_info.get('entities', []):
    if tables_used:
        self.chat_history_service.update_query_pattern(
            pattern_type='entity_table',
            pattern_key=entity,
            pattern_value=','.join(tables_used[:3]),
            success=True,
            confidence=confidence
        )
```
**Stored in**: `chatbot_query_patterns` table

#### **18.6: Log to RLHF (Cross-Session Learning)**
```python
self.rlhf_service.record_feedback(
    chatbot_type="sql_assistant",
    query=chat_request.message,
    response=response_text,
    feedback_type="neutral",
    rating=None,
    comment="Auto-generated with high confidence",
    metadata={
        "sql_query": sql_query,
        "confidence": confidence,
        "row_count": len(results),
        "strategy": strategy,
        "attempt": attempt + 1,
        "auto_corrections": auto_corrections
    }
)
```
**Stored in**: `app/modules/neo_chatbot/data/rlhf/feedback_history.jsonl`

---

### 19. **Session Cache Update**
**File**: `sql_assistant_service.py`  
**Method**: `_store_successful_query()`  
**Line**: ~542

```python
self._store_successful_query(
    chat_request.session_id,
    chat_request.message,
    sql_query,
    len(results)
)
```

**Stores in memory**:
```python
self.session_query_cache[session_id].append({
    'question': question,
    'sql': sql,
    'results_count': results_count,
    'timestamp': datetime.now().isoformat()
})
```

**Used for**: Next queries in same session have context

---

### 20. **Return ChatResponse**
**File**: `sql_assistant_service.py`  
**Line**: ~1068

```python
return ChatResponse(
    response=response_text,
    chatbot_type=ChatbotType.SQL_ASSISTANT,
    session_id=chat_request.session_id,
    sql_query=sql_query,
    query_results=results[:100],  # Limit to 100 rows
    confidence_score=confidence,
    sources=[]
)
```

---

### 21. **API Endpoint Returns to Client**
**File**: `chatbot_endpoints.py`  
**Line**: ~55

```python
# Add assistant response to in-memory session
chat_sessions[session_id].append({
    "role": "assistant",
    "content": response.response
})

return response  # FastAPI serializes to JSON
```

---

## Error Handling Flow

### If Query Execution Fails

**File**: `sql_assistant_service.py`  
**Line**: ~927

```python
if error:
    logger.warning(f"⚠️ Query execution error (attempt {attempt + 1}): {error}")
    
    # Log failed query (on last attempt only)
    if self.chat_history_service and attempt == max_attempts - 1:
        chat_id = self.chat_history_service.log_chat_interaction(...)
        self.chat_history_service.log_sql_query(
            execution_status='failed',
            error_message=error[:500]
        )
    
    continue  # Try next strategy
```

### If All Attempts Fail

**Method**: `_create_low_confidence_response()`  
**Line**: ~1563

```python
return self._create_low_confidence_response(
    sql_query if sql_query else "Could not generate SQL",
    chat_request.session_id,
    chat_request.message
)
```

**Returns**:
```
I generated a SQL query for your question, but I'm not confident in the results.

**Your Question:** how many orders today

**Generated SQL:**
```sql
SELECT COUNT(*) FROM order_master WHERE ...
```

**Issue:** The query execution didn't return results I'm confident about.

💡 **Suggestions:**
1. Try rephrasing your question with more specific details
2. Check if the data exists for the time period mentioned
3. Review the SQL query above and run it manually if needed
```

---

## Learning Flow (Happens in Background)

### Pattern Recognition

**Every successful query updates**:
```
chatbot_query_patterns table:
├── Intent patterns (count, retrieve, aggregate)
├── Entity-table mappings (order → order_master)
└── Success rates and frequencies
```

### Column Mapping Learning

**Every auto-correction stores**:
```
chatbot_column_corrections table:
├── Table name
├── Wrong column name
├── Correct column name
├── Similarity score
└── Frequency count
```

**After 3+ occurrences**: Appears in improvement suggestions

### Error Pattern Detection

**Every failed query tracks**:
```
chatbot_sql_queries table (status='failed'):
├── Error message
├── Failed SQL
├── Tables attempted
└── Frequency analysis
```

**Analytics identify**: Most common error patterns

---

## Data Flow Summary

```
┌─────────────────────────────────────────────────────────────┐
│                        User Query                            │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  1. Correction Detection (manual corrections)                │
│  2. Auto-Correction (fuzzy column matching)                  │
│  3. Context Extraction (past queries, corrections)           │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  4. Intent Classification (count/retrieve/aggregate)         │
│  5. Entity Detection (bin/order/sku/bot)                     │
│  6. Table Mapping (entities → database tables)               │
│  7. JOIN Detection (multi-table relationships)               │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  8. Build Query Guidance (intent-specific hints)             │
│  9. Get Dynamic Schema (only relevant tables)                │
│ 10. Generate System Prompt (schema + context + guidance)     │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                   RETRY LOOP (up to 3 attempts)              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 11. Generate SQL (via LLM with strategy)             │   │
│  │ 12. Extract SQL from response                        │   │
│  │ 13. Execute Query (with safety checks)               │   │
│  │ 14. Validate Results (confidence scoring)            │   │
│  │                                                       │   │
│  │ If confidence >= 0.75: ✅ SUCCESS → Exit loop        │   │
│  │ If confidence < 0.75:  🔄 RETRY → Next strategy      │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 15. Format Response (results table + SQL + confidence)       │
│ 16. Calculate Metrics (response time, tables/columns used)   │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│               COMPREHENSIVE LOGGING (NEW!)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 17. Log chat interaction → chatbot_chat_history      │   │
│  │ 18. Log SQL query details → chatbot_sql_queries      │   │
│  │ 19. Log auto-corrections → chatbot_column_corrections│   │
│  │ 20. Update query patterns → chatbot_query_patterns   │   │
│  │ 21. Log to RLHF → feedback_history.jsonl            │   │
│  │ 22. Update session cache → in-memory                 │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              Return Response to User                         │
└─────────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  BACKGROUND LEARNING (Continuous)                            │
│  • Pattern frequency analysis                                │
│  • Success rate calculation                                  │
│  • Column mapping learning                                   │
│  • Error pattern detection                                   │
│  • Performance monitoring                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Tables Used

### 1. **chatbot_chat_history**
```sql
Stores: Every chat interaction
Fields: chat_id, session_id, user_query, assistant_response, 
        confidence_score, response_time_ms, timestamp
Purpose: Complete conversation history
```

### 2. **chatbot_sql_queries**
```sql
Stores: SQL query details
Fields: chat_id, generated_sql, execution_status (success/failed),
        error_message, rows_returned, execution_time_ms,
        tables_used, columns_used, intent, entities
Purpose: Query analytics and debugging
```

### 3. **chatbot_column_corrections**
```sql
Stores: Column name corrections
Fields: table_name, wrong_column, correct_column, 
        correction_type (automatic/manual), similarity_score
Purpose: Learn common column name mistakes
```

### 4. **chatbot_feedback**
```sql
Stores: User feedback
Fields: chat_id, feedback_type (positive/negative/neutral),
        rating (1-5), comment
Purpose: Manual feedback for improvement
```

### 5. **chatbot_query_patterns**
```sql
Stores: Learned patterns
Fields: pattern_type, pattern_key, pattern_value,
        frequency, success_rate, avg_confidence
Purpose: Pattern recognition and optimization
```

---

## Key Services Used

### 1. **LLMService** (`llm_service.py`)
- Communicates with OpenAI/Azure OpenAI
- Generates SQL from natural language
- Temperature: 0.1 (consistent outputs)
- Max tokens: 300 (SQL queries)

### 2. **RLHFService** (`rlhf_service.py`)
- Records feedback across sessions
- Retrieves past corrections
- Learns from manual feedback
- Stores in JSONL format

### 3. **ChatHistoryService** (`chat_history_service.py`) ⭐ NEW
- Logs all interactions to database
- Provides analytics APIs
- Generates improvement suggestions
- Tracks patterns and success rates

### 4. **SchemaParser** (`schema_parser.py`)
- Parses database schema from HTML
- Returns table and column info
- Used for dynamic schema loading

---

## Performance Optimizations

### 1. **Dynamic Schema Loading**
- Only loads relevant tables (not all 183!)
- Based on entities detected in query
- Reduces LLM token usage significantly

### 2. **Retry with Different Strategies**
- Start simple, get progressively more explicit
- Max 3 attempts to avoid wasted time
- Early exit on high confidence

### 3. **Query Timeout**
- 5-second timeout on database queries
- Prevents hanging on slow queries
- Returns error for retry

### 4. **Result Limiting**
- Max 100 rows returned to user
- Prevents huge responses
- Can be adjusted based on needs

### 5. **Async Logging**
- Logging doesn't block response
- Failures logged as warnings only
- System continues even if logging fails

---

## Confidence Scoring Logic

```python
Base: 0.5

+0.2 → Results not None
+0.1 → Results have rows
+0.15 → Intent matches (count query returns 1 row)
+0.1 → Intent matches (retrieve query returns multiple rows)
+0.1 → Expected columns found in results

Total: 0.50 - 1.05 (capped at 1.0)

Threshold: 0.75 (75% confidence required)
```

---

## Example End-to-End Trace

**Query**: "how many orders do we have today"

```
1. ✅ Correction detection: None
2. ✅ Auto-correction: None (no column names to correct)
3. ✅ Context extraction: Found 2 past successful queries
4. ✅ Intent classification: 'count', entities: ['order'], time_filter: True
5. ✅ Entity mapping: order → [order_master, order_line, ...]
6. ✅ JOIN detection: None needed (single entity)
7. ✅ Query guidance: "Use COUNT(*) with DATE filter for today"
8. ✅ Dynamic schema: Loaded order_master table details
9. ✅ System prompt: Built with schema + context
10. ✅ Attempt 1 (direct strategy):
    - Generated SQL: SELECT COUNT(*) FROM order_master WHERE DATE(CREATED_AT) = CURDATE()
    - Executed: Success, 1 row returned: [{count: 45}]
    - Validation: Confidence 0.92 (count intent matched)
11. ✅ Format response: Table with 45 orders
12. ✅ Logged to chatbot_chat_history
13. ✅ Logged to chatbot_sql_queries (status=success, rows=1)
14. ✅ Updated query_patterns (intent=count, frequency++)
15. ✅ Logged to RLHF feedback
16. ✅ Stored in session cache
17. ✅ Response returned in 245ms

Result: User gets accurate count with high confidence!
```

---

## Verification Checklist

Use this to verify the system is working:

- [ ] User query reaches `process_query()`
- [ ] Corrections detected if present
- [ ] Auto-corrections applied via fuzzy matching
- [ ] Context extracted from conversation history
- [ ] Intent classified correctly
- [ ] Entities detected
- [ ] Tables mapped to entities
- [ ] JOINs suggested if needed
- [ ] Dynamic schema loaded (not all 183 tables)
- [ ] SQL generated by LLM
- [ ] SQL extracted from response
- [ ] Query executed safely (no DROP/DELETE)
- [ ] Results validated
- [ ] Confidence calculated
- [ ] Response formatted
- [ ] Chat interaction logged to DB
- [ ] SQL query details logged to DB
- [ ] Corrections logged to DB
- [ ] Patterns updated in DB
- [ ] RLHF feedback recorded
- [ ] Session cache updated
- [ ] Response returned to user

---

## Common Issues & Solutions

### Issue: Low confidence scores
**Check**: 
- Intent classification accuracy
- Table mapping correctness
- Column names in schema

### Issue: Wrong tables used
**Check**:
- Entity detection working?
- Entity-table mappings correct?
- Dynamic schema loading relevant tables?

### Issue: Column name errors
**Check**:
- Fuzzy matching threshold (currently 0.6)
- Column corrections being logged?
- Schema parser loading correct columns?

### Issue: Slow responses
**Check**:
- Database query timeout (5s)
- LLM response time
- Number of retry attempts

### Issue: No logging in database
**Check**:
- ChatHistoryService initialized?
- Database tables created?
- Database permissions?
- Check logs for errors

---

**This is the complete flow! Use this document to verify each step is working correctly.** 🚀
