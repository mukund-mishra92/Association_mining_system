"""
SQL Assistant Service - Convert natural language to SQL queries
Helps users query the database using plain English
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
import os

from .llm_service import LLMService
from ..models.schemas import ChatRequest, ChatResponse, ChatbotType, SQLQueryRequest, SQLQueryResponse

logger = logging.getLogger(__name__)


class SQLAssistantService:
    """
    Service for SQL query generation from natural language
    Converts user questions into SQL queries
    """
    
    def __init__(self):
        """Initialize SQL assistant service"""
        self.llm_service = LLMService()
        self.db_schema = self._load_database_schema()
        
        self.system_prompt = f"""You are a SQL expert assistant for the NEO Warehouse Management System database.

Database Schema:
{self.db_schema}

When generating SQL queries:
1. Generate valid MySQL syntax
2. Use appropriate JOINs when needed
3. Add LIMIT clauses for large result sets (default LIMIT 100)
4. Use proper date/time filtering
5. Include helpful comments in the SQL
6. Explain what the query does

Always respond with:
1. The SQL query
2. A brief explanation of what it does
3. Any warnings or notes

Remember: Be accurate and follow SQL best practices."""

        logger.info("✅ SQL Assistant Service initialized")
    
    def _load_database_schema(self) -> str:
        """Load database schema from file or connection"""
        try:
            # Try to load schema.sql file
            from pathlib import Path
            schema_path = Path(__file__).parent.parent / "data" / "database" / "schema.sql"
            
            if schema_path.exists():
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema = f.read()
                logger.info(f"📂 Loaded database schema from {schema_path}")
                return schema
            else:
                # Return default schema if file doesn't exist
                logger.warning("⚠️ No schema.sql found, using default NEO schema")
                return self._get_default_schema()
        except Exception as e:
            logger.error(f"❌ Error loading database schema: {e}")
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
        Process natural language query and convert to SQL
        
        Args:
            chat_request: User's chat request
            
        Returns:
            Chat response with SQL query and optionally results
        """
        try:
            logger.info(f"🔍 Processing SQL query: {chat_request.message[:50]}...")
            
            # Build messages for LLM
            messages = [{
                "role": "user",
                "content": f"""Convert this question to a SQL query:

Question: {chat_request.message}

Provide:
1. The SQL query
2. An explanation of what it does
3. Any warnings or notes

Format your response clearly with the SQL query first."""
            }]
            
            # Generate SQL using LLM
            response_text = self.llm_service.generate_response(
                messages=messages,
                system_prompt=self.system_prompt,
                max_tokens=800,
                temperature=0.3  # Lower temperature for more deterministic SQL
            )
            
            # Extract SQL query from response
            sql_query = self._extract_sql_query(response_text)
            
            # Try to execute if database connection available
            query_results = None
            execution_note = ""
            
            # Note: Actual execution would require database connection
            # For now, just return the generated query
            execution_note = "\n\n💡 To execute this query, run it in your database client or use the NEO system's query interface."
            
            return ChatResponse(
                response=response_text + execution_note,
                chatbot_type=ChatbotType.SQL_ASSISTANT,
                session_id=chat_request.session_id or str(uuid.uuid4()),
                sql_query=sql_query,
                query_results=query_results,
                confidence_score=0.8 if sql_query else 0.5,
                suggested_actions=self._generate_sql_suggestions(chat_request.message)
            )
            
        except Exception as e:
            logger.error(f"❌ Error processing SQL query: {e}", exc_info=True)
            return ChatResponse(
                response="I apologize, but I encountered an error while generating the SQL query. Please try rephrasing your question or provide more details.",
                chatbot_type=ChatbotType.SQL_ASSISTANT,
                session_id=chat_request.session_id or str(uuid.uuid4()),
                sql_query=None,
                confidence_score=0.0
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
            "schema": self.db_schema,
            "tables": self._extract_table_names(),
            "llm_provider": self.llm_service.get_provider_info()
        }
    
    def _extract_table_names(self) -> List[str]:
        """Extract table names from schema"""
        try:
            tables = []
            for line in self.db_schema.split('\n'):
                if 'CREATE TABLE' in line.upper():
                    # Extract table name
                    parts = line.split()
                    table_idx = parts.index('TABLE') + 1
                    if table_idx < len(parts):
                        table_name = parts[table_idx].strip('(').strip()
                        tables.append(table_name)
            return tables
        except Exception as e:
            logger.error(f"❌ Error extracting table names: {e}")
            return []
