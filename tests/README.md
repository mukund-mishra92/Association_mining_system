# Test Suite

Comprehensive tests for the NEO Association Mining System.

## Directory Structure

```
tests/
├── agentic_system/          # Agentic AI chatbot tests
│   ├── test_agentic_ai.py
│   ├── test_accuracy_improvements.py
│   └── test_enhanced_architecture.py
└── README.md
```

## Agentic System Tests

### test_agentic_ai.py
**Purpose:** Basic multi-agent workflow testing  
**Tests:**
- Format Decision Agent
- Response Agent
- Verification Agent
- End-to-end workflow

**Run:**
```bash
python tests/agentic_system/test_agentic_ai.py
```

### test_accuracy_improvements.py
**Purpose:** Validate anti-hallucination improvements  
**Tests:**
- Hallucination detection
- Citation accuracy
- Context-only responses
- Forbidden phrases check

**Run:**
```bash
python tests/agentic_system/test_accuracy_improvements.py
```

### test_enhanced_architecture.py
**Purpose:** Complete system with ranking and feedback  
**Tests:**
- Document ranking (20→10 selection)
- LLM-based ranking quality
- Validation feedback loop
- Iteration tracking (max 2 retries)
- Response improvement metrics

**Run:**
```bash
python tests/agentic_system/test_enhanced_architecture.py
```

## Running All Tests

### Run All Agentic Tests
```bash
# Windows
for %f in (tests\agentic_system\test_*.py) do python %f

# Linux/Mac
for f in tests/agentic_system/test_*.py; do python "$f"; done
```

### Run Individual Test
```bash
python tests/agentic_system/test_accuracy_improvements.py
```

## Test Coverage

### Agentic AI System
- ✅ Multi-agent workflow
- ✅ Format intelligence
- ✅ Anti-hallucination prompting
- ✅ Document ranking
- ✅ Validation feedback loop
- ✅ Response style quality
- ✅ Natural language generation

### What's NOT Tested Yet
- ⏳ API endpoint integration
- ⏳ Database queries
- ⏳ Association mining logic
- ⏳ Velocity analysis
- ⏳ Performance benchmarks

## Adding New Tests

### 1. Create test file
```bash
# In appropriate subdirectory
touch tests/agentic_system/test_new_feature.py
```

### 2. Follow naming convention
```python
"""
Test [Feature Name]
Tests the [specific functionality]
"""

import asyncio
from app.modules.neo_chatbot.services.agentic_service import AgenticService

async def test_feature():
    """Test description"""
    service = AgenticService()
    # Test code...
    assert result, "Test assertion message"

if __name__ == "__main__":
    asyncio.run(test_feature())
```

### 3. Document in this README

## Test Requirements

### Environment
- Python 3.10+
- Virtual environment activated
- Required packages installed: `pip install -r requirements.txt`

### API Keys
Ensure `.env` file has:
```env
GROQ_API_KEY=your_key_here
AGENTIC_MODE_ENABLED=true
```

### Data
- Vector store populated with documents
- Test queries should have relevant context

## Best Practices

### Test Structure
1. **Setup** - Initialize services
2. **Execute** - Run test scenarios
3. **Assert** - Validate results
4. **Cleanup** - Clean up if needed

### Naming
- File: `test_feature_name.py`
- Function: `test_specific_behavior()`
- Descriptive names that explain what's being tested

### Documentation
- Docstrings for each test
- Inline comments for complex logic
- Expected results documented
- Edge cases noted

## Troubleshooting

### Import Errors
```bash
# Ensure you're in project root
cd association_mining_system

# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### API Key Errors
```bash
# Check .env file exists and has correct keys
cat .env  # Linux/Mac
type .env  # Windows
```

### Vector Store Empty
```bash
# Ingest documents first
python ingest_unified.py
```

### Test Fails
1. Check test output for specific error
2. Verify services are running (if needed)
3. Check logs: `logs/` directory
4. Verify test data exists

## CI/CD Integration

### GitHub Actions (Future)
```yaml
# .github/workflows/tests.yml
name: Run Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest tests/
```

## Metrics

### Current Status
- **Total Tests:** 3
- **Coverage:** ~60% of agentic system
- **Passing:** ✅ (as of last run)
- **Average Runtime:** ~30 seconds per test

### Goals
- Increase coverage to 80%
- Add performance benchmarks
- Automate in CI/CD
- Add integration tests

## Related Documentation

- `/docs/ENHANCED_AGENTIC_ARCHITECTURE.md` - System architecture
- `/docs/CHATBOT_ACCURACY_IMPROVEMENTS.md` - Accuracy strategies
- `/docs/NATURAL_RESPONSE_SYSTEM.md` - Response generation
- `/docs/TESTING_CHAT_LOGGING_GUIDE.md` - Logging for tests

---

**Last Updated:** November 27, 2025  
**Maintainer:** Development Team
