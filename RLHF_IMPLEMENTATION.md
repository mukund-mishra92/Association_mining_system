# RLHF (Reinforcement Learning from Human Feedback) Implementation

## Overview

The NEO Chatbot now includes a comprehensive RLHF system that learns from user feedback to continuously improve response quality across all three chatbot modules:
- **SQL Assistant**
- **Knowledge Base**  
- **Diagnostic Support**

This implementation enables the system to identify high-quality response patterns and provide improvement suggestions based on real user interactions.

---

## Architecture

### Core Components

#### 1. **RLHFService** (`rlhf_service.py`)
Central service handling all RLHF operations:

**Key Methods:**
- `record_feedback()` - Records user feedback with detailed ratings
- `get_response_suggestions()` - Provides improvement tips based on learned patterns
- `get_analytics()` - Generates performance metrics and trends
- `_calculate_reward()` - Converts feedback to numerical reward (-1 to 1 scale)
- `_learn_patterns()` - Extracts and stores successful query-response patterns
- `_find_similar_patterns()` - Uses Jaccard similarity to match queries

**Data Storage:**
- `feedback_history.jsonl` - Append-only log of all feedback
- `reward_model.json` - Aggregate statistics per chatbot type
- `learned_patterns.json` - Last 1000 high-reward patterns per type

#### 2. **Reward Model**

Converts user feedback into numerical rewards on -1 to 1 scale:

```python
# Base reward calculation
positive feedback: +0.8
negative feedback: -0.8
neutral feedback: 0.0

# Rating adjustment (1-5 scale)
rating 5: +0.1 bonus
rating 4: +0.05 bonus
rating 3: no change
rating 2: -0.05 penalty
rating 1: -0.1 penalty

# Comment bonus
comment length > 20 chars: +0.1
```

**Examples:**
- Positive + Rating 5 + Comment = 0.8 + 0.1 + 0.1 = **1.0** (perfect)
- Positive + Rating 3 = 0.8 + 0.0 = **0.8**
- Negative + Rating 1 + Comment = -0.8 - 0.1 + 0.1 = **-0.8**
- Neutral = **0.0**

#### 3. **Pattern Learning**

The system learns from high-reward responses (score ≥ 0.7):

1. **Keyword Extraction**: Extracts important keywords from queries
2. **Pattern Storage**: Stores query-response pairs with metadata
3. **Similarity Matching**: Uses Jaccard coefficient on keywords to find analogous queries
4. **Rolling Window**: Keeps last 1000 patterns per chatbot type

**Pattern Structure:**
```json
{
  "query": "Show me all active bots",
  "response": "SELECT * FROM bot_master WHERE status = 'active'",
  "reward_score": 0.95,
  "keywords": ["show", "active", "bots"],
  "timestamp": "2025-11-13T16:00:00",
  "metadata": {
    "sql_query": "SELECT * FROM bot_master WHERE status = 'active'",
    "confidence": 0.95,
    "row_count": 42
  }
}
```

#### 4. **Analytics Engine**

Generates comprehensive performance metrics:

**Metrics Calculated:**
- Total feedback count
- Average reward score
- Feedback distribution (positive/negative/neutral)
- Weekly improvement trends
- Top 5 performing patterns
- Queries needing improvement (reward < 0.3)
- Learning rate (first half vs second half comparison)

**API Response:**
```json
{
  "total_feedback": 150,
  "average_reward": 0.72,
  "feedback_distribution": {
    "positive": 95,
    "negative": 25,
    "neutral": 30
  },
  "weekly_trends": [
    {
      "week": "2025-W45",
      "average_reward": 0.75,
      "feedback_count": 42
    }
  ],
  "top_patterns": [...],
  "needs_improvement": [...],
  "learning_rate": 0.15
}
```

---

## Integration Points

### SQL Assistant Integration

**Location:** `app/modules/neo_chatbot/services/sql_assistant_service.py`

**Automatic Feedback Recording:**
```python
# After successful SQL query generation (confidence >= 0.75)
self.rlhf_service.record_feedback(
    chatbot_type="sql_assistant",
    query=chat_request.message,
    response=response_text,
    feedback_type="neutral",  # Auto-logged
    rating=None,
    comment="Auto-generated with high confidence",
    metadata={
        "sql_query": sql_query,
        "confidence": confidence,
        "row_count": len(results),
        "strategy": strategy,
        "attempt": attempt + 1
    }
)
```

### Knowledge Base Integration

**Location:** `app/modules/neo_chatbot/services/knowledge_base_service.py`

