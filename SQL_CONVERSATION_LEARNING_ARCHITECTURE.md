# SQL Assistant Conversation Learning - Architecture

## Before (Stateless Processing)

```
┌─────────────┐
│   User      │
│   Query     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│  SQL Assistant (Stateless)      │
│  • No memory                    │
│  • No context                   │
│  • No learning                  │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────┐
│   LLM       │
│ (Basic      │
│  prompt)    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   SQL       │
│  Query      │
└─────────────┘

Problems:
❌ Same errors repeated
❌ No correction memory
❌ No conversation flow
❌ User frustration
```

## After (Contextual Learning)

```
┌─────────────────────────────────────────────────────────────┐
│                    User Conversation                         │
│  Q1: "show tables"                                          │
│  Q2: "details from config_master"                           │
│  Q3: "ArticleId is wrong, use ARTICLE_ID" ← CORRECTION     │
│  Q4: "now show empty bins from live_inventory_master"      │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│           SQL Assistant (Stateful + Learning)                │
│                                                              │
│  ┌────────────────────────────────────────────────┐        │
│  │  1. Detect Correction                          │        │
│  │     • Pattern matching                         │        │
│  │     • "X is wrong, use Y"                      │        │
│  │     • Store in session_corrections             │        │
│  └────────┬───────────────────────────────────────┘        │
│           │                                                  │
│           ▼                                                  │
│  ┌────────────────────────────────────────────────┐        │
│  │  2. Extract Conversation Context               │        │
│  │     • Tables: [config_master, live_...]        │        │
│  │     • Corrections: [ArticleId → ARTICLE_ID]    │        │
│  │     • Successful queries: [Q1, Q2]             │        │
│  │     • Key insights: [empty bins logic]         │        │
│  └────────┬───────────────────────────────────────┘        │
│           │                                                  │
│           ▼                                                  │
│  ┌────────────────────────────────────────────────┐        │
│  │  3. Build Enhanced Prompt                      │        │
│  │     🔧 USER CORRECTIONS (top priority)         │        │
│  │     💡 CONTEXT from conversation               │        │
│  │     ✅ PREVIOUS successful queries             │        │
│  │     📋 TABLES discussed                        │        │
│  │     + Base system prompt + Schema              │        │
│  └────────┬───────────────────────────────────────┘        │
│           │                                                  │
└───────────┼──────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────┐
│                    LLM Service                             │
│  Enhanced Prompt with full context:                       │
│                                                            │
│  🔧 CORRECTIONS: Use ARTICLE_ID not ArticleId             │
│  💡 CONTEXT: User asking about empty bins                 │
│  ✅ PREVIOUS: SELECT * FROM config_master...              │
│  📋 TABLES: config_master, live_inventory_master          │
│  + System Rules + Schema                                  │
└────────────┬──────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────┐
│                 Corrected SQL Query                         │
│  SELECT BIN_ID FROM live_inventory_master                  │
│  WHERE ARTICLE_ID = 'no-sku'  ← Uses correct column!      │
└────────────┬───────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────┐
│              Execute & Validate                             │
│  • Run query on database                                   │
│  • Check results confidence                                │
│  • High confidence → Success!                              │
└────────────┬───────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────┐
│              Store Success for Learning                     │
│                                                             │
│  ┌───────────────────────┐   ┌───────────────────────┐   │
│  │ Session Cache         │   │  RLHF Service         │   │
│  │ (This session only)   │   │  (All sessions)       │   │
│  │                       │   │                       │   │
│  │ • Successful queries  │   │ • User corrections    │   │
│  │ • Corrections         │   │ • Feedback patterns   │   │
│  │ • Tables used         │   │ • Reward scores       │   │
│  └───────────────────────┘   └───────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

Benefits:
✅ Learns from corrections
✅ Remembers conversation
✅ Builds context
✅ Improves accuracy
✅ Happy users!
```

## Data Flow

```
┌──────────────┐
│   Request    │
│   + history  │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│  Conversation Context    │
│  Extraction              │
└──────┬───────────────────┘
       │
       ├──► Session Cache ──► Previous Queries
       │
       ├──► Session Corrections ──► User Fixes
       │
       ├──► RLHF Service ──► Historic Corrections
       │
       └──► Conversation History ──► Recent Messages
              │
              ▼
       ┌─────────────────┐
       │  Context Dict   │
       │  {              │
       │   tables: [...] │
       │   corrections:  │
       │     [{w→c}...]  │
       │   queries: [...] │
       │   insights: [...] │
       │  }              │
       └─────┬───────────┘
             │
             ▼
       ┌─────────────────┐
       │  Build Prompt   │
       │  with Context   │
       └─────┬───────────┘
             │
             ▼
       ┌─────────────────┐
       │   LLM           │
       └─────┬───────────┘
             │
             ▼
       ┌─────────────────┐
       │   SQL           │
       └─────┬───────────┘
             │
             ▼
       ┌─────────────────┐
       │  Store Success  │
       └─────────────────┘
```

