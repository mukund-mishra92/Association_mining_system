# Dynamic Response Formatting - User Intent Classification

## Problem Solved

Previously, the diagnostic support system always used the same rigid format regardless of user intent:

```
Root Cause
What I Found  
Solution
Next Steps
```

This caused awkward responses when users asked simple questions like:
- "what is your criteria to check active bots" → They want to see the SQL query/logic, not a full diagnosis
- "show me all tasks for this bot" → They want data, not troubleshooting
- "what should I check to prevent this" → They want recommendations, not root cause analysis

## Solution: Intent-Driven Dynamic Formatting

### How It Works

```
User Query
    ↓
1. CLASSIFY INTENT (using LLM)
    ↓
2. DETERMINE RESPONSE FORMAT
    ↓
3. GATHER DATA (SQL queries, historical logs, docs)
    ↓
4. SYNTHESIZE RESPONSE (using format matched to intent)
    ↓
5. RETURN CONTEXTUALLY APPROPRIATE ANSWER
```

### Intent Types

The system now detects 5 types of user intent:

| Intent Type | User Wants | Response Format |
|-------------|-----------|-----------------|
| **DATA_QUERY** | See raw data/query results | Brief answer + data table/list |
| **EXPLAIN_CRITERIA** | Understand how system checks something | Explanation of logic + SQL query |
| **TROUBLESHOOT** | Diagnose a problem | Full diagnostic (Root Cause → Solution) |
| **RECOMMENDATION** | Get advice/best practices | Actionable recommendations |
| **SHOW_QUERY** | See the SQL query | SQL query + explanation |

### Examples

#### 1. DATA_QUERY
**User:** "why you are giving only one task. is this only one task assigned to this bot_id till now"

**Old Response:**
```
Root Cause: The bot has only one task because...
What I Found: Query showed 1 task...
Solution: To assign more tasks...
Next Steps: Check task allocation...
```

**New Response:**
```
Yes, there is only 1 task assigned to bot BOT-0011. Here's what I found:

| Task Count |
|------------|
| 1          |

This bot currently has a single task in the system. If you expect more, 
check the task allocation logic or wave configuration.
```

---

#### 2. EXPLAIN_CRITERIA
**User:** "what is your criteria to check the active bots"

**Old Response:**
```
Root Cause: The system checks active bots by...
What I Found: There are 0 active bots...
Solution: Activate bots by...
Next Steps: Run activation query...
```

**New Response:**
```
The system checks active bots using this criteria:

```sql
SELECT COUNT(*) as total_bots, 
       SUM(CASE WHEN STATUS='ACTIVE' THEN 1 ELSE 0 END) as active_bots 
FROM bot_master;
```

**How it works:**
1. Queries the `bot_master` table
2. Counts total bots in the system
3. Filters for STATUS = 'ACTIVE' to get active count
4. A bot is considered "active" when its STATUS field is explicitly 'ACTIVE'

**Thresholds:**
- STATUS must be 'ACTIVE' (not 'IDLE', 'CHARGING', 'OFFLINE')
- No time-based criteria - purely status-driven
```

---

#### 3. TROUBLESHOOT (Default Diagnostic)
**User:** "why bots are not coming to the station"

**Response:** (Full diagnostic format - unchanged)
```
## Root Cause
The bots are not coming to the station because there are no active bots 
available, as indicated by active_bots = 0.

## What I Found
- Total bots: 48, but active_bots: 0
- 2 tasks in PROCESSING status
- Pending bin assignments may be blocking allocation

## Solution
1. Check order_bin_mapping for bins in pending state
2. Verify put_wave_order_master for wave issues
3. Review bot allocation logic
4. Check system logs for errors

## Next Steps
1. Run: SELECT * FROM order_bin_mapping WHERE STATUS='PENDING'
2. Investigate put wave orders
3. Review error logs
```

---

#### 4. SHOW_QUERY
**User:** "show me the query you use to check bot tasks"

**New Response:**
```
Here's the SQL query used to check bot tasks:

```sql
SELECT 
    BOT_ID,
    TASK_ID,
    STATUS,
    CREATED_AT,
    UPDATED_AT
