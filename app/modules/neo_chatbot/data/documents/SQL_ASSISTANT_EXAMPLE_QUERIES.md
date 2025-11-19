# SQL Assistant - Example Queries You Can Ask

## Overview
The SQL Assistant can help you query the NEO WMS database to retrieve operational data. Here are examples of questions you can ask:

## Order & Task Queries

### Order Status
- "Show me all orders with status 'pending' from today"
- "How many orders were completed yesterday?"
- "Give me orders that are still in progress"
- "Show me failed orders from the last 7 days"

### Order Details
- "What are the details of order number ORD12345?"
- "Show me all orders for customer ABC Company"
- "List orders created in the last hour"
- "Find orders with more than 10 line items"

## Station & Bin Queries

### Station Information
- "Show me all active stations"
- "Which stations processed orders today?"
- "Give me station performance metrics"
- "List stations with pending tasks"

### Bin & Location
- "Show me all bins in zone A"
- "Which bins have inventory above 100 units?"
- "Find empty bins available for storage"
- "Show me bin utilization by zone"

## SKU & Inventory Queries

### SKU Information
- "Show me details for SKU ABC123"
- "List all SKUs with low inventory"
- "What are the top 10 most picked SKUs today?"
- "Show me SKUs with velocity grade A"

### Inventory Levels
- "Show me current inventory levels for warehouse W1"
- "Which SKUs are out of stock?"
- "Give me inventory summary by zone"
- "Show me SKUs that need replenishment"

## Task & Wave Queries

### Task Status
- "How many pick tasks are pending?"
- "Show me completed putaway tasks from today"
- "List tasks assigned to station ST01"
- "Give me average task completion time"

### Wave Management
- "Show me all active waves"
- "How many waves were released today?"
- "Give me wave efficiency metrics"
- "Show me waves with errors"

## Performance & Analytics

### Productivity Metrics
- "What is today's order fulfillment rate?"
- "Show me average order processing time"
- "Give me hourly order volume for today"
- "Compare this week's performance to last week"

### Error Analysis
- "Show me all errors from the last 24 hours"
- "Which error types occur most frequently?"
- "Give me error rate by station"
- "Show me orders that failed validation"

## Time-Based Queries

### Recent Activity
- "Show me orders from the last hour"
- "What happened in the last 30 minutes?"
- "Give me today's summary"
- "Show me this week's totals"

### Date Ranges
- "Show me orders between 2025-01-01 and 2025-01-15"
- "Give me last month's order count"
- "Compare Q1 to Q2 performance"
- "Show me year-to-date statistics"

## Tips for Better Results

### Be Specific
- ✅ "Show me pending orders from station ST01 today"
- ❌ "Show me orders"

### Include Time Ranges
- ✅ "How many orders were completed in the last hour?"
- ❌ "How many orders were completed?"

### Use Proper Terms
- Use: "order", "SKU", "station", "bin", "task", "wave"
- Avoid: vague terms like "stuff", "things", "items"

### Provide Context
- ✅ "Show me high-priority orders that are delayed"
- ❌ "Show me delayed"

## What SQL Assistant CANNOT Do

1. **Modify Data** - Read-only queries only
2. **Create Reports** - Use the Analytics dashboard instead
3. **Execute Actions** - Cannot release waves, assign tasks, etc.
4. **Access External Data** - Only NEO WMS database
5. **Answer General Questions** - Use Knowledge Base for documentation

## Common Database Tables

- **Orders**: `wms_to_wcs_order_line_request_data`
- **SKU Master**: `sku_master`
- **Stations**: `station_master`
- **Bins**: `bin_master`
- **Tasks**: Various task tables (pick, putaway, etc.)
- **Waves**: Wave management tables

## Need Help?

If SQL Assistant cannot answer your question:
1. Try rephrasing with more specific terms
2. Ask the Knowledge Base for documentation
3. Use the Diagnostic Assistant for system issues
4. Check the Analytics dashboard for pre-built reports

---

**Remember**: The more specific your question, the better the SQL query and results!
