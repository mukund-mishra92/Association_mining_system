# SQL Assistant Self-Improving Loop - Quick Reference

## 🎯 Overview
LLM-as-Judge iteratively refines SQL queries until optimal results are achieved. **Users see only the final result.**

## ⚙️ Configuration

```python
# In SQLAssistantService.__init__()
self.max_refinement_iterations = 3        # Max loops (1-5 recommended)
self.judge_confidence_threshold = 0.85    # Stop when judge satisfied (0.8-0.95)
```

## 🔄 How It Works

```
1. Generate SQL → Execute
2. Judge Evaluates (quality, schema, results)
3. If not satisfied → Generate Improved SQL
4. Execute Improved → Repeat
5. Return Best Result (stop at max iterations or high confidence)
```

## 🛑 Exit Conditions

| Condition | Value | Action |
|-----------|-------|--------|
| Judge Satisfied | confidence ≥ 0.85 | ✅ Stop, return result |
| Very High Confidence | ≥ 0.90 | ✅ Stop, return result |
| Max Iterations | 3 | ✅ Stop, return best found |
| Can't Improve | N/A | ✅ Stop, return current |

## 📊 Judge Evaluation

**Checks:**
- ✓ Correct tables/columns used?
- ✓ Results make sense?
- ✓ Right number of rows?
- ✓ Schema properly utilized?

**Returns:**
```json
{
  "is_satisfactory": true/false,
  "confidence": 0.85,
  "issues": ["Wrong table"],
  "suggestions": ["Use order_master"],
  "improved_query": "SELECT ..."
}
```

## 💡 Example

**User:** "Show orders from today"

### Iteration 1
```sql
SELECT * FROM order_log WHERE date=CURDATE()
```
Result: 0 rows → Judge: "Try order_master table"

### Iteration 2
```sql
SELECT * FROM wms_to_wcs_order_line_request_data 
WHERE DATE(INSERTED_TIMESTAMP)=CURDATE()
```
Result: 150 rows → Judge: ✅ Satisfactory (0.90)

**Final Response:**
```
🔄 Query refined through 2 iterations
Found 150 orders from today...
```

## 🎛️ Tuning Guide

| Scenario | `max_iterations` | `threshold` |
|----------|------------------|-------------|
| Fast responses | 1-2 | 0.90 |
| **Balanced** ⭐ | 3 | 0.85 |
| Maximum quality | 4-5 | 0.80 |

## 📈 Performance

- **No refinement**: 2-4s
- **2 iterations**: 5-8s  
- **3 iterations**: 8-12s

## 🔍 Monitoring

Check logs for:
```
🔁 Self-refinement iteration X/3
🧑‍⚖️ Judge: satisfactory=True, confidence=0.90
📈 Refinement summary: 2 iterations, final confidence: 0.92
```

## ⚡ Quick Tips

1. **Reduce iterations** if users complain about speed
2. **Increase threshold** (0.90) for faster exit
3. **Check refinement_history** in metadata to debug
4. Judge uses same schema context as initial query

## 🚀 Best Practices

✅ **DO:**
- Let it run for complex multi-table queries
- Monitor iteration counts in logs
- Adjust thresholds based on use case

❌ **DON'T:**
- Set iterations > 5 (diminishing returns)
- Set threshold < 0.75 (quality issues)
- Disable for simple queries (auto-exits fast anyway)

## 🔧 Troubleshooting

**Problem**: Always uses max iterations
**Fix**: Increase `judge_confidence_threshold` to 0.90

**Problem**: Slow responses
**Fix**: Reduce `max_refinement_iterations` to 2

**Problem**: No improvements happening
**Fix**: Verify schema context is complete

---

**Full Docs**: [SQL_ASSISTANT_SELF_IMPROVING_LOOP.md](SQL_ASSISTANT_SELF_IMPROVING_LOOP.md)