FROM task_master
WHERE BOT_ID = ?
ORDER BY CREATED_AT DESC;
```

**What it does:**
- Retrieves all tasks for a specific bot
- Shows task status (ASSIGNED, IN_PROGRESS, COMPLETED)
- Orders by creation time (newest first)
- Filters by BOT_ID to get bot-specific tasks
```

---

#### 5. RECOMMENDATION
**User:** "what should I check to prevent bots getting stuck"

**New Response:**
```
To prevent bots getting stuck, regularly monitor:

**1. Task Allocation**
```sql
SELECT STATUS, COUNT(*) FROM task_master GROUP BY STATUS;
```
- Watch for growing IN_PROGRESS count
- Alert if tasks stuck >30 minutes

**2. Station Bin Mappings**
```sql
SELECT * FROM order_bin_mapping WHERE STATUS='PENDING' AND 
CREATED_AT < NOW() - INTERVAL 15 MINUTE;
```
- Clear stale PENDING mappings
- Prevent bin location conflicts

**3. Bot Health Checks**
- Monitor battery levels (alert <20%)
- Check connectivity status every 5 minutes
- Auto-restart bots stuck in IDLE >10 minutes

**Best Practices:**
- Implement task timeout (e.g., 1 hour max)
- Add bot heartbeat monitoring
- Log state transitions for debugging
- Set up alerts for anomaly patterns
```

---

## Configuration

### Intent Classification Prompt

The LLM classifies intent using this structured prompt:

```python
classification_prompt = f"""Classify this user query to determine what type of response they expect:

User Query: "{query}"

Classify into ONE of these intent types:
1. DATA_QUERY: User wants to see raw data/query results
2. EXPLAIN_CRITERIA: User wants to understand how system checks something
3. TROUBLESHOOT: User has a problem and needs diagnosis
4. RECOMMENDATION: User wants advice/best practices
5. SHOW_QUERY: User wants to see the SQL query being used

Also determine what to include:
- show_sql_query: true/false
- show_data_table: true/false
- show_analysis: true/false
- show_solution: true/false
- response_style: "data_focused" | "explanation" | "diagnostic" | "advisory"

Respond in JSON format.
```

### Response Format Templates

Based on classified intent, the system uses different format templates:

```python
# DATA_QUERY
"""Provide a brief answer showing the relevant data. 
If you ran queries, present results in a clear table or list format.
Be concise - just answer what they asked for."""

# EXPLAIN_CRITERIA
"""Explain HOW the system checks/determines this. Show:
1. The criteria used (e.g., SQL query logic)
2. What fields/tables are checked
3. Thresholds or conditions applied
Be explanatory and technical. Show the actual SQL query if relevant."""

# SHOW_QUERY
"""Show the actual SQL query being used. Explain what each part does.
Format as: ```sql [the query] ```
Then briefly explain the logic."""

# RECOMMENDATION
"""Provide actionable recommendations:
1. What to check (with specific queries/tables)
2. Best practices to follow
3. How to prevent issues
Be advisory and forward-looking."""

# TROUBLESHOOT (default)
"""
## Root Cause
[1-2 sentences: What's wrong based on the data]

## What I Found
[3-4 bullet points of actual findings from queries]

## Solution
[3-5 numbered steps to fix it]

## Next Steps
[2-3 immediate actions]
"""
```

---

## Implementation Details

### Code Flow

```python
# intelligent_diagnostic_service.py

def diagnose_problem(self, chat_request: ChatRequest):
    problem = chat_request.message
    
    # Step 0: Classify user intent
    intent_classification = self._classify_user_intent(problem)
    # Returns: {
    #   "intent_type": "EXPLAIN_CRITERIA",
    #   "show_sql_query": true,
    #   "show_data_table": false,
    #   "show_analysis": false,
    #   "show_solution": false,
    #   "response_style": "explanation",
    #   "reasoning": "User is asking about criteria/logic"
    # }
    
    # Step 1-5: Gather data (unchanged)
    problem_analysis = self._analyze_problem_description(problem)
    historical_matches = self.support_service.search_similar_issues(problem)
    diagnostic_queries = self._generate_diagnostic_queries(...)
    diagnostic_data = self._execute_diagnostic_queries(...)
    doc_context = self._search_documentation(...)
    
    # Step 6: Synthesize solution WITH intent-driven formatting
    solution = self._synthesize_solution(
        problem=problem,
        problem_analysis=problem_analysis,
        historical_matches=historical_matches,
        diagnostic_data=diagnostic_data,
        doc_context=doc_context,
        intent_classification=intent_classification  # <-- NEW
    )
    
    # Synthesis method now uses dynamic format based on intent_type
```

