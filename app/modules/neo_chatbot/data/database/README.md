# Database Schema Information

Provide your database information in one of two ways:

## Option 1: SQL Schema File (Recommended)

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