**Automatic Feedback Recording:**
```python
# After generating RAG-based response
self.rlhf_service.record_feedback(
    chatbot_type="knowledge_base",
    query=chat_request.message,
    response=response_text,
    feedback_type="neutral",
    rating=None,
    comment=f"Auto-generated ({query_type} query)",
    metadata={
        "query_type": query_type,  # SIMPLE_FACT, PROCEDURAL, etc.
        "confidence": confidence,
        "source_count": len(source_documents),
        "document_names": [doc.document_name for doc in source_documents[:3]]
    }
)
```

### Diagnostic Support Integration

**Location:** `app/modules/neo_chatbot/services/diagnostic_service.py`

**Automatic Feedback Recording:**
```python
# After generating diagnostic response
self.rlhf_service.record_feedback(
    chatbot_type="diagnostic_support",
    query=chat_request.message,
    response=response_text,
    feedback_type="neutral",
    rating=None,
    comment=f"Auto-generated diagnostic response ({'matched' if matching_issues else 'general'})",
    metadata={
        "matched_issues_count": len(matching_issues),
        "best_match_title": best_match.get('title') if matching_issues else None,
        "confidence": confidence,
        "suggested_actions_count": len(suggested_actions)
    }
)
```

---

## API Endpoints

### 1. Record Feedback
**POST** `/api/chatbot/rlhf/feedback`

Submit detailed user feedback with ratings and comments.

**Request Body:**
```json
{
  "chatbot_type": "sql_assistant",
  "query": "Show me all active bots",
  "response": "SELECT * FROM bot_master WHERE status = 'active'",
  "feedback_type": "positive",
  "rating": 5,
  "comment": "Perfect query! Exactly what I needed.",
  "metadata": {
    "sql_query": "SELECT * FROM bot_master WHERE status = 'active'",
    "confidence": 0.95,
    "session_id": "abc123"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Thank you for your detailed feedback!",
  "feedback_id": "f8648de9-2b9f-4704-916a-873bd6403865",
  "reward_score": 1.0
}
```

### 2. Get Analytics
**GET** `/api/chatbot/rlhf/analytics`

Retrieve performance metrics and learning trends.

**Query Parameters:**
- `chatbot_type` (optional): Filter by specific chatbot type
- `days` (optional, default=30): Number of days to analyze

**Example:**
```
GET /api/chatbot/rlhf/analytics?chatbot_type=sql_assistant&days=7
```

**Response:**
```json
{
  "total_feedback": 42,
  "average_reward": 0.85,
  "feedback_distribution": {
    "positive": 30,
    "negative": 5,
    "neutral": 7
  },
  "weekly_trends": [
    {
      "week": "2025-W45",
      "average_reward": 0.85,
      "feedback_count": 42
    }
  ],
  "top_patterns": [
    {
      "query": "Show all active bots",
      "reward": 0.95,
      "count": 8
    }
  ],
  "needs_improvement": [
    {
      "query": "Complex join query",
      "reward": 0.25
    }
  ],
  "learning_rate": 0.12
}
```

### 3. Get Improvement Suggestions
**POST** `/api/chatbot/rlhf/suggestions`

Get suggestions to improve a response based on learned patterns.

**Request Body:**
```json
{
  "chatbot_type": "sql_assistant",
  "query": "Show me bot information",
  "response": "SELECT * FROM bots",
  "metadata": {
    "sql_query": "SELECT * FROM bots"
  }
}
```

**Response:**
```json
{
  "similar_patterns_count": 4,
  "suggestion_score": 0.92,
  "similar_patterns": [
    {
      "query": "Show all bots",
      "response_snippet": "SELECT * FROM bot_master WHERE status = 'active'",
      "reward_score": 0.95,
      "similarity_score": 0.67
    }
  ],
  "improvement_tips": [
    "Consider using bot_master table instead of bots",
    "Add WHERE clause to filter active bots",
    "Include LIMIT clause for better performance"
  ]
}
```

---

## Frontend UI

### Enhanced Feedback Interface

The chatbot UI now includes a sophisticated feedback system with:

**Features:**
1. **Quick Actions**: Thumbs up/down buttons for initial feedback
2. **Detailed Ratings**: 1-5 star rating system
3. **Comments**: Optional text field for detailed feedback
4. **Visual Feedback**: Success messages with reward scores

**User Flow:**
1. User receives chatbot response
2. Clicks "👍 Yes" or "👎 No"
3. Detailed feedback form appears with:
   - Star rating (1-5) - pre-filled based on initial feedback
   - Comment textarea
   - Submit/Cancel buttons
4. After submission, displays thank you message with reward score
5. Toast notification confirms feedback recorded

**Code Location:** `app/web/templates/chatbot.html`

**Key Functions:**
- `addFeedbackButtons()` - Adds feedback section to response
- `showDetailedFeedback()` - Shows detailed rating form
- `selectRating()` - Handles star rating selection
- `submitDetailedFeedback()` - Submits to RLHF API
- `cancelDetailedFeedback()` - Cancels and resets form

