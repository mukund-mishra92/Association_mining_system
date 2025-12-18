# SQL Assistant Self-Improving Loop with LLM-as-Judge

## Overview

The SQL Assistant now features an **intelligent self-improving loop** where an LLM acts as a judge to iteratively refine SQL queries until optimal results are achieved. This ensures higher quality responses with better schema alignment and more accurate results.

---

## How It Works

### Architecture

```
User Question
    ↓
Generate Initial SQL (using schema + context)
    ↓
Execute Query
    ↓
╔══════════════════════════════════════════╗
║  SELF-IMPROVING LOOP (Max 3 iterations)  ║
╠══════════════════════════════════════════╣
║  1. Basic Validation (confidence score)  ║
║  2. LLM Judge Evaluation                 ║
║  3. Check Exit Conditions                ║
║  4. Generate Improved Query              ║
║  5. Execute Improved Query               ║
║  6. Repeat or Exit                       ║
╚══════════════════════════════════════════╝
    ↓
Return Best Result (only final output to user)
```

---

## Key Features

### 1. **LLM Judge Evaluation**

The judge evaluates:
- **Correctness**: Does SQL match user's intent?
- **Schema Alignment**: Are correct tables/columns used?
- **Result Quality**: Do results make sense? Right row count?
- **Optimization**: Can the query be improved?

**Judge Output:**
```json
{
    "is_satisfactory": true/false,
    "confidence": 0.0-1.0,
    "issues": ["Wrong table used", "Missing time filter"],
    "suggestions": ["Use order_master instead", "Add DATE filter"],
    "improved_query": "SELECT ... (improved SQL)"
}
```

### 2. **Iterative Refinement**

- **Maximum Iterations**: 3 (configurable via `max_refinement_iterations`)
- **Judge Confidence Threshold**: 0.85 (configurable via `judge_confidence_threshold`)
- Each iteration:
  1. Validates current results
  2. Gets judge feedback
  3. Generates improved query based on feedback
  4. Executes improved query
  5. Compares with previous best

### 3. **Exit Conditions**

The loop stops when ANY of these conditions are met:

| Condition | Threshold | Description |
|-----------|-----------|-------------|
| **Judge Satisfied** | confidence ≥ 0.85 | Judge approves with high confidence |
| **Very High Confidence** | confidence ≥ 0.90 | Basic validation shows excellent results |
| **Max Iterations** | 3 iterations | Safety limit reached |
| **Improvement Failed** | N/A | Cannot generate better query |

### 4. **Best Result Tracking**

Throughout iterations, system tracks:
- Best SQL query
- Best results
- Best confidence score
- Returns the BEST result found, even if last iteration failed

---

## Configuration

### Adjustable Parameters

Located in `SQLAssistantService.__init__()`:

```python
# Maximum refinement iterations
self.max_refinement_iterations = 3

# Judge confidence threshold to stop iterating
self.judge_confidence_threshold = 0.85
```

**Recommendations:**
- **Fast Responses**: Set `max_refinement_iterations = 1` (no refinement)
- **Balanced**: `max_refinement_iterations = 3` (default)
- **Maximum Quality**: `max_refinement_iterations = 5`

---

## Example Flow

### User Query
```
"Show me all orders from today"
```

### Iteration 1: Initial Query
```sql
SELECT * FROM order_master WHERE DATE(created_at) = CURDATE()
```
- **Results**: 0 rows
- **Confidence**: 0.3
- **Judge Evaluation**:
  - Issue: "Wrong table - order_master might not have today's data"
  - Suggestion: "Try wms_to_wcs_order_line_request_data table"

### Iteration 2: Improved Query
```sql
SELECT * FROM wms_to_wcs_order_line_request_data 
WHERE DATE(INSERTED_TIMESTAMP) = CURDATE()
```
- **Results**: 150 rows
- **Confidence**: 0.85
- **Judge Evaluation**:
  - Issue: "Good table, but returning all columns"
  - Suggestion: "Select specific columns for clarity"

### Iteration 3: Final Optimized Query
```sql
SELECT ORDER_ID, ORDER_LINE_ID, ARTICLE_ID, QUANTITY, INSERTED_TIMESTAMP 
FROM wms_to_wcs_order_line_request_data 
WHERE DATE(INSERTED_TIMESTAMP) = CURDATE()
```
- **Results**: 150 rows with relevant columns
- **Confidence**: 0.92
- **Judge**: ✅ Satisfactory (0.90 confidence)

**Final Response to User:**
```
🔄 Query Refinement: Improved through 3 iterations for optimal results.

Found 150 orders from today:

ORDER_ID | ORDER_LINE_ID | ARTICLE_ID | QUANTITY | TIMESTAMP
---------|---------------|------------|----------|----------
ORD001   | LINE001       | SKU123     | 10       | 2025-12-18 08:30
...
```

