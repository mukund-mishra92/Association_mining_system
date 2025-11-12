"""
SQL Assistant Service - Convert natural language to SQL queries and execute them
Helps users query the database using plain English with validation and retry logic
"""

import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple
import os
import pymysql
import pandas as pd
import re

from .llm_service import LLMService
from ..models.schemas import ChatRequest, ChatResponse, ChatbotType, SQLQueryRequest, SQLQueryResponse
from app.shared.config.config import config

logger = logging.getLogger(__name__)


class SQLAssistantService:
    """
    Service for SQL query generation, execution, and validation
    Features:
    - Converts natural language to SQL
    - Executes queries on actual database
    - Validates results with confidence scoring
    - Retries with different strategies if needed
    - Returns formatted results only when confident
    - Dynamic schema loading to avoid token limits
    """
    
    def __init__(self):
        """Initialize SQL assistant service with database connection"""
        self.llm_service = LLMService()
        self.schema_parser = self._load_schema_parser()
        self.db_config = {
            'host': config.DB_HOST,
            'port': config.DB_PORT,
            'user': config.DB_USER,
            'password': config.DB_PASSWORD,
            'database': config.DB_NAME
        }
        
        # Test database connection
        self.db_available = self._test_db_connection()
        
        logger.info(f"✅ SQL Assistant Service initialized | DB Available: {self.db_available} | Tables: {len(self.schema_parser.get_table_names())}")
    
    def _load_schema_parser(self):
        """Load schema parser"""
        try:
            from ..utils.schema_parser import get_schema_parser
            parser = get_schema_parser()
            logger.info(f"✅ Loaded schema parser with {len(parser.get_table_names())} tables")
            return parser
        except Exception as e:
            logger.error(f"❌ Error loading schema parser: {e}")
            return None
    
    def _get_relevant_schema(self, query: str, max_tables: int = 10) -> str:
        """
        Get relevant schema for the query to avoid token limits.
        Extracts table names from query and returns compact schema.
        
        Args:
            query: User's natural language query
            max_tables: Maximum number of tables to include
            
        Returns:
            Compact schema string with relevant tables
        """
        if not self.schema_parser:
            return self._get_default_schema()
        
        # Extract potential table keywords from query
        query_lower = query.lower()
        keywords = re.findall(r'\b\w+\b', query_lower)
        
        # Find relevant tables
        relevant_tables = set()
        all_tables = self.schema_parser.get_table_names()
        
        # First, try direct keyword matching
        for keyword in keywords:
            matching_tables = self.schema_parser.search_tables(keyword)
            relevant_tables.update(matching_tables[:3])  # Add up to 3 matches per keyword
        
        # If no tables found, include most common tables
        if not relevant_tables:
            common_tables = [
                'wms_to_wcs_order_line_request_data',
                'sku_recommendations',
                'mining_job_logs',
                'bin_velocity_scores',
                'article_proximity_score',
                'alarm_master',
                'bin_configuration'
            ]
            for table in common_tables:
                if table in all_tables:
                    relevant_tables.add(table)
        
        # Limit to max_tables
        relevant_tables = list(relevant_tables)[:max_tables]
        
        # Build compact schema
        schema_lines = ["Database Schema (Relevant Tables):"]
        for table in relevant_tables:
            columns = self.schema_parser.tables.get(table, [])
            pk_cols = [c['field'] for c in columns if c['key'] == 'PRI']
            pk_info = f" [PK: {', '.join(pk_cols)}]" if pk_cols else ""
            
            col_list = [f"{c['field']} ({c['type']})" for c in columns[:15]]  # Limit columns
            if len(columns) > 15:
                col_list.append(f"... and {len(columns) - 15} more columns")
            
            schema_lines.append(f"\n{table}{pk_info}:")
            schema_lines.append(f"  {', '.join(col_list)}")
        
        schema = "\n".join(schema_lines)
        logger.info(f"📋 Using {len(relevant_tables)} relevant tables in schema")
        return schema
    
    def _get_system_prompt(self, query: str) -> str:
        """Generate system prompt with relevant schema"""
        schema = self._get_relevant_schema(query)
        
        return f"""You are a SQL expert for the NEO Warehouse Management System.

CRITICAL TABLE RELATIONSHIPS:

1. ORDERS & SKUs:
   - Orders table: wms_to_wcs_order_line_request_data
     Key columns: ORDER_ID, ORDER_LINE_ID, ARTICLE_ID (links to SKU), QUANTITY, INSERTED_TIMESTAMP
   - SKU table: sku_master
     Key columns: SKU_ID (primary key), SKU_NAME, VELOCITY, CATEGORY
   - JOIN: ord.ARTICLE_ID = sm.SKU_ID

2. BINS & LOCATIONS:
   - Bin config: bin_configuration
     Key columns: bin_id (varchar), sku_code, bin_location, zone, current_sku_count
   - Bin info: bin_info_master
     Key columns: BIN_ID (int, primary key), BIN_BARCODE, BIN_TYPE
   - Order-bin mapping: order_bin_mapping
     Key columns: ORDER_BIN_ID, BIN_ID (int), STATION_ID, TYPE, STATUS, INSERTED_TIMESTAMP
   
3. BINS & ORDERS (Multi-table JOIN):
   - To link orders to bin locations:
     wms_to_wcs_order_line_request_data → (via intermediate tables) → bin_configuration
   - Direct bin-order link: order_bin_mapping.BIN_ID = bin_info_master.BIN_ID
   - Then: bin_info_master to bin_configuration via bin_id/BIN_BARCODE matching

4. SKU RECOMMENDATIONS:
   - Table: sku_recommendations
   - Common columns: sku_id, recommended_sku_id, score, confidence

{schema}

IMPORTANT RULES:
1. Use MySQL syntax (CURDATE(), DATE_SUB(), NOW(), etc.)
2. Always add LIMIT clause (default 100, max 1000)
3. Check data types: bin_configuration.bin_id is VARCHAR, bin_info_master.BIN_ID is INT
4. For dates: use INSERTED_TIMESTAMP, UPDATED_TIMESTAMP, or specific date columns
5. Return ONLY the SQL query, no explanations, no markdown code blocks
6. When joining multiple tables, verify column names match exactly (case-sensitive)

EXAMPLE QUERIES:

-- Orders with SKU names (2-table JOIN):
SELECT sm.SKU_ID, sm.SKU_NAME, SUM(ord.QUANTITY) AS total_qty 
FROM wms_to_wcs_order_line_request_data ord 
JOIN sku_master sm ON ord.ARTICLE_ID = sm.SKU_ID 
WHERE ord.INSERTED_TIMESTAMP >= DATE_SUB(NOW(), INTERVAL 7 DAY) 
GROUP BY sm.SKU_ID, sm.SKU_NAME 
ORDER BY total_qty DESC LIMIT 5;

-- Bins with most orders (location analysis):
SELECT bc.bin_location, bc.zone, COUNT(obm.ORDER_BIN_ID) AS order_count
FROM order_bin_mapping obm
JOIN bin_info_master bim ON obm.BIN_ID = bim.BIN_ID
JOIN bin_configuration bc ON bim.BIN_BARCODE = bc.bin_id
WHERE obm.INSERTED_TIMESTAMP >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY bc.bin_location, bc.zone
ORDER BY order_count DESC LIMIT 10;"""
    
    def _test_db_connection(self) -> bool:
        """Test if database connection is available"""
        try:
            conn = pymysql.connect(**self.db_config, connect_timeout=3)
            conn.close()
            logger.info("✅ Database connection successful")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Database connection failed: {e}")
            return False
    
    def _load_database_schema(self) -> str:
        """Load database schema from HTML file"""
        try:
            from ..utils.schema_parser import get_schema_parser
            
            logger.info("🔍 Parsing database schema from HTML file...")
            parser = get_schema_parser()
            
            # Get compact schema for LLM system prompt
            schema = parser.get_compact_schema()
            
            table_count = len(parser.get_table_names())
            logger.info(f"✅ Loaded {table_count} tables from database schema")
            
            return schema
        except Exception as e:
            logger.error(f"❌ Error loading database schema: {e}")
            logger.warning("⚠️ Falling back to default schema")
            return self._get_default_schema()
    
    def _get_default_schema(self) -> str:
        """Get default NEO database schema"""
        return """
-- NEO Warehouse Management System Database Schema

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
    schedule_time TIME,
    min_support DECIMAL(5,3),
    min_confidence DECIMAL(5,3),
    min_lift DECIMAL(5,3),
    is_active BOOLEAN,
    created_at DATETIME,
    last_run_at DATETIME
);

CREATE TABLE mining_job_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    schedule_id INT,
    started_at DATETIME,
    completed_at DATETIME,
    execution_status VARCHAR(50),
    rules_generated INT,
    records_processed INT,
    error_message TEXT,
    FOREIGN KEY (schedule_id) REFERENCES mining_schedules(id)
);

-- Add more tables as needed
"""
    
    def process_query(self, chat_request: ChatRequest) -> ChatResponse:
        """
        Process natural language query with intelligent SQL generation, execution, and validation
        
        Workflow:
        1. Generate SQL from natural language
        2. Execute query on database
        3. Validate results with confidence scoring
        4. Retry with different strategy if low confidence
        5. Return formatted results only when confident
        
        Args:
            chat_request: User's chat request
            
        Returns:
            Chat response with validated query results
        """
        try:
            logger.info(f"🔍 Processing SQL query: {chat_request.message[:50]}...")
            
            if not self.db_available:
                return self._create_error_response(
                    "Database connection is not available. Please check your database configuration.",
                    chat_request.session_id
                )
            
            # Try up to 3 strategies to get confident results
            max_attempts = 3
            strategies = ['direct', 'with_context', 'simplified']
            
            for attempt in range(max_attempts):
                strategy = strategies[min(attempt, len(strategies) - 1)]
                logger.info(f"🔄 Attempt {attempt + 1}/{max_attempts} using strategy: {strategy}")
                
                # Step 1: Generate SQL query
                sql_query = self._generate_sql_with_strategy(chat_request.message, strategy)
                
                if not sql_query:
                    continue
                
                # Step 2: Execute query
                results, error = self._execute_query_safe(sql_query)
                
                if error:
                    logger.warning(f"⚠️ Query execution error (attempt {attempt + 1}): {error}")
                    continue
                
                # Step 3: Validate results
                confidence, validation_msg = self._validate_results(
                    results, 
                    chat_request.message, 
                    sql_query
                )
                
                logger.info(f"📊 Validation: confidence={confidence:.2f}, msg={validation_msg}")
                
                # Step 4: Check if confident enough to return
                if confidence >= 0.75:  # High confidence threshold
                    response_text = self._format_results_with_confidence(
                        results, 
                        sql_query, 
                        chat_request.message,
                        confidence,
                        validation_msg
                    )
                    
                    return ChatResponse(
                        response=response_text,
                        chatbot_type=ChatbotType.SQL_ASSISTANT,
                        session_id=chat_request.session_id or str(uuid.uuid4()),
                        sql_query=sql_query,
                        query_results=results[:100] if results else [],  # Limit to 100 for response
                        confidence_score=confidence,
                        sources=[]
                    )
            
            # If all attempts failed, return query-only response
            logger.warning("⚠️ All attempts failed to produce confident results")
            return self._create_low_confidence_response(
                sql_query if sql_query else "Could not generate SQL",
                chat_request.session_id,
                chat_request.message
            )
            
        except Exception as e:
            logger.error(f"❌ Error processing SQL query: {e}", exc_info=True)
            return self._create_error_response(
                f"I encountered an error: {str(e)}",
                chat_request.session_id
            )
    
    def _extract_sql_query(self, response: str) -> Optional[str]:
        """Extract SQL query from LLM response"""
        try:
            # Look for SQL code blocks
            if "```sql" in response.lower():
                start = response.lower().find("```sql") + 6
                end = response.find("```", start)
                if end > start:
                    return response[start:end].strip()
            
            # Look for SELECT, INSERT, UPDATE, DELETE statements
            lines = response.split('\n')
            sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH']
            
            sql_lines = []
            in_query = False
            
            for line in lines:
                upper_line = line.strip().upper()
                if any(upper_line.startswith(kw) for kw in sql_keywords):
                    in_query = True
                
                if in_query:
                    sql_lines.append(line)
                    if line.strip().endswith(';'):
                        break
            
            if sql_lines:
                return '\n'.join(sql_lines).strip()
            
            return None
        except Exception as e:
            logger.error(f"❌ Error extracting SQL query: {e}")
            return None
    
    def _generate_sql_suggestions(self, query: str) -> List[str]:
        """Generate suggested SQL-related actions"""
        suggestions = []
        
        query_lower = query.lower()
        
        if "top" in query_lower or "best" in query_lower:
            suggestions.extend([
                "Add time period filter",
                "View detailed breakdown",
                "Export results to CSV"
            ])
        elif "count" in query_lower or "how many" in query_lower:
            suggestions.extend([
                "View distribution over time",
                "Compare with previous period",
                "Show detailed list"
            ])
        else:
            suggestions.extend([
                "Refine date range",
                "Add additional filters",
                "View related data"
            ])
        
        return suggestions[:3]
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get database schema information"""
        return {
            "total_tables": len(self._extract_table_names()),
            "tables": self._extract_table_names()[:20],  # Return first 20 tables
            "llm_provider": self.llm_service.get_provider_info(),
            "db_available": self.db_available
        }
    
    def _extract_table_names(self) -> List[str]:
        """Extract table names from schema parser"""
        try:
            if self.schema_parser:
                return self.schema_parser.get_table_names()
            return []
        except Exception as e:
            logger.error(f"❌ Error extracting table names: {e}")
            return []
    
    # ========================================
    # NEW INTELLIGENT METHODS
    # ========================================
    
    def _generate_sql_with_strategy(self, question: str, strategy: str) -> Optional[str]:
        """Generate SQL with different strategies"""
        try:
            # Get dynamic system prompt with relevant schema only
            system_prompt = self._get_system_prompt(question)
            
            if strategy == 'direct':
                prompt = f"Convert to SQL: {question}"
            elif strategy == 'with_context':
                prompt = f"""User question: {question}

