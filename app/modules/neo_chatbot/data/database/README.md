# Database Schema Documentation

This directory contains documentation to help the SQL Assistant understand the NEO WMS database structure and generate accurate queries.

## 📁 Files in This Directory

### 1. `database_schema.htm` ⭐
- **Source:** MySQL schema export (HTML format)
- **Contains:** Complete table definitions with columns, types, keys, constraints
- **Size:** 45,469 lines, 163 tables
- **Usage:** Parsed by `schema_parser.py` to provide real-time schema information

### 2. `schema_guide.md` 📚
- **Purpose:** Human-readable documentation of complex table relationships
- **Contains:**
  - Table relationships with JOIN examples
  - Common query patterns
  - Business logic rules
  - Troubleshooting guide
  - Performance tips
- **When to update:** When you discover new query patterns or relationships

### 3. `quick_reference.md` ⚡
- **Purpose:** Fast lookup cheatsheet for SQL Assistant
- **Contains:**
  - Table relationship cheatsheet
  - Data type warnings
  - Status enum values
  - Query templates
  - Common mistakes to avoid
- **When to update:** When you encounter repeated issues

---

## 🔧 How the SQL Assistant Uses This

### Current Implementation
1. **Dynamic Schema Loading** - Parses `database_schema.htm` at runtime
2. **Relevant Table Selection** - Extracts keywords from user query to find relevant tables (max 10 tables)
3. **System Prompt Enhancement** - Injects table relationships and examples into LLM context

### Token Limits
- Groq LLM has 12K token limit per request
- Full schema is 76KB (too large)
- Solution: Dynamically load only relevant tables per query

---

## 📝 Maintaining Documentation

### When to Update `schema_guide.md`

✅ **DO Update When:**
- You discover a new complex JOIN pattern
- Users ask questions requiring multi-table queries
- A new table is added to the database
- Business logic changes affect query patterns
- You find a common error pattern

❌ **DON'T Update For:**
- Simple single-table queries
- Temporary test queries
- User-specific one-off requests

### Update Template

Add new patterns to `schema_guide.md` using this structure:

```markdown
### Pattern: [Descriptive Name]
**Business Question:** [What user asks]

**Tables:**
- `table1` - [Purpose]
- `table2` - [Purpose]

**Join Logic:**
table1.column = table2.column

**SQL Example:**
```sql
[Working SQL query]
```

**Notes:**
- [Important considerations]
- [Common pitfalls]
```

---

## 🚀 Future Improvements

### Option 1: RAG-based Schema Documentation
- Store query patterns in vector database
- Retrieve relevant patterns based on semantic similarity
- **Pros:** Scalable, handles unlimited patterns
- **Cons:** Requires vector DB setup

### Option 2: Query Pattern Library
- Maintain library of tested SQL queries
- Match user questions to existing patterns
- **Pros:** High accuracy, fast
- **Cons:** Limited to known patterns

### Option 3: Fine-tuning
- Fine-tune LLM on your specific schema and query patterns
- **Pros:** Better accuracy
- **Cons:** Requires training data, regular updates

---

## 📋 Best Practices

1. **Test Before Documenting** - Always verify SQL works on actual database
2. **Include Context** - Explain WHY the JOIN works, not just HOW
3. **Document Edge Cases** - Note data type mismatches, null handling
4. **Keep Examples Current** - Update when schema changes
5. **Version Control** - Track changes with dates and reasons

---

## 🎯 Quick Start for New Complex Queries

1. Test your SQL query manually first
2. Document in `schema_guide.md` if it's a new pattern
3. Add to system prompt in `sql_assistant_service.py` if very common
4. Update `quick_reference.md` with any new warnings or tips

---

## Legacy: Manual Schema Options

### Option 1: SQL Schema File (Old Method)

Create a file named `schema.sql` with your database structure:

```sql
-- Example: schema.sql

CREATE TABLE order_history (
    order_id VARCHAR(50) PRIMARY KEY,
    sku VARCHAR(50) NOT NULL,
    order_date DATE NOT NULL,
    quantity INT,
    customer_id VARCHAR(50),
    amount DECIMAL(10,2),
    INDEX idx_sku (sku),
    INDEX idx_order_date (order_date)
);

CREATE TABLE sku_recommendations (
    parent_article_id VARCHAR(50),
    child_article_id VARCHAR(50),
    proximity_score DECIMAL(5,3),
    PRIMARY KEY (parent_article_id, child_article_id)
);

CREATE TABLE mining_schedules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_name VARCHAR(255),
    schedule_type VARCHAR(50),
    min_support DECIMAL(5,3),
    created_at DATETIME
);

-- Add all your tables here...
```

## Option 2: Database Connection

Add credentials to your `.env` file in the project root:

```env
# NEO Chatbot Database Connection
CHATBOT_DB_HOST=localhost
CHATBOT_DB_PORT=3306
CHATBOT_DB_USER=root
CHATBOT_DB_PASSWORD=your_password
CHATBOT_DB_NAME=neo
```

## What will the chatbot do?

The chatbot will:
- Learn your database structure
- Understand table relationships
- Generate SQL queries from natural language
- Answer questions like:
  - "Show me top 10 SKUs"
  - "How many orders last month?"
  - "What tables store recommendations?"
  - "Show orders for SKU ABC123"

The chatbot converts natural language to SQL automatically!