---

## Benefits

### 1. **Higher Accuracy**
- Automatically corrects table/column selection
- Adapts to schema structure
- Reduces wrong results

### 2. **Better Schema Utilization**
- Learns which tables actually contain data
- Discovers optimal JOIN patterns
- Finds alternative data sources

### 3. **Improved User Experience**
- Users get correct results on first try
- No need to rephrase questions
- Transparent refinement process

### 4. **Self-Learning**
- Each iteration learns from mistakes
- Builds understanding of schema relationships
- Improves over time

---

## Implementation Details

### Core Methods

#### `_judge_query_quality()`
```python
def _judge_query_quality(
    question: str,
    sql_query: str,
    results: List[Dict],
    schema_context: str,
    iteration: int
) -> Dict[str, Any]
```

Evaluates query quality using LLM as judge.

**Returns:**
```python
{
    'is_satisfactory': bool,
    'confidence': float,
    'issues': List[str],
    'suggestions': List[str],
    'improved_query': Optional[str]
}
```

#### `_refine_query_with_judge_feedback()`
```python
def _refine_query_with_judge_feedback(
    question: str,
    original_sql: str,
    judgment: Dict,
    schema_context: str,
    conversation_context: Optional[Dict]
) -> Optional[str]
```

Generates improved SQL based on judge's feedback.

#### `_prepare_result_summary_for_judge()`
```python
def _prepare_result_summary_for_judge(
    results: List[Dict]
) -> str
```

Creates concise result summary for judge evaluation.

---

## Logging & Monitoring

### Refinement History Tracked

Each successful response includes:
```python
metadata={
    'refinement_iterations': 3,
    'refinement_history': [
        {
            'iteration': 1,
            'sql': '...',
            'confidence': 0.3,
            'judge_confidence': 0.4,
            'is_satisfactory': False,
            'issues': [...],
            'suggestions': [...]
        },
        # ... more iterations
    ]
}
```

### Logs
```
🔁 Self-refinement iteration 1/3
📊 Validation: confidence=0.30
🧑‍⚖️ Judge: satisfactory=False, confidence=0.40
🔄 Executing improved query (iteration 2)
✨ Improved query executed successfully
📈 Refinement summary: 3 iterations, final confidence: 0.92
```

---

## Performance Considerations

### Response Time
- **Without Refinement**: ~2-4 seconds
- **With 1-2 Iterations**: ~5-8 seconds
- **With 3 Iterations**: ~8-12 seconds

### Token Usage
- **Base Query**: ~1,500 tokens
- **Per Iteration**: +800 tokens (judge) + 400 tokens (refinement)
- **3 Iterations**: ~5,000 tokens total

### Optimization Tips

1. **Early Exit**: High confidence stops early
2. **Schema Caching**: Reuses schema context
3. **Parallel Validation**: Judge runs alongside basic validation
4. **Smart Iteration**: Only refines when improvements are possible

---

## Future Enhancements

### Planned Features

1. **Adaptive Iteration Count**
   - Learn optimal iteration count per query type
   - Skip refinement for simple queries

2. **Multi-Judge System**
   - Multiple specialized judges (schema expert, performance expert)
   - Consensus-based decisions

3. **Query Templates**
   - Cache successful patterns
   - Reuse for similar queries

4. **Performance Tracking**
   - Monitor iteration effectiveness
   - Auto-tune thresholds

---

## Usage Examples

### Simple Query (1 Iteration)
```python
# Question: "Count active bots"
# Initial query is perfect → exits after 1 iteration
SELECT COUNT(*) FROM bot_master WHERE status='active'
# Result: Immediate response
```

### Complex Query (3 Iterations)
```python
# Question: "Show me SKUs with high velocity that were picked today"
# Iteration 1: Wrong table
# Iteration 2: Missing JOIN
# Iteration 3: Optimized with proper JOINs and filters
# Result: Accurate multi-table query
```

### Failed Query (Uses Best Attempt)
```python
# Question: "Show me xyz data from nonexistent table"
# All iterations fail
# Returns: Best attempt with low confidence warning
```

---

## Troubleshooting

### Issue: Too Many Iterations
**Solution**: Reduce `max_refinement_iterations` to 2

### Issue: Slow Responses
**Solution**: Increase `judge_confidence_threshold` to 0.90 for faster exit

### Issue: Judge Always Unsatisfied
**Solution**: Check schema context - may be incomplete

### Issue: No Improvement Between Iterations
**Solution**: Verify LLM has sufficient context about schema

---

## Conclusion

The self-improving loop with LLM-as-judge dramatically improves SQL query quality through:
- Intelligent evaluation
- Iterative refinement
- Best result tracking
- Transparent process

Users receive **only the final, optimal result** without seeing intermediate iterations.

---

**Last Updated**: December 18, 2025