---

## Usage Examples

### Example 1: Recording Positive Feedback Programmatically

```python
from app.modules.neo_chatbot.services.rlhf_service import RLHFService

rlhf = RLHFService()

feedback = rlhf.record_feedback(
    chatbot_type="sql_assistant",
    query="Count all orders",
    response="SELECT COUNT(*) FROM orders",
    feedback_type="positive",
    rating=5,
    comment="Exactly what I needed!",
    metadata={"sql_query": "SELECT COUNT(*) FROM orders", "confidence": 0.92}
)

print(f"Reward Score: {feedback['reward_score']}")  # Output: 1.0
```

### Example 2: Getting Analytics

```python
# Get analytics for all chatbots (last 30 days)
analytics = rlhf.get_analytics()

print(f"Total Feedback: {analytics['total_feedback']}")
print(f"Average Reward: {analytics['average_reward']}")
print(f"Learning Rate: {analytics['learning_rate']}")

# Get analytics for specific chatbot (last 7 days)
sql_analytics = rlhf.get_analytics(chatbot_type="sql_assistant", days=7)
```

### Example 3: Getting Improvement Suggestions

```python
suggestions = rlhf.get_response_suggestions(
    chatbot_type="sql_assistant",
    query="Show bot status",
    current_response="SELECT * FROM bots",
    metadata={"sql_query": "SELECT * FROM bots"}
)

print(f"Similar Patterns Found: {suggestions['similar_patterns_count']}")
print(f"Suggestion Score: {suggestions['suggestion_score']}")

for tip in suggestions['improvement_tips']:
    print(f"💡 {tip}")
```

---

## Testing

### Run Test Suite

```bash
python test_rlhf_system.py
```

**Test Coverage:**
1. ✅ Feedback recording for all chatbot types
2. ✅ Pattern learning from high-reward feedback
3. ✅ Analytics generation
4. ✅ Response improvement suggestions
5. ✅ Reward calculation with various inputs

**Expected Output:**
```
======================================================================
TEST SUMMARY
======================================================================
Total Tests: 5
✅ Passed: 5
❌ Failed: 0

🎉 ALL TESTS PASSED! RLHF system is working correctly.
```

### Manual Testing Steps

1. **Start Flask Server:**
   ```bash
   python app/web/main.py
   ```

2. **Open Chatbot UI:**
   ```
   http://localhost:5000/chatbot
   ```

3. **Test Feedback Flow:**
   - Ask SQL Assistant: "Show me all active bots"
   - Click "👍 Yes" on the response
   - Select 5 stars
   - Add comment: "Perfect query!"
   - Click "Submit Feedback"
   - Verify success message with reward score

4. **Check Analytics:**
   ```bash
   curl http://localhost:5000/api/chatbot/rlhf/analytics
   ```

5. **View Learned Patterns:**
   ```bash
   cat app/modules/neo_chatbot/data/rlhf/learned_patterns.json
   ```

---

## Data Files

### feedback_history.jsonl
Append-only log of all feedback (one JSON object per line):

```jsonl
{"feedback_id": "abc123", "timestamp": "2025-11-13T16:00:00", "chatbot_type": "sql_assistant", "query": "Show bots", "response": "SELECT * FROM bot_master", "feedback_type": "positive", "rating": 5, "comment": "Perfect!", "reward_score": 1.0, "metadata": {...}}
{"feedback_id": "def456", "timestamp": "2025-11-13T16:05:00", "chatbot_type": "knowledge_base", "query": "What is receiving?", "response": "...", "feedback_type": "positive", "rating": 4, "comment": "Good", "reward_score": 0.85, "metadata": {...}}
```

### reward_model.json
Aggregate statistics per chatbot type:

```json
{
  "sql_assistant": {
    "total_feedback": 150,
    "positive_count": 95,
    "negative_count": 25,
    "neutral_count": 30,
    "average_reward": 0.72,
    "last_updated": "2025-11-13T16:30:00"
  },
  "knowledge_base": {...},
  "diagnostic_support": {...}
}
```

### learned_patterns.json
Last 1000 high-reward patterns per chatbot type:

```json
{
  "sql_assistant": [
    {
      "query": "Show all active bots",
      "response": "SELECT * FROM bot_master WHERE status = 'active'",
      "reward_score": 0.95,
      "keywords": ["show", "active", "bots"],
      "timestamp": "2025-11-13T16:00:00",
      "metadata": {...}
    }
  ],
  "knowledge_base": [...],
  "diagnostic_support": [...]
}
```

---

## Performance Metrics

### Learning Rate Calculation

Compares first half vs second half of feedback window:

