# SQL Assistant Conversation Learning - Testing Guide

## Quick Test Scenarios

### Scenario 1: The Exact User Journey (Empty Bins Issue)

This replicates the exact conversation flow the user experienced:

```javascript
// Test conversation sequence
const testConversation = [
  {
    query: "give me all the table available in the database",
    expectedSQL: "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE()",
    shouldSucceed: true
  },
  {
    query: "show me details from config_master",
    expectedSQL: "SELECT * FROM config_master",
    shouldSucceed: true
  },
  {
    query: "how many bin are available or free from live_inventory_master where ArticleId='no-sku'",
    expectedSQL: "SELECT COUNT(DISTINCT BIN_ID) AS available_bins FROM live_inventory_master WHERE ARTICLE_ID = 'no-sku'",
    note: "Should auto-correct ArticleId to ARTICLE_ID"
  },
  {
    query: "ArticleId is wrong the correct is Article_ID",
    type: "correction",
    shouldDetect: true,
    correction: { wrong: "ArticleId", correct: "Article_ID" }
  },
  {
    query: "Quantity is 0 not means ,bin is empty because we have virtual quantity allocation which acculumate in quantity post put operation",
    type: "clarification",
    shouldAddToContext: true
  },
  {
    query: "now give me how many bin are available or free from live_inventory_master where ArticleId='no-sku'",
    expectedSQL: "SELECT COUNT(DISTINCT BIN_ID) AS available_bins FROM live_inventory_master WHERE ARTICLE_ID = 'no-sku'",
    shouldUseCorrection: true,
    note: "MUST use ARTICLE_ID (from correction), not ArticleId"
  }
];
```

### How to Test via UI

1. **Open Chatbot Interface** (http://localhost:8000/chatbot)

2. **Switch to SQL Assistant Mode**

3. **Execute the conversation sequence:**

```
You: give me all the table available in the database
Bot: [Shows table list with TABLE_NAME column]

You: show me details from config_master  
Bot: [Shows config_master data with all columns]

You: how many bin are available or free from live_inventory_master where ArticleId='no-sku'
Bot: [Should auto-correct to ARTICLE_ID and return count]

You: ArticleId is wrong the correct is Article_ID
Bot: [Should acknowledge and store correction]

You: Quantity is 0 not means ,bin is empty because we have virtual quantity allocation
Bot: [Should understand this is a clarification]

You: now give me how many bin are available or free from live_inventory_master where ArticleId='no-sku'
Bot: [CRITICAL: Should use ARTICLE_ID correctly based on previous correction]
```

### Expected Log Outputs

Look for these in the logs to confirm it's working:

```
✅ "📚 Extracted context: 2 tables, 1 corrections, 1 insights"
✅ "🔧 Stored correction: 'ArticleId' → 'Article_ID'"
✅ "📋 Using 1 relevant tables in schema"
```

### What Should Happen

#### ✅ Success Indicators:
1. **Context Building**: Each query includes previous tables and corrections in prompt
2. **Correction Detection**: "ArticleId is wrong..." triggers correction storage
3. **Correction Application**: Final query uses ARTICLE_ID instead of ArticleId
4. **Session Memory**: System remembers config_master and live_inventory_master tables
5. **High Confidence**: Final result shows 95% confidence with correct SQL

#### ❌ Failure Indicators:
1. Repeats same column name error after correction
2. Doesn't remember previous tables discussed
3. Low confidence (<50%) on simple queries
4. No context extracted from conversation history

## Scenario 2: Multi-Correction Learning

Test that system handles multiple corrections in one session:

```
You: Show me orders where OrderId = 123
Bot: [May use wrong column name]

You: OrderId is wrong, use ORDER_ID
Bot: [Stores correction]

You: Also, CustomerId should be CUSTOMER_ID
Bot: [Stores second correction]

You: Now show me orders where OrderId = 123 and CustomerId = 456
Bot: [Should use both corrections: ORDER_ID and CUSTOMER_ID]
```

## Scenario 3: Cross-Session Learning (RLHF)

Test that corrections persist across sessions:

**Session 1:**
```
You: count bins
Bot: [Generates query]

You: [Provides negative feedback with comment: "Use BIN_ID not bin_id"]
```

**Session 2 (new browser/session):**
```
You: how many bins are there?
Bot: [Should use BIN_ID correctly based on RLHF learning]
```

## API Testing (curl/Postman)

### Test with conversation_history:

```bash
curl -X POST http://localhost:8000/api/neo-chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "show me empty bins from live_inventory_master",
    "chatbot_type": "sql_assistant",
    "session_id": "test-session-123",
    "conversation_history": [
      {
        "role": "user",
        "content": "how many bins where ArticleId='no-sku'"
      },
      {
        "role": "assistant",
        "content": "[Previous SQL result]"
      },
      {
        "role": "user",
        "content": "ArticleId is wrong, use ARTICLE_ID"
      }
    ]
  }'
```

### Expected Response:

```json
{
  "response": "Found X results: ...",
  "sql_query": "SELECT BIN_ID FROM live_inventory_master WHERE ARTICLE_ID = 'no-sku' LIMIT 100;",
  "confidence_score": 0.95,
  "chatbot_type": "sql_assistant",
  "session_id": "test-session-123"
}
```

Note the SQL uses `ARTICLE_ID` (correct) not `ArticleId` (wrong).

## Debugging Tips

### Check Session Cache:

Add this to your test to inspect session state:

```python
# In Python console or test file
from app.modules.neo_chatbot.services.sql_assistant_service import SQLAssistantService

service = SQLAssistantService()

# After running some queries
print("Session cache:", service.session_query_cache)
print("Session corrections:", service.session_corrections)
```

### Check RLHF Data:

```python
from app.modules.neo_chatbot.services.rlhf_service import RLHFService

rlhf = RLHFService()
corrections = rlhf.get_sql_corrections(limit=10)
print("Recent corrections:", corrections)
```

### Enable Debug Logging:

Add to your `.env`:
```
LOG_LEVEL=DEBUG
```

## Success Metrics

After implementing, you should see:

| Metric | Before | After |
|--------|--------|-------|
| First-try success rate | 60% | 85%+ |
| Queries needing retry | 40% | 15% |
| User corrections needed | Multiple | 1 (remembered) |
| Average confidence | 75% | 90%+ |
| User satisfaction | Frustrated | Satisfied |

## Troubleshooting

### Issue: Corrections not being detected

**Check:**
- Is `conversation_history` being passed in ChatRequest?
- Is `session_id` consistent across queries?
- Check logs for "🔧 Stored correction" message

### Issue: Context not being used

**Check:**
- Is `_extract_conversation_context` being called?
- Check logs for "📚 Extracted context" message
- Verify conversation_history format matches ChatMessage schema

### Issue: SQL still using wrong column names

**Check:**
- Is correction in the correct format? (wrong → correct)
- Check system prompt includes "🔧 USER CORRECTIONS" section
- Verify LLM is seeing the enhanced prompt (check LLM service logs)

## Next Steps After Testing

1. **Monitor RLHF feedback** - Check `app/modules/neo_chatbot/data/rlhf/feedback_history.jsonl`
2. **Review correction patterns** - Analyze what corrections are most common
3. **Update documentation** - Add discovered patterns to system prompt
4. **A/B Testing** - Compare old vs new system performance

---

**Key Test to Pass:** User should never have to repeat the same correction twice in one session.
