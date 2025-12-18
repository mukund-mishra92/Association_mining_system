# SQL Assistant Self-Improving Loop - Visual Flow Diagram

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER SENDS QUERY                            │
│                  "Show me all orders from today"                    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SQL ASSISTANT RECEIVES                           │
│                   • Extracts context                                │
│                   • Applies auto-corrections                        │
│                   • Gets schema info                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  GENERATE INITIAL SQL QUERY                         │
│              SELECT * FROM order_master                             │
│              WHERE date = CURDATE()                                 │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      EXECUTE QUERY                                  │
│                    Result: 0 rows                                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
╔═════════════════════════════════════════════════════════════════════╗
║              SELF-IMPROVING LOOP (Max 3 iterations)                 ║
╠═════════════════════════════════════════════════════════════════════╣
║                                                                     ║
║  ┌───────────────────────────────────────────────────────────┐    ║
║  │              ITERATION 1                                  │    ║
║  ├───────────────────────────────────────────────────────────┤    ║
║  │  1. BASIC VALIDATION                                      │    ║
║  │     • Row count: 0                                        │    ║
║  │     • Confidence: 0.30                                    │    ║
║  │                                                           │    ║
║  │  2. LLM JUDGE EVALUATION                                  │    ║
║  │     Judge analyzes:                                       │    ║
║  │     ✗ Wrong table used                                    │    ║
║  │     ✗ No results returned                                 │    ║
║  │     → Suggestion: Try wms_to_wcs_order_line_request_data  │    ║
║  │     → is_satisfactory: False                              │    ║
║  │     → judge_confidence: 0.40                              │    ║
║  │                                                           │    ║
║  │  3. CHECK EXIT CONDITIONS                                 │    ║
║  │     ✗ Not satisfied (0.40 < 0.85)                         │    ║
║  │     ✗ Not max iterations (1 < 3)                          │    ║
║  │     → Continue to improvement                             │    ║
║  │                                                           │    ║
║  │  4. GENERATE IMPROVED QUERY                               │    ║
║  │     SELECT * FROM wms_to_wcs_order_line_request_data      │    ║
║  │     WHERE DATE(INSERTED_TIMESTAMP) = CURDATE()            │    ║
║  │                                                           │    ║
║  │  5. EXECUTE IMPROVED QUERY                                │    ║
║  │     Result: 150 rows                                      │    ║
║  └───────────────────────────────────────────────────────────┘    ║
║                            │                                        ║
║                            ▼                                        ║
║  ┌───────────────────────────────────────────────────────────┐    ║
║  │              ITERATION 2                                  │    ║
║  ├───────────────────────────────────────────────────────────┤    ║
║  │  1. BASIC VALIDATION                                      │    ║
║  │     • Row count: 150                                      │    ║
║  │     • Confidence: 0.85                                    │    ║
║  │     • Update best_confidence = 0.85                       │    ║
║  │                                                           │    ║
║  │  2. LLM JUDGE EVALUATION                                  │    ║
║  │     Judge analyzes:                                       │    ║
║  │     ✓ Correct table used                                  │    ║
║  │     ✓ Results returned                                    │    ║
║  │     ⚠ Could be more specific (select columns)             │    ║
║  │     → Suggestion: Select specific columns                 │    ║
║  │     → is_satisfactory: False                              │    ║
║  │     → judge_confidence: 0.75                              │    ║
║  │                                                           │    ║
║  │  3. CHECK EXIT CONDITIONS                                 │    ║
║  │     ✗ Not satisfied (0.75 < 0.85)                         │    ║
║  │     ✗ Not max iterations (2 < 3)                          │    ║
║  │     → Continue to improvement                             │    ║
║  │                                                           │    ║
║  │  4. GENERATE IMPROVED QUERY                               │    ║
║  │     SELECT ORDER_ID, ORDER_LINE_ID, ARTICLE_ID,           │    ║
║  │            QUANTITY, INSERTED_TIMESTAMP                   │    ║
║  │     FROM wms_to_wcs_order_line_request_data               │    ║
║  │     WHERE DATE(INSERTED_TIMESTAMP) = CURDATE()            │    ║
║  │                                                           │    ║
║  │  5. EXECUTE IMPROVED QUERY                                │    ║
║  │     Result: 150 rows (with specific columns)              │    ║
║  └───────────────────────────────────────────────────────────┘    ║
║                            │                                        ║
║                            ▼                                        ║
║  ┌───────────────────────────────────────────────────────────┐    ║
║  │              ITERATION 3                                  │    ║
║  ├───────────────────────────────────────────────────────────┤    ║
║  │  1. BASIC VALIDATION                                      │    ║
║  │     • Row count: 150                                      │    ║
║  │     • Confidence: 0.92                                    │    ║
║  │     • Update best_confidence = 0.92                       │    ║
║  │                                                           │    ║
║  │  2. LLM JUDGE EVALUATION                                  │    ║
║  │     Judge analyzes:                                       │    ║
║  │     ✓ Correct table                                       │    ║
║  │     ✓ Specific columns selected                           │    ║
║  │     ✓ Proper date filter                                  │    ║
║  │     ✓ Results look correct                                │    ║
║  │     → is_satisfactory: True                               │    ║
║  │     → judge_confidence: 0.90                              │    ║
║  │                                                           │    ║
║  │  3. CHECK EXIT CONDITIONS                                 │    ║
║  │     ✅ SATISFIED: judge_confidence (0.90) >= threshold!   │    ║
║  │     → STOP ITERATING                                      │    ║
║  └───────────────────────────────────────────────────────────┘    ║
║                                                                     ║
╚═════════════════════════════════════════════════════════════════════╝
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FORMAT FINAL RESPONSE                            │
│                  • Use best SQL found (iteration 3)                 │
│                  • Use best results (150 rows)                      │
│                  • Add refinement note                              │
│                  • Confidence: 0.92                                 │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     RETURN TO USER                                  │
│  ─────────────────────────────────────────────────────────────────  │
│  🔄 Query Refinement: Improved through 3 iterations                 │
│                                                                     │
│  Found 150 orders from today:                                      │
│                                                                     │
│  ORDER_ID | ORDER_LINE_ID | ARTICLE_ID | QUANTITY | TIMESTAMP      │
│  ─────────────────────────────────────────────────────────────────  │
│  ORD001   | LINE001       | SKU123     | 10       | 2025-12-18..   │
│  ORD002   | LINE002       | SKU456     | 5        | 2025-12-18..   │
│  ...                                                                │
│                                                                     │
│  Confidence: 92%                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

