# Semi-Automated Diagnostic Support System

## Overview
Interactive problem diagnosis system integrated into main chatbot interface at `http://localhost:5000/chatbot`

Features:
- Matches user problems with historical support cases
- Prioritizes by impact (High/Medium/Low)
- Executes SQL queries to audit problems
- Suggests next solution if user says "not correct"
- Point-to-point communication (no paragraphs)

## Quick Start

1. **Navigate to Chatbot**: `http://localhost:5000/chatbot`
2. **Select "Semi-Auto Diagnostic"** button in chatbot selector
3. **Describe problem**: e.g., "Bot is not moving"
4. **Review matched case** with impact and solution
5. **Run SQL audit** if available (optional)
6. **Choose action**:
   - ✓ **This Solved It** - Problem resolved
   - ✗ **Not Correct** - Try next solution

## How to Use

## Key Features

### 1. **Problem Matching**
- Uses similarity search on problem statements
- Returns top 5 most relevant cases
- Sorts by impact priority (High > Medium > Low)

### 2. **Impact-Based Prioritization**
- **High Impact**: Most effective solution first (costly if mistake)
- **Medium Impact**: Balanced approach
- **Low Impact**: Standard solutions

### 3. **SQL Audit**
- Executes SQL queries to verify problem exists
- Compares results with expected outcome
- Provides data-driven diagnosis

### 4. **Multi-Case Verification**
- User tests each solution
- If "not correct" → suggests next possible cause
- Iterates through all matched cases

## API Endpoints

### Start Diagnosis
```http
POST /api/chatbot/diagnostic/start?problem_description=bot not moving
```

**Response:**
```json
{
  "session_id": "abc123",
  "total_matches": 3,
  "current_case_index": 0,
  "current_case": {
    "case_number": "1/3",
    "type": "BOT_LEVEL",
    "problem": "Bot not moving...",
    "impact": "High",
    "solution": "Check motor connections...",
    "sql_query": "SELECT * FROM...",
    "expected_outcome": "Should return 0 rows"
  },
  "requires_sql_audit": true
}
```

### Run SQL Audit
```http
POST /api/chatbot/diagnostic/audit-sql?sql_query=SELECT...
```

**Response:**
```json
{
  "success": true,
  "data": [...],
  "row_count": 5,
  "columns": ["col1", "col2"]
}
```

### Analyze Results
```http
POST /api/chatbot/diagnostic/analyze-results
Content-Type: application/json

{
  "case": {...},
  "sql_results": {...}
}
```

**Response:**
```json
{
  "rows_found": 5,
  "expected": "should be empty",
  "interpretation": "Problem confirmed - data exists when it should be empty",
  "status": "problem_confirmed",
  "data_preview": [...]
}
```

### Submit Feedback
```http
POST /api/chatbot/diagnostic/feedback
Content-Type: application/json

{
  "session_data": {...},
  "is_correct": false,
  "user_comment": "Still not working"
}
```

**If solution worked (is_correct=true):**
```json
{
  "status": "resolved",
  "message": "Problem resolved successfully! ✅",
  "solved_with": {...}
}
```

**If not correct (is_correct=false):**
```json
{
  "status": "next_suggestion",
  "message": "Trying next possible cause...",
  "current_case_index": 1,
  "current_case": {...},
  "requires_sql_audit": true
}
```

**If all solutions exhausted:**
```json
{
  "status": "exhausted",
  "message": "All known solutions tried. Escalating to development team.",
  "recommendation": "Manual investigation required"
}
```

## Web Interface

Open `app/modules/neo_chatbot/web/semi_auto_diagnostic.html` in browser

**Workflow:**
1. Enter problem description
2. System shows matched case with highest impact
3. If SQL query available → Run audit
4. Review solution
5. Click "✓ This Solved It" OR "✗ Not Correct"
6. If not correct → next solution appears
7. Repeat until resolved or exhausted

## Data Structure

### Support Logs Format

**Bot Level CSV:**
- Column 0: S NO (ID)
- Column 1: Problem Statement
- Column 2: Impact (High/Medium/Low)
- Column 3: Solution
- Column 4: SQL Query
- Column 5: Expected Outcome
- Column 6: Reported to Dev (Y/N)

**Station Level CSV:**
- Column 0: S NO (ID)
- Column 1: Problem Statement
- Column 2: Impact
- Column 3: Scenario
- Column 4: Solution
- Column 5: SQL Query
- Column 6: Expected Outcome
- Column 7: Reported to Dev (Y/N)

## Usage Example

```python
from app.modules.neo_chatbot.services.semi_automated_diagnostic_service import SemiAutomatedDiagnosticService

service = SemiAutomatedDiagnosticService()

# Start diagnosis
result = service.start_diagnosis("Bot is not moving")
print(result['current_case']['solution'])

# Run SQL audit if available
if result['requires_sql_audit']:
    sql_result = service.execute_sql_audit(
        result['current_case']['sql_query']
    )
    
    # Analyze
    analysis = service.analyze_sql_results(
        result['current_case'],
        sql_result
    )
    print(analysis['interpretation'])

# User feedback
next_step = service.handle_user_feedback(
    session_data=result,
    is_correct=False  # Try next solution
)
```

## Testing

### Web Interface (Recommended)
1. Start server: `.\quick_start.py`
2. Open: `http://localhost:5000/chatbot`
3. Click **"Semi-Auto Diagnostic"** button
4. Enter problem: "Bot not moving"
5. Use interactive buttons to test workflow

### Standalone Page (Alternative)
Open: `http://localhost:8000/app/modules/neo_chatbot/web/semi_auto_diagnostic.html`

## Benefits

✅ **Concise**: Point-to-point, no paragraphs
✅ **Impact-Aware**: Prioritizes by severity
✅ **Data-Driven**: SQL audit verifies issues
✅ **Iterative**: Suggests next cause if not correct
✅ **Separate**: Doesn't touch existing diagnostic service