```python
learning_rate = avg_reward_second_half - avg_reward_first_half
```

**Interpretation:**
- **Positive**: System improving over time ✅
- **Zero**: Stable performance
- **Negative**: Performance declining (investigate!)

### Weekly Trends

Groups feedback by week and calculates average reward:

```python
{
  "week": "2025-W45",
  "average_reward": 0.85,
  "feedback_count": 42
}
```

Visualize trends to monitor continuous improvement.

---

## Best Practices

### 1. Encourage User Feedback
- Add clear feedback buttons to every response
- Make rating and comments optional (reduce friction)
- Show thank you messages to acknowledge contributions

### 2. Monitor Analytics Regularly
- Check weekly trends for improvement
- Investigate queries with low rewards (< 0.3)
- Celebrate top performing patterns with team

### 3. Act on Insights
- Review "needs improvement" list
- Update documentation based on high-reward patterns
- Refine prompts using learned preferences

### 4. Balance Automatic vs Manual Feedback
- Auto-log neutral feedback for baseline data
- Prioritize explicit user feedback for learning
- Don't overwhelm logs with low-quality auto-feedback

### 5. Data Retention
- Archive old feedback_history.jsonl periodically
- Keep last 90 days in active file
- Maintain learned_patterns at 1000 per type (rolling window)

---

## Troubleshooting

### Issue: No patterns being learned

**Cause:** Not enough high-reward feedback (≥ 0.7)

**Solution:**
- Check `reward_model.json` for average rewards
- Review feedback distribution (too many negatives?)
- Encourage positive feedback for good responses

### Issue: Suggestions not improving responses

**Cause:** Low similarity between queries

**Solution:**
- Use more specific queries for better pattern matching
- Increase pattern storage limit in `_learn_patterns()`
- Review keyword extraction logic

### Issue: Analytics showing negative learning rate

**Cause:** Performance declining over time

**Solution:**
- Review recent code changes to chatbot services
- Check for prompt degradation
- Investigate "needs improvement" queries
- Consider retraining or prompt refinement

---

## Future Enhancements

### Planned Features
1. **RLHF Dashboard** - Visual analytics with charts and graphs
2. **A/B Testing** - Compare different response strategies
3. **Automatic Prompt Tuning** - Adjust prompts based on feedback
4. **Multi-turn Conversation Rewards** - Track satisfaction across conversations
5. **User Segmentation** - Different reward models for power users vs beginners
6. **Export Reports** - Weekly/monthly performance reports

### Extensibility
The RLHF system is designed for easy extension:
- Add new chatbot types by passing unique `chatbot_type` string
- Customize reward calculation in `_calculate_reward()`
- Extend metadata with domain-specific fields
- Integrate with external analytics platforms

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interaction                         │
├─────────────────────────────────────────────────────────────────┤
│  Chatbot UI → Response Display → Feedback Form (⭐ 1-5, 💬)    │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     API Layer (Flask)                           │
├─────────────────────────────────────────────────────────────────┤
│  POST /api/chatbot/rlhf/feedback                               │
│  GET  /api/chatbot/rlhf/analytics                              │
│  POST /api/chatbot/rlhf/suggestions                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                   RLHF Service (Core)                           │
├─────────────────────────────────────────────────────────────────┤
│  • record_feedback()        • _calculate_reward()              │
│  • get_analytics()          • _learn_patterns()                │
│  • get_response_suggestions() • _find_similar_patterns()       │
└────────┬────────────────────┬────────────────────┬─────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ feedback_       │  │ reward_model    │  │ learned_        │
│ history.jsonl   │  │ .json           │  │ patterns.json   │
│                 │  │                 │  │                 │
│ Append-only log │  │ Aggregate stats │  │ Top patterns    │
│ All feedback    │  │ Per chatbot     │  │ Last 1000       │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         ▲                    ▲                    ▲
         │                    │                    │
         └────────────────────┴────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Chatbot Service Integrations                       │
├─────────────────────────────────────────────────────────────────┤
│  SQL Assistant   │  Knowledge Base   │  Diagnostic Support     │
│  Auto-log:       │  Auto-log:        │  Auto-log:              │
│  • sql_query     │  • query_type     │  • matched_issues       │
│  • confidence    │  • sources        │  • confidence           │
│  • row_count     │  • documents      │  • actions              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Conclusion

The RLHF implementation provides a robust foundation for continuous improvement of the NEO Chatbot system. By learning from real user feedback, the system can:

✅ Identify high-quality response patterns  
✅ Provide actionable improvement suggestions  
✅ Track performance trends over time  
✅ Optimize prompts and strategies based on data  
✅ Deliver better user experiences through continuous learning  

For questions or issues, check the troubleshooting section or review the test suite for implementation examples.