### Key Methods

#### 1. `_classify_user_intent(query)`
- **Purpose**: Determine what type of response user expects
- **Input**: User's question string
- **Output**: Intent classification dict with type and formatting flags
- **LLM Model**: Uses main LLM with temp=0.2 for consistency
- **Fallback**: Defaults to TROUBLESHOOT if classification fails

#### 2. `_synthesize_solution(..., intent_classification)`
- **Purpose**: Generate response using format matched to intent
- **Enhancement**: Dynamic format selection based on intent_type
- **Prompt Engineering**: Includes 5 different format templates
- **Backward Compatible**: Defaults to TROUBLESHOOT if no intent provided

---

## Benefits

### 1. Natural Conversation Flow
Users get answers that match their expectation:
- Ask for data → Get data
- Ask for explanation → Get explanation
- Ask for help → Get diagnosis

### 2. Reduced Cognitive Load
- No need to parse full diagnostic when user just wants a query
- More scannable responses
- Faster information retrieval

### 3. Better User Experience
- System feels more intelligent and context-aware
- Responses are more concise for simple questions
- Detailed only when actually troubleshooting

### 4. Flexibility
- Can still provide full diagnostics when needed
- Adapts to user's expertise level
- Supports multiple conversation styles

---

## Testing

Run the test script to see dynamic formatting in action:

```bash
python test_dynamic_response_format.py
```

This will test all 5 intent types and show how responses adapt.

---

## Monitoring

### Intent Classification Logs

```
🎯 Intent classified: EXPLAIN_CRITERIA - User is asking about how system determines active bots
🎯 Response format: explanation
```

### Metrics to Track

1. **Intent Distribution**
   - % of queries in each intent category
   - Helps understand user behavior patterns

2. **Classification Accuracy**
   - User feedback on response appropriateness
   - Manual review of misclassified intents

3. **Response Length**
   - DATA_QUERY: Should be <100 words
   - EXPLAIN_CRITERIA: 100-200 words
   - TROUBLESHOOT: 200-300 words

---

## Future Enhancements

### 1. Multi-Intent Handling
Some queries may have multiple intents:
- "Show me bot tasks AND explain why bot-001 is stuck"
- Could split into two responses or prioritize

### 2. Learning from Feedback
- Track which intent classifications get poor ratings
- Retrain classification logic
- Add new intent types based on patterns

### 3. Conversational Context
- Remember previous question type
- Adapt format based on conversation flow
- E.g., "Show me more" after DATA_QUERY → more data

### 4. User Preference
- Allow users to set preferred response style
- Power users might always want to see SQL
- Beginners might prefer more explanation

---

## Troubleshooting

### Intent Misclassification

**Problem**: System classifies "show bot status" as TROUBLESHOOT instead of DATA_QUERY

**Solution**: 
1. Check intent classification prompt
2. Add more examples to training
3. Adjust temperature (currently 0.2)

### JSON Parsing Errors

**Problem**: LLM returns text instead of JSON

**Solution**:
```python
# Already handled with regex extraction
json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', response, re.DOTALL)
if json_match:
    response = json_match.group(1)
intent_data = json.loads(response)
```

### Fallback Behavior

If intent classification fails, system defaults to TROUBLESHOOT (full diagnostic) - safest option that includes all information.

---

## Summary

The dynamic response formatting enhancement makes the diagnostic system:
- ✅ **Contextually aware** - Understands user intent
- ✅ **Flexible** - Adapts format to question type
- ✅ **Natural** - Responds how users expect
- ✅ **Efficient** - Concise when appropriate, detailed when needed
- ✅ **Backward compatible** - Still supports full diagnostics

Users now get **the right type of answer** for their question, not a one-size-fits-all response.
