# Diagnostic Support Service - Quick Reference

## 🚀 Quick Start

### Initialize the Service
```python
from app.modules.neo_chatbot.services.diagnostic_support_service import DiagnosticSupportService

ds = DiagnosticSupportService()
```

## 📚 Common Operations

### 1. Search for Issues
```python
# Search all issue types
results = ds.search_issue("bot stuck")

# Search only bot-level issues
results = ds.search_issue("bot not responding", issue_type="BOT_LEVEL")

# Search only station-level issues
results = ds.search_issue("station pick failed", issue_type="STATION_LEVEL")

# Results include:
# - id, type, problem, severity, solution
# - sql_query, outcome, reported_to_dev
# - relevance_score (sorted by this)
```

### 2. Get Issue by ID
```python
# Get specific bot-level issue
bot_issue = ds.get_issue_by_id(1, "BOT_LEVEL")

# Get specific station-level issue
station_issue = ds.get_issue_by_id(1, "STATION_LEVEL")

print(bot_issue['problem'])
print(bot_issue['solution'])
print(bot_issue['sql_query'])
```

### 3. Get All Issues
```python
# Get all issues
all_issues = ds.get_all_issues()
bot_issues = all_issues['bot_level']
station_issues = all_issues['station_level']

# Get only high severity issues
high_severity = ds.get_all_issues(severity="high")

# Get only medium severity issues
medium_severity = ds.get_all_issues(severity="medium")
```

### 4. Multi-Symptom Diagnosis
```python
# Analyze multiple symptoms together
symptoms = [
    "bot not responding",
    "stuck in tower",
    "no error messages"
]

recommendations = ds.get_diagnostic_recommendations(symptoms)

print(f"Total matches: {recommendations['total_matches']}")
print(f"Developer required: {recommendations['requires_developer']}")

# Get top recommendations
for solution in recommendations['recommended_solutions'][:3]:
    print(f"Problem: {solution['problem']}")
    print(f"Severity: {solution['severity']}")
    print(f"Relevance: {solution['relevance_score']}")
```

### 5. Get Service Statistics
```python
stats = ds.get_statistics()

print(f"Total issues: {stats['total_issues']}")
print(f"Bot level: {stats['bot_level_count']}")
print(f"Station level: {stats['station_level_count']}")
print(f"High severity: {stats['severity']['high']}")
print(f"With SQL: {stats['with_sql_solutions']}")
```

## 🎯 Real-World Examples

### Example 1: Bot Troubleshooting
```python
# User reports: "Bot stopped on ground without error"
results = ds.search_issue("bot stopped without error", "BOT_LEVEL")

if results:
    issue = results[0]
    print(f"Problem: {issue['problem']}")
    print(f"Severity: {issue['severity']}")
    print(f"\nSolution:")
    print(issue['solution'])
    
    if issue.get('sql_query'):
        print(f"\nDiagnostic SQL:")
        print(issue['sql_query'])
```

### Example 2: Station Issues
```python
# User reports: "Station not picking bin"
results = ds.search_issue("station pick bin", "STATION_LEVEL")

for i, result in enumerate(results[:3], 1):
    print(f"\n{i}. {result['problem']}")
    print(f"   Relevance: {result['relevance_score']}")
    print(f"   Severity: {result['severity']}")
    print(f"   Solution: {result['solution'][:100]}...")
```

### Example 3: Complex Issue Analysis
```python
# User describes multiple symptoms
symptoms = [
    "bot communication lost",
    "not responding to commands",
    "stuck in place"
]

recommendations = ds.get_diagnostic_recommendations(symptoms)

print(f"\nAnalyzed {len(recommendations['symptoms_analyzed'])} symptoms")
print(f"Found {recommendations['total_matches']} potential matches")
print(f"\nTop {len(recommendations['recommended_solutions'])} recommendations:")

for i, rec in enumerate(recommendations['recommended_solutions'], 1):
    print(f"\n{i}. {rec['problem']}")
    print(f"   Type: {rec['type']}")
    print(f"   Severity: {rec['severity']}")
    print(f"   Relevance: {rec['relevance_score']:.2f}")
    
    # Show solution
    solution_preview = rec['solution'][:200]
    print(f"   Solution: {solution_preview}...")
```

## 🔍 Search Tips

### Best Search Queries
✅ **Good queries** (specific, descriptive):
- "bot stuck in tower"
- "station pick failed"
- "bot not responding"
- "communication error"
- "unable to put bin"

❌ **Less effective queries** (too generic):
- "error"
- "problem"
- "issue"