## Exit Condition Decision Tree

```
                    ┌─────────────────────┐
                    │  After Validation   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Judge Evaluates    │
                    └──────────┬──────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
        ┌───────▼────────┐           ┌───────▼────────┐
        │  is_satisfactory│          │ Very High      │
        │  = True?        │          │ Confidence?    │
        │                 │          │ (>= 0.90)      │
        └───────┬─────────┘          └───────┬────────┘
                │                             │
         ┌──────▼──────┐              ┌──────▼──────┐
         │  Judge       │              │  Basic      │
         │  Confidence  │              │  Confidence │
         │  >= 0.85?    │              │  >= 0.90?   │
         └──────┬───────┘              └──────┬──────┘
                │                             │
         ┌──────▼──────┐              ┌──────▼──────┐
         │    YES      │              │    YES      │
         │  ✅ EXIT    │              │  ✅ EXIT    │
         │  RETURN     │              │  RETURN     │
         └─────────────┘              └─────────────┘
                │                             │
                NO                            NO
                │                             │
                └──────────┬──────────────────┘
                           │
                  ┌────────▼────────┐
                  │ Max Iterations  │
                  │ Reached?        │
                  │ (>= 3)          │
                  └────────┬────────┘
                           │
                    ┌──────┴──────┐
                    │             │
            ┌───────▼──────┐  ┌──▼──────┐
            │   YES        │  │   NO    │
            │   ✅ EXIT    │  │ Continue│
            │   (Use Best) │  │ Refine  │
            └──────────────┘  └────┬────┘
                                   │
                          ┌────────▼────────┐
                          │ Can Generate    │
                          │ Improved Query? │
                          └────────┬────────┘
                                   │
                            ┌──────┴──────┐
                            │             │
                    ┌───────▼──────┐  ┌──▼──────────┐
                    │   YES        │  │   NO        │
                    │ Execute      │  │  ✅ EXIT    │
                    │ Improved     │  │  (Use Best) │
                    │ → Next Loop  │  └─────────────┘
                    └──────────────┘
```

## Metadata Structure