## Memory Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│                    Memory Layers                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. IMMEDIATE (Current Query)                           │
│     • User's message                                     │
│     • Detected corrections                               │
│     • Generated SQL                                      │
│     Lifetime: Single request                            │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  2. SESSION (conversation_history)                      │
│     • Last 10 messages                                   │
│     • Tables discussed                                   │
│     • Corrections given                                  │
│     • Successful queries                                 │
│     Lifetime: Until session ends                        │
│     Storage: In-memory (session_query_cache)            │
│              (session_corrections)                       │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  3. PERSISTENT (RLHF)                                   │
│     • All user feedback                                  │
│     • Cross-session corrections                          │
│     • Learned patterns                                   │
│     • Reward model                                       │
│     Lifetime: Forever                                    │
│     Storage: feedback_history.jsonl                     │
│              learned_patterns.json                       │
│              reward_model.json                           │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Correction Detection Flow

```
User Message: "ArticleId is wrong the correct is Article_ID"
                        │
                        ▼
        ┌───────────────────────────────┐
        │  _detect_user_correction()    │
        │  Pattern Matching:            │
        │  • "X is wrong...correct is Y"│
        │  • "not X...should be Y"      │
        │  • "use X instead of Y"       │
        └───────────┬───────────────────┘
                    │
                    ▼
              ┌─────────┐
              │ Match!  │
              └────┬────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌───────────────┐    ┌────────────────┐
│ Extract:      │    │  Store in:     │
│ wrong:        │    │  session_      │
│  "ArticleId"  │───▶│  corrections   │
│ correct:      │    │  {session_id}  │
│  "ARTICLE_ID" │    └────────────────┘
└───────────────┘
        │
        ▼
┌───────────────────────────┐
│  Next Query:              │
│  "show bins..."           │
│         │                 │
│         ▼                 │
│  _extract_conversation_   │
│  context()                │
│         │                 │
│         ▼                 │
│  Retrieves correction:    │
│  ArticleId → ARTICLE_ID   │
│         │                 │
│         ▼                 │
│  Injects into prompt:     │
│  "🔧 Use ARTICLE_ID not   │
│      ArticleId"           │
│         │                 │
│         ▼                 │
│  LLM generates:           │
│  WHERE ARTICLE_ID = ...   │
│  ✅ CORRECT!              │
└───────────────────────────┘
```

## Key Components

### 1. SQLAssistantService
- **New Attributes:**
  - `session_query_cache: Dict[str, List]`
  - `session_corrections: Dict[str, Dict]`

- **New Methods:**
  - `_detect_user_correction()`
  - `_extract_conversation_context()`
  - `_build_context_prompt()`
  - `_store_successful_query()`
  - `_store_correction()`

### 2. RLHFService
- **New Methods:**
  - `get_sql_corrections(limit=50)`

### 3. Flow Integration
- `process_query()` now:
  1. Detects corrections
  2. Extracts context
  3. Passes context to SQL generation
  4. Stores successful queries
  5. Learns for future

## Example Context Structure

```python
context = {
    'tables_used': {
        'config_master',
        'live_inventory_master',
        'bin_configuration'
    },
    'corrections': [
        {
            'wrong': 'ArticleId',
            'correct': 'ARTICLE_ID',
            'type': 'column_name'
        },
        {
            'wrong': 'BinId',
            'correct': 'BIN_ID',
            'type': 'column_name'
        }
    ],
    'successful_queries': [
        {
            'question': 'show tables',
            'sql': 'SELECT TABLE_NAME...',
            'results_count': 183
        },
        {
            'question': 'config details',
            'sql': 'SELECT * FROM config_master...',
            'results_count': 1
        }
    ],
    'key_info': [
        "User asking about empty bins - use ARTICLE_ID='no-sku'",
        "Quantity=0 doesn't mean empty (virtual allocation)"
    ]
}
```

This context is then transformed into a prompt section that guides the LLM to use correct column names and understand the conversation flow.