### Issue Types
- `"BOT_LEVEL"` - Bot-related issues (7 issues)
- `"STATION_LEVEL"` - Station-related issues (9 issues)
- `None` - Search all types (16 issues)

### Severity Levels
- `"high"` - Critical issues requiring immediate attention
- `"medium"` - Important issues
- `"low"` - Minor issues

## 📊 Response Structure

### Search Results
```python
{
    'id': 1,
    'type': 'BOT_LEVEL',
    'problem': 'BOT Stopped Without Any Error on Ground...',
    'severity': 'High',
    'solution': '· Verify BOT status...',
    'sql_query': 'Select * from task_master...',
    'outcome': '`',
    'reported_to_dev': '',
    'relevance_score': 47.00
}
```

### Statistics Response
```python
{
    'total_issues': 16,
    'bot_level_count': 7,
    'station_level_count': 9,
    'severity': {
        'high': 8,
        'medium': 7,
        'low': 0
    },
    'with_sql_solutions': 10,
    'reported_to_developers': 3
}
```

### Diagnostic Recommendations Response
```python
{
    'symptoms_analyzed': ['symptom1', 'symptom2'],
    'total_matches': 14,
    'recommended_solutions': [...],  # Top 5 matches
    'severity_breakdown': {...},
    'requires_developer': True/False
}
```

## 🎓 Via Chatbot (End Users)

Users can interact naturally with the chatbot:

**User**: "My bot stopped on the ground without any error"

**Chatbot**: Will use the Diagnostic Support Service to:
1. Search historical support logs
2. Generate diagnostic SQL queries
3. Execute queries and analyze results
4. Search documentation for context
5. Provide intelligent root cause analysis
6. Suggest step-by-step solutions

## 🔧 Configuration

### Data Location
```
app/modules/neo_chatbot/data/support/support_logs/
├── NEO Support Logs(Bot Level).csv
└── NEO Support Logs(Station Level ).csv
```

### Supported Encodings
The service automatically tries multiple encodings:
- utf-8
- latin1
- cp1252
- iso-8859-1

### Text Cleaning
Automatically removes:
- Bullet points (��������)
- Special characters
- Extra whitespace
- Empty entries

## 📈 Relevance Scoring

Search results are ranked by relevance:

| Match Type | Points |
|------------|--------|
| Exact phrase in problem | +100 |
| Each term in problem | +10 |
| Each term in solution | +5 |
| High severity boost | +2 |

Higher scores = better matches

## 🎯 Common Use Cases

### 1. Bot Operations Team
```python
# Quick lookup for common bot issues
results = ds.search_issue("bot maintenance", "BOT_LEVEL")
```

### 2. Station Support Team
```python
# Find station-related solutions
results = ds.search_issue("station pick", "STATION_LEVEL")
```

### 3. Support Engineers
```python
# Comprehensive analysis
recommendations = ds.get_diagnostic_recommendations([
    "communication lost",
    "bot stuck",
    "task failed"
])
```

### 4. Dashboard Integration
```python
# Get statistics for dashboard
stats = ds.get_statistics()

# Get all high-priority issues
high_priority = ds.get_all_issues(severity="high")
```

## 🚨 Error Handling

The service handles errors gracefully:
- Missing CSV files: Logs error, continues with available data
- Encoding issues: Tries multiple encodings
- Invalid IDs: Returns None
- Empty queries: Returns top matches
- Invalid issue types: Searches all types

## 📝 Testing

Run comprehensive tests:
```bash
python test_diagnostic_support.py
python test_diagnostic_chatbot.py
```

## 🔗 Related Services

- **DiagnosticService**: Main diagnostic orchestrator
- **IntelligentDiagnosticService**: AI-powered diagnosis
- **SQLAssistantService**: Query execution
- **KnowledgeBaseService**: Documentation search

## 💡 Pro Tips

1. **Use specific keywords** for better matches
2. **Filter by type** when you know the issue category
3. **Use multi-symptom analysis** for complex issues
4. **Check SQL queries** for diagnostic validation
5. **Monitor statistics** to track support trends

---

**Need Help?**
- Check [DIAGNOSTIC_SUPPORT_TEST_RESULTS.md](DIAGNOSTIC_SUPPORT_TEST_RESULTS.md) for test results
- Review API routes at [diagnostic_support_routes.py](app/modules/neo_chatbot/api/diagnostic_support_routes.py)
- See service implementation at [diagnostic_support_service.py](app/modules/neo_chatbot/services/diagnostic_support_service.py)