Generate MySQL query to answer this question. Return ONLY the SQL."""
            else:  # simplified
                prompt = f"Generate simple SQL for: {question}. Keep it basic with proper table names."
            
            messages = [{"role": "user", "content": prompt}]
            
            response = self.llm_service.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=300,
                temperature=0.1
            )
            
            sql_query = self._extract_sql_query(response)
            return sql_query
            
        except Exception as e:
            logger.error(f"❌ SQL generation error with strategy {strategy}: {e}")
            return None
    
    def _execute_query_safe(self, sql_query: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Execute SQL query safely with timeout and error handling"""
        try:
            # Security: Prevent dangerous operations (use word boundaries to avoid false positives)
            import re
            dangerous_patterns = [
                r'\bDROP\s+TABLE\b',
                r'\bDROP\s+DATABASE\b',
                r'\bDELETE\s+FROM\b',
                r'\bTRUNCATE\b',
                r'\bALTER\s+TABLE\b',
                r'\bCREATE\s+TABLE\b',
                r'\bINSERT\s+INTO\b',
                r'\bUPDATE\s+\w+\s+SET\b'
            ]
            query_upper = sql_query.upper()
            
            for pattern in dangerous_patterns:
                if re.search(pattern, query_upper):
                    return [], f"Query contains dangerous operation: {pattern}"
            
            # Execute with timeout
            conn = pymysql.connect(**self.db_config, connect_timeout=5)
            
            try:
                df = pd.read_sql(sql_query, conn)
                results = df.to_dict('records')
                
                logger.info(f"✅ Query executed: {len(results)} rows returned")
                return results, None
                
            finally:
                conn.close()
                
        except pymysql.Error as e:
            error_msg = str(e)
            logger.error(f"❌ Database error: {error_msg}")
            return [], error_msg
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Execution error: {error_msg}")
            return [], error_msg
    
    def _validate_results(
        self, 
        results: List[Dict[str, Any]], 
        question: str, 
        sql_query: str
    ) -> Tuple[float, str]:
        """
        Validate query results and calculate confidence score
        
        Returns:
            Tuple of (confidence_score, validation_message)
        """
        confidence = 0.5  # Base confidence
        messages = []
        
        # Check 1: Results exist
        if not results:
            return 0.3, "No results returned - query might be too restrictive or data doesn't exist"
        
        confidence += 0.1
        messages.append(f"✅ {len(results)} results found")
        
        # Check 2: Reasonable result count
        if 1 <= len(results) <= 1000:
            confidence += 0.15
            messages.append("✅ Result count looks reasonable")
        elif len(results) > 10000:
            confidence -= 0.1
            messages.append("⚠️ Very large result set - might need filtering")
        
        # Check 3: Results have data (not all nulls)
        if results:
            first_row = results[0]
            non_null_values = sum(1 for v in first_row.values() if v is not None)
            
            if non_null_values >= len(first_row) * 0.7:  # 70% non-null
                confidence += 0.15
                messages.append("✅ Results contain meaningful data")
            else:
                confidence -= 0.05
                messages.append("⚠️ Many null values in results")
        
        # Check 4: Column names make sense
        if results:
            columns = list(results[0].keys())
            relevant_keywords = question.lower().split()
            
            column_relevance = sum(
                1 for col in columns 
                for keyword in relevant_keywords 
                if keyword in col.lower()
            )
            
            if column_relevance > 0:
                confidence += 0.10
                messages.append("✅ Column names match question context")
        
        # Cap confidence at 0.95 (never 100% sure)
        confidence = min(confidence, 0.95)
        
        validation_msg = " | ".join(messages)
        return confidence, validation_msg
    
    def _format_results_with_confidence(
        self,
        results: List[Dict[str, Any]],
        sql_query: str,
        question: str,
        confidence: float,
        validation_msg: str
    ) -> str:
        """Format results with confidence indicators"""
        
        # Confidence badge
        if confidence >= 0.9:
            confidence_badge = f"🟢 **High Confidence** ({confidence * 100:.0f}%)"
        elif confidence >= 0.75:
            confidence_badge = f"🟡 **Good Confidence** ({confidence * 100:.0f}%)"
        else:
            confidence_badge = f"🟠 **Moderate Confidence** ({confidence * 100:.0f}%)"
        
        response_parts = [
            f"**Query:** {question}\n",
            f"{confidence_badge}\n",
            f"**Found {len(results)} result(s):**\n"
        ]
        
        # Format results as markdown table
        if results:
            columns = list(results[0].keys())
            
            # Table header
            table = "| " + " | ".join(columns) + " |\n"
            table += "| " + " | ".join(["---"] * len(columns)) + " |\n"
            
            # Table rows (show first 20)
            display_results = results[:20]
            for row in display_results:
                values = [str(row.get(col, '')) for col in columns]
                table += "| " + " | ".join(values) + " |\n"
            
            response_parts.append(table)
            
            if len(results) > 20:
                response_parts.append(f"\n*Showing first 20 of {len(results)} results*")
        
        # Add SQL query used
        response_parts.append(f"\n**SQL Query:**\n```sql\n{sql_query}\n```")
        
        # Add validation info
        if validation_msg:
            response_parts.append(f"\n*Validation: {validation_msg}*")
        
        return "\n".join(response_parts)
    
    def _create_error_response(self, message: str, session_id: Optional[str]) -> ChatResponse:
        """Create error response"""
        return ChatResponse(
            response=f"❌ {message}",
            chatbot_type=ChatbotType.SQL_ASSISTANT,
            session_id=session_id or str(uuid.uuid4()),
            confidence_score=0.0,
            sources=[]
        )
    
    def _create_low_confidence_response(
        self, 
        sql_query: str, 
        session_id: Optional[str],
        question: str
    ) -> ChatResponse:
        """Create response when confidence is too low"""
        response_text = f"""I generated a SQL query for your question, but I'm not confident in the results.

**Your Question:** {question}

**Generated SQL:**
```sql
{sql_query}
```

**Issue:** The query execution didn't return results I'm confident about. This could mean:
- The data doesn't exist in the specified time range
- The query needs refinement
- The table structure differs from expected

💡 **Suggestions:**
1. Try rephrasing your question with more specific details
2. Check if the data exists for the time period mentioned
3. Review the SQL query above and run it manually if needed

Would you like to try a different question?"""
        
        return ChatResponse(
            response=response_text,
            chatbot_type=ChatbotType.SQL_ASSISTANT,
            session_id=session_id or str(uuid.uuid4()),
            sql_query=sql_query,
            confidence_score=0.5,
            sources=[]
        )
