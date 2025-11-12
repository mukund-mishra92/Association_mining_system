# Schema Documentation Change Log

Track changes to schema documentation and new query patterns discovered.

## Format
```
### [Date] - [Your Name]
**Change Type:** [New Pattern | Fix | Update | Enhancement]
**Query Type:** [Description]
**Why:** [Reason for documentation]
**SQL Added:** [Yes/No]
**Tested:** [Yes/No]
```

---

## 2025-11-12 - System

### Change Type: Initial Documentation
**Query Type:** Multi-table JOINs for Orders, SKUs, and Bins
**Why:** SQL Assistant was generating incorrect queries with non-existent table names
**SQL Added:** Yes
**Tested:** Yes

**Changes Made:**
1. Created `schema_guide.md` with:
   - Orders ↔ SKUs relationship
   - Bins ↔ Locations multi-table JOIN
   - Mining jobs ↔ Schedules
   - Common query patterns
   - Troubleshooting guide

2. Created `quick_reference.md` with:
   - Fast lookup table relationships
   - Data type warnings (INT vs VARCHAR for bin_id)
   - Status enum values
   - Query templates
   - Common mistakes

3. Updated SQL Assistant system prompt with:
   - Critical table relationships
   - JOIN examples
   - Data type warnings

**Verified Working Queries:**
- ✅ Top SKUs ordered last week (2-table JOIN)
- ✅ Bin locations with most orders (3-table JOIN)
- ✅ Top bins by velocity score
- ✅ Failed mining jobs

**Known Issues:**
- ⚠️ `sku_recommendations` table column names need verification
- ⚠️ Some queries show 50% confidence due to empty result sets (expected behavior)

---

## Template for Future Entries

### [YYYY-MM-DD] - [Your Name]
**Change Type:** [New Pattern | Fix | Update | Enhancement]
**Query Type:** [Brief description]
**Why:** [Reason for change]
**SQL Added:** [Yes/No]
**Tested:** [Yes/No]

**Changes Made:**
- [List what was added/changed]

**Verified Queries:**
- ✅ [Query description]
- ✅ [Query description]

**Issues Found:**
- ⚠️ [Any problems discovered]

---

## Guidelines for Adding Entries

1. **New Pattern** - When you discover a new complex query requiring 3+ tables
2. **Fix** - When you correct an existing documented pattern
3. **Update** - When schema changes require documentation updates
4. **Enhancement** - When you improve existing documentation

Always include:
- The actual user question that triggered the discovery
- The working SQL query
- Any gotchas or warnings
- Test results (does it run? does it return data?)