```
ChatResponse.metadata = {
    'refinement_iterations': 3,
    'refinement_history': [
        {
            'iteration': 1,
            'sql': 'SELECT * FROM order_master WHERE...',
            'confidence': 0.30,
            'judge_confidence': 0.40,
            'is_satisfactory': False,
            'issues': [
                'Wrong table used',
                'No results returned'
            ],
            'suggestions': [
                'Try wms_to_wcs_order_line_request_data'
            ]
        },
        {
            'iteration': 2,
            'sql': 'SELECT * FROM wms_to_wcs_order_line_request_data...',
            'confidence': 0.85,
            'judge_confidence': 0.75,
            'is_satisfactory': False,
            'issues': [
                'Returns all columns unnecessarily'
            ],
            'suggestions': [
                'Select specific columns only'
            ]
        },
        {
            'iteration': 3,
            'sql': 'SELECT ORDER_ID, ORDER_LINE_ID, ARTICLE_ID...',
            'confidence': 0.92,
            'judge_confidence': 0.90,
            'is_satisfactory': True,
            'issues': [],
            'suggestions': []
        }
    ]
}
```

## Judge Evaluation Process

```
┌─────────────────────────────────────────────────────────────┐
│              LLM JUDGE EVALUATION INPUT                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User Question: "Show me all orders from today"             │
│                                                             │
│  Generated SQL:                                             │
│  SELECT * FROM order_master WHERE date = CURDATE()          │
│                                                             │
│  Execution Results:                                         │
│  - Row Count: 0                                             │
│  - Columns: []                                              │
│  - Sample Data: None                                        │
│                                                             │
│  Available Schema:                                          │
│  - order_master (id, status, date, ...)                    │
│  - wms_to_wcs_order_line_request_data (ORDER_ID, ...)      │
│  - pick_wave_order_master (...)                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  JUDGE ANALYZES                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Correctness Check:                                      │
│     ✗ Query returns no results                             │
│     ✗ Doesn't answer user's question                       │
│                                                             │
│  2. Schema Alignment:                                       │
│     ⚠ order_master may not have today's data               │
│     ✓ wms_to_wcs_order_line_request_data looks promising   │
│                                                             │
│  3. Result Quality:                                         │
│     ✗ Zero rows - likely wrong approach                    │
│                                                             │
│  4. Optimization:                                           │
│     → Should try different table                           │
│     → Check INSERTED_TIMESTAMP column                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              JUDGE OUTPUT (JSON)                            │
├─────────────────────────────────────────────────────────────┤
│  {                                                          │
│    "is_satisfactory": false,                               │
│    "confidence": 0.40,                                      │
│    "issues": [                                              │
│      "Wrong table - order_master returns no results",      │
│      "Missing TIMESTAMP column for today's filter"         │
│    ],                                                       │
│    "suggestions": [                                         │
│      "Try wms_to_wcs_order_line_request_data table",       │
│      "Use INSERTED_TIMESTAMP column with DATE() function"  │
│    ],                                                       │
│    "improved_query": "SELECT * FROM wms_to_wcs_order_...   │
│                       WHERE DATE(INSERTED_TIMESTAMP)=..."  │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
```

## Performance Timeline

```
Time →

0s ────┬──────────────────────────────────────────────────────┬──── Response
       │                                                      │
       │  Initial Generation & Execution                      │
       │  ▓▓▓▓▓▓▓▓                                           │
       │  (2s)                                                │
       │                                                      │
       ├──────────────────────────────────────────────────────┤
       │                                                      │
       │  Iteration 1                                         │
       │  ├─ Validation (0.1s)                                │
       │  ├─ Judge Evaluation (1.5s) ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓         │
       │  ├─ Refinement Generation (0.8s) ▓▓▓▓▓▓▓            │
       │  └─ Execution (0.5s) ▓▓▓                            │
       │  Total: ~2.9s                                        │
       │                                                      │
       ├──────────────────────────────────────────────────────┤
       │                                                      │
       │  Iteration 2                                         │
       │  ├─ Validation (0.1s)                                │
       │  ├─ Judge Evaluation (1.5s) ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓         │
       │  ├─ Refinement Generation (0.8s) ▓▓▓▓▓▓▓            │
       │  └─ Execution (0.5s) ▓▓▓                            │
       │  Total: ~2.9s                                        │
       │                                                      │
       ├──────────────────────────────────────────────────────┤
       │                                                      │
       │  Iteration 3                                         │
       │  ├─ Validation (0.1s)                                │
       │  ├─ Judge Evaluation (1.5s) ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓         │
       │  └─ ✅ SATISFIED - EXIT                             │
       │  Total: ~1.6s                                        │
       │                                                      │
       ├──────────────────────────────────────────────────────┤
       │                                                      │
       │  Format & Return (0.2s) ▓                           │
       │                                                      │
       └──────────────────────────────────────────────────────┘

Total Response Time: ~9.6 seconds (with 3 iterations)
```

---

**Note**: Actual times vary based on:
- LLM response speed
- Database query complexity
- Number of iterations needed
- Network latency
