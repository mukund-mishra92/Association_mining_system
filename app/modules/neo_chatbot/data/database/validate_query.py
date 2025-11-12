"""
Query Validation Helper

Use this script to test complex SQL queries before documenting them.
This helps ensure queries work correctly before adding them to schema_guide.md

Usage:
    python validate_query.py "your SQL query here"
    
Or run interactively:
    python validate_query.py
"""

import sys
sys.path.insert(0, r'c:\Users\Balmukund.Mishra\Desktop\NEO\association_mining_system')

import pymysql
import pandas as pd
from datetime import datetime
from app.shared.config.config import config


class QueryValidator:
    """Validate and test SQL queries against the database"""
    
    def __init__(self):
        self.db_config = {
            'host': config.DB_HOST,
            'port': config.DB_PORT,
            'user': config.DB_USER,
            'password': config.DB_PASSWORD,
            'database': config.DB_NAME
        }
    
    def validate_query(self, sql_query: str) -> dict:
        """
        Validate a SQL query and return results
        
        Returns:
            dict with keys: success, message, rows, columns, execution_time, data
        """
        result = {
            'success': False,
            'message': '',
            'rows': 0,
            'columns': [],
            'execution_time': 0,
            'data': None
        }
        
        try:
            # Security check - read-only
            dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT INTO', 'UPDATE']
            query_upper = sql_query.upper()
            
            for keyword in dangerous_keywords:
                if keyword in query_upper:
                    result['message'] = f"❌ Query contains dangerous operation: {keyword}"
                    return result
            
            # Connect and execute
            conn = pymysql.connect(**self.db_config, connect_timeout=5)
            start_time = datetime.now()
            
            df = pd.read_sql(sql_query, conn)
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            conn.close()
            
            result['success'] = True
            result['message'] = '✅ Query executed successfully'
            result['rows'] = len(df)
            result['columns'] = df.columns.tolist()
            result['execution_time'] = execution_time
            result['data'] = df
            
        except pymysql.MySQLError as e:
            result['message'] = f"❌ MySQL Error: {e}"
        except Exception as e:
            result['message'] = f"❌ Error: {e}"
        
        return result
    
    def print_results(self, result: dict):
        """Pretty print validation results"""
        print("\n" + "=" * 80)
        print("QUERY VALIDATION RESULTS")
        print("=" * 80)
        
        print(f"\n{result['message']}")
        
        if result['success']:
            print(f"\n📊 Statistics:")
            print(f"   Rows returned: {result['rows']}")
            print(f"   Columns: {len(result['columns'])}")
            print(f"   Execution time: {result['execution_time']:.3f} seconds")
            
            print(f"\n📋 Column Names:")
            for i, col in enumerate(result['columns'], 1):
                print(f"   {i}. {col}")
            
            if result['rows'] > 0:
                print(f"\n📝 Sample Data (first 5 rows):")
                print(result['data'].head(5).to_string())
            else:
                print(f"\n⚠️  Query returned 0 rows (empty result set)")
        
        print("\n" + "=" * 80)
    
    def generate_documentation_template(self, sql_query: str, result: dict, user_question: str = ""):
        """Generate markdown template for schema_guide.md"""
        if not result['success']:
            print("\n⚠️  Query must be successful before generating documentation")
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d")
        
        template = f"""
---
## Add to schema_guide.md:

### Pattern: [Give it a descriptive name]
**Business Question:** {user_question if user_question else "[What user asked]"}

**Tables Used:**
[List tables here - check FROM and JOIN clauses]

**Key Relationships:**
- [table1.column = table2.column]
- [table2.column = table3.column]

**SQL Query:**
```sql
{sql_query}
```

**Results:**
- Returns {result['rows']} rows
- Columns: {', '.join(result['columns'])}
- Execution time: {result['execution_time']:.3f}s

**Notes:**
- [Add any warnings, gotchas, or important considerations]
- [Document any data type mismatches]
- [Explain business logic if needed]

**Tested:** {timestamp}

---
## Add to CHANGELOG.md:

### {timestamp} - [Your Name]
**Change Type:** New Pattern
**Query Type:** [Brief description]
**Why:** [Why this query pattern is important]
**SQL Added:** Yes
**Tested:** Yes

**Changes Made:**
- Added new query pattern: [Pattern name]
- Handles user questions like: "{user_question if user_question else '[User question]'}"

**Verified Query:**
- ✅ Returns {result['rows']} rows, {result['execution_time']:.3f}s execution time
"""
        
        print(template)


def interactive_mode():
    """Run in interactive mode"""
    validator = QueryValidator()
    
    print("\n" + "=" * 80)
    print("SQL QUERY VALIDATOR - Interactive Mode")
    print("=" * 80)
    print("\nEnter your SQL query (type 'exit' to quit)")
    print("For multi-line queries, end with semicolon ';'\n")
    
    while True:
        query_lines = []
        print("SQL> ", end="")
        
        while True:
            line = input()
            if line.lower() == 'exit':
                print("\nGoodbye!")
                return
            
            query_lines.append(line)
            
            if line.strip().endswith(';'):
                break
            else:
                print("...> ", end="")
        
        sql_query = '\n'.join(query_lines)
        
        # Ask for user question
        print("\nWhat was the user's original question? (optional, press Enter to skip)")
        print("Question> ", end="")
        user_question = input().strip()
        
        # Validate
        result = validator.validate_query(sql_query)
        validator.print_results(result)
        
        # Ask if user wants documentation template
        if result['success'] and result['rows'] > 0:
            print("\nGenerate documentation template? (y/n): ", end="")
            if input().lower() == 'y':
                validator.generate_documentation_template(sql_query, result, user_question)
        
        print("\n" + "-" * 80 + "\n")


def main():
    """Main entry point"""
    validator = QueryValidator()
    
    if len(sys.argv) > 1:
        # Command line mode
        sql_query = ' '.join(sys.argv[1:])
        result = validator.validate_query(sql_query)
        validator.print_results(result)
        
        if result['success']:
            print("\nGenerate documentation template? (y/n): ", end="")
            if input().lower() == 'y':
                print("\nUser's original question: ", end="")
                user_question = input().strip()
                validator.generate_documentation_template(sql_query, result, user_question)
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
