"""
SQL Assistant Service - Convert natural language to SQL queries and execute them
Helps users query the database using plain English with validation and retry logic
"""

import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import os
import pymysql
import pandas as pd
import re

from .llm_service import LLMService
from .rlhf_service import RLHFService
from .chat_history_service import ChatHistoryService
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
        self.rlhf_service = RLHFService()
        self.schema_parser = self._load_schema_parser()
        self.db_config = {
            'host': config.DB_HOST,
            'port': config.DB_PORT,
            'user': config.DB_USER,
            'password': config.DB_PASSWORD,
            'database': config.DB_NAME
        }
        
        # Initialize vector store for SQL examples
        try:
            from .vector_store_service import VectorStoreService
            self.vector_store = VectorStoreService()
            logger.info("✅ Vector store available for SQL examples")
        except Exception as e:
            logger.warning(f"⚠️ Vector store unavailable: {e}")
            self.vector_store = None
        
        # Initialize chat history service for comprehensive logging
        try:
            self.chat_history_service = ChatHistoryService(self.db_config)
            logger.info("✅ Chat history logging enabled")
        except Exception as e:
            logger.warning(f"⚠️ Chat history service unavailable: {e}")
            self.chat_history_service = None
        
        # Session-based query cache: stores successful queries per session
        self.session_query_cache: Dict[str, List[Dict[str, Any]]] = {}
        
        # Session-based corrections: stores user corrections per session
        self.session_corrections: Dict[str, Dict[str, Any]] = {}
        
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
    
    def _find_similar_sql_examples(self, question: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search vector store for similar SQL queries from codebase
        Returns relevant SQL file examples that can help generate better queries
        """
        if not self.vector_store:
            return []
        
        try:
            # Generate embedding for the question
            query_embedding = self.llm_service.generate_embedding(question)
            
            # Search for SQL code files
            results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k * 2,  # Get more, then filter
                filter_metadata={'type': 'code', 'language': 'sql'},
                min_similarity=0.4
            )
            
            # Extract SQL examples
            sql_examples = []
            for result in results[:top_k]:
                doc = result.get('document', {})
                metadata = doc.get('metadata', {})
                content = doc.get('content', '')
                
                # Extract actual SQL from the content
                sql_lines = [line for line in content.split('\n') if line.strip() and not line.strip().startswith('--')]
                sql_code = '\n'.join(sql_lines)
                
                if sql_code and len(sql_code) > 20:
                    sql_examples.append({
                        'filename': metadata.get('filename', 'unknown'),
                        'sql': sql_code[:500],  # Limit length
                        'similarity': result.get('similarity', 0),
                        'context': metadata.get('chunk_context', {})
                    })
            
            if sql_examples:
                logger.info(f"📚 Found {len(sql_examples)} similar SQL examples from codebase")
            
            return sql_examples
            
        except Exception as e:
            logger.warning(f"⚠️ Error searching SQL examples: {e}")
            return []
    
    def _classify_query_intent(self, query: str) -> Dict[str, Any]:
        """
        Classify the intent and entities in the user's query.
        Helps identify which tables and columns are needed.
        
        Returns:
            {
                'intent': 'count' | 'retrieve' | 'aggregate' | 'filter' | 'metadata',
                'entities': ['bin', 'order', 'sku', 'bot'],
                'operations': ['count', 'sum', 'average'],
                'time_filter': True/False,
                'join_needed': True/False,
                'is_metadata_query': True/False
            }
        """
        query_lower = query.lower()
        
        # Check if this is a METADATA query (about schema, not data)
        is_metadata_query = any(phrase in query_lower for phrase in [
            'column names', 'columns in', 'columns available', 'what columns',
            'describe table', 'show columns', 'table structure', 'schema of',
            'fields in', 'list columns', 'show fields', 'what fields',
            'show me all the column', 'show me all column'
        ])
        
        # Detect intent
        intent = 'retrieve'  # default
        if is_metadata_query:
            intent = 'metadata'
        elif any(word in query_lower for word in ['how many', 'count', 'number of', 'total']):
            intent = 'count'
        elif any(word in query_lower for word in ['sum', 'total quantity', 'total amount']):
            intent = 'aggregate'
        elif any(word in query_lower for word in ['average', 'mean', 'avg']):
            intent = 'aggregate'
        elif any(word in query_lower for word in ['show', 'list', 'get', 'display', 'details']):
            intent = 'retrieve'
        
        # Detect entities (domain concepts)
        entities = []
        entity_map = {
            'bin': ['bin', 'bins', 'location', 'locations'],
            'order': ['order', 'orders', 'shipment', 'delivery'],
            'sku': ['sku', 'article', 'product', 'item', 'inventory'],
            'bot': ['bot', 'bots', 'robot', 'robots'],
            'alarm': ['alarm', 'alarms', 'alert', 'alerts', 'error'],
            'maintenance': ['maintenance', 'repair', 'service'],
            'velocity': ['velocity', 'speed', 'frequency'],
            'configuration': ['config', 'configuration', 'setting'],
        }
        
        for entity, keywords in entity_map.items():
            if any(kw in query_lower for kw in keywords):
                entities.append(entity)
        
        # Detect if JOIN might be needed
        join_needed = len(entities) > 1 or any(phrase in query_lower for phrase in [
            'with', 'and', 'along with', 'including', 'details of'
        ])
        
        # Detect operations
        operations = []
        if 'count' in query_lower or 'how many' in query_lower:
            operations.append('count')
        if 'sum' in query_lower or 'total' in query_lower:
            operations.append('sum')
        if 'average' in query_lower or 'avg' in query_lower:
            operations.append('average')
        if 'group' in query_lower or 'by' in query_lower:
            operations.append('group_by')
        
        # Detect time filter
        time_filter = any(word in query_lower for word in [
            'today', 'yesterday', 'week', 'month', 'year', 'recent', 'last', 'past'
        ])
        
        return {
            'intent': intent,
            'entities': entities,
            'operations': operations,
            'time_filter': time_filter,
            'join_needed': join_needed,
            'is_metadata_query': is_metadata_query
        }
    
    def _get_tables_for_entities(self, entities: List[str]) -> Dict[str, List[str]]:
        """
        Map domain entities to actual database tables.
        
        Args:
            entities: List of domain concepts ['bin', 'order', 'sku']
            
        Returns:
            Dict mapping entity to list of relevant tables
        """
        # Entity to table mapping (based on NEO WMS domain)
        entity_table_map = {
            'bin': [
                'bin_configuration',
                'bin_info_master',
                'live_inventory_master',
                'order_bin_mapping'
            ],
            'order': [
                'wms_to_wcs_order_line_request_data',
                'order_bin_mapping',
                'order_history'
            ],
            'sku': [
                'sku_master',
                'articles_registered',
                'article_proximity_score',
                'live_inventory_master'
            ],
            'bot': [
                'bot_master',
                'bot_master_log',
                'bot_alarm_log',
                'bot_charging_bit_log'
            ],
            'alarm': [
                'alarm_master',
                'bot_alarm_log',
                'bot_manual_alarm_log'
            ],
            'maintenance': [
                'dashboard_log_maintenance_task_master'
            ],
            'velocity': [
                'bin_velocity_scores',
                'sku_velocity_analysis'
            ],
            'configuration': [
                'config_master',
                'bin_configuration'
            ],
        }
        
        result = {}
        for entity in entities:
            if entity in entity_table_map:
                result[entity] = entity_table_map[entity]
        
        return result
    
    def _get_join_paths(self, tables: List[str]) -> List[Dict[str, Any]]:
        """
        Identify how to JOIN multiple tables.
        Returns possible JOIN paths with columns.
        
        Args:
            tables: List of table names that need to be joined
            
        Returns:
            List of JOIN path dictionaries
        """
        # Known JOIN relationships in NEO WMS
        join_relationships = [
            {
                'table1': 'wms_to_wcs_order_line_request_data',
                'table2': 'sku_master',
                'join_on': 'ARTICLE_ID = SKU_ID',
                'description': 'Orders to SKU details'
            },
            {
                'table1': 'order_bin_mapping',
                'table2': 'bin_info_master',
                'join_on': 'BIN_ID = BIN_ID',
                'description': 'Order-Bin mapping to bin details'
            },
            {
                'table1': 'bin_info_master',
                'table2': 'bin_configuration',
                'join_on': 'BIN_BARCODE = bin_id',
                'description': 'Bin info to bin configuration'
            },
            {
                'table1': 'live_inventory_master',
                'table2': 'sku_master',
                'join_on': 'ARTICLE_ID = SKU_ID',
                'description': 'Inventory to SKU details'
            },
            {
                'table1': 'bot_master',
                'table2': 'bot_alarm_log',
                'join_on': 'BOT_ID = BOT_ID',
                'description': 'Bots to their alarms'
            },
            {
                'table1': 'dashboard_log_maintenance_task_master',
                'table2': 'bot_master',
                'join_on': 'MAINTENANCE_POINT_BOT_ID = BOT_ID',
                'description': 'Maintenance tasks to bots'
            },
        ]
        
        relevant_joins = []
        for join in join_relationships:
            if join['table1'] in tables and join['table2'] in tables:
                relevant_joins.append(join)
        
        return relevant_joins
    
    def _get_relevant_schema(self, query: str, max_tables: int = 10) -> str:
        """
        INTELLIGENT schema selection based on query intent and entities.
        Uses semantic understanding to find the right tables.
        
        Args:
            query: User's natural language query
            max_tables: Maximum number of tables to include
            
        Returns:
            Compact schema string with relevant tables + JOIN hints
        """
        if not self.schema_parser:
            return self._get_default_schema()
        
        # Step 1: Classify query intent
        intent_info = self._classify_query_intent(query)
        logger.info(f"🎯 Query intent: {intent_info['intent']}, entities: {intent_info['entities']}")
        
        # Step 2: Get tables for identified entities
        entity_tables = self._get_tables_for_entities(intent_info['entities'])
        
        # Step 3: Combine all relevant tables
        relevant_tables = set()
        for entity, tables in entity_tables.items():
            relevant_tables.update(tables)
        
        # Step 4: Also try keyword matching as fallback
        query_lower = query.lower()
        keywords = re.findall(r'\b\w+\b', query_lower)
        all_tables = self.schema_parser.get_table_names()
        
        for keyword in keywords:
            matching_tables = self.schema_parser.search_tables(keyword)
            relevant_tables.update(matching_tables[:2])
        
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
        
        # Step 5: Get JOIN paths if multiple tables
        join_hints = []
        if len(relevant_tables) > 1:
            join_paths = self._get_join_paths(relevant_tables)
            if join_paths:
                join_hints.append("\n🔗 SUGGESTED JOIN PATHS:")
                for join in join_paths:
                    join_hints.append(
                        f"  • {join['table1']} JOIN {join['table2']} ON {join['join_on']}"
                    )
                    join_hints.append(f"    ({join['description']})")
        
        # Build compact schema with semantic information
        schema_lines = [f"📊 Database Schema (Intent: {intent_info['intent']}, Entities: {', '.join(intent_info['entities']) or 'general'})"]
        
        # Add JOIN hints at the top if needed
        if join_hints:
            schema_lines.extend(join_hints)
        
        # Add table schemas
        schema_lines.append("\n📋 RELEVANT TABLES:")
        for table in relevant_tables:
            columns = self.schema_parser.tables.get(table, [])
            pk_cols = [c['field'] for c in columns if c['key'] == 'PRI']
            pk_info = f" [PK: {', '.join(pk_cols)}]" if pk_cols else ""
            
            # Add semantic information for key columns
            semantic_cols = self._add_column_semantics(table, columns[:15])
            
            schema_lines.append(f"\n{table}{pk_info}:")
            schema_lines.append(f"  {semantic_cols}")
            
            if len(columns) > 15:
                schema_lines.append(f"  ... and {len(columns) - 15} more columns")
        
        schema = "\n".join(schema_lines)
        logger.info(f"📋 Using {len(relevant_tables)} relevant tables | JOINs detected: {len(join_paths) if len(relevant_tables) > 1 else 0}")
        return schema
    
    def _add_column_semantics(self, table: str, columns: List[Dict]) -> str:
        """
        Add semantic meaning to columns to help LLM understand their purpose.
        
        Args:
            table: Table name
            columns: List of column dictionaries
            
        Returns:
            Formatted string with columns and their semantic meanings
        """
        # Column semantic hints (what they actually mean)
        column_meanings = {
            'ARTICLE_ID': '(SKU identifier)',
            'BIN_ID': '(bin identifier)',
            'ORDER_ID': '(order identifier)',
            'BOT_ID': '(robot identifier)',
            'QUANTITY': '(item count)',
            'INSERTED_TIMESTAMP': '(creation time)',
            'UPDATED_TIMESTAMP': '(last modified time)',
            'IS_ACTIVE': '(active status: 1=active, 0=inactive)',
            'STATUS': '(current status)',
            'TASK_DONE': '(completion: 1=done, 0=pending)',
        }
        
        col_list = []
        for col in columns:
            field = col['field']
            data_type = col['type']
            semantic = column_meanings.get(field, '')
            
            # Add semantic hint if available
            if semantic:
                col_list.append(f"{field} {semantic}")
            else:
                col_list.append(f"{field} ({data_type})")
        
        return ', '.join(col_list)
    
    def _store_failed_table(self, session_id: str, table_name: str, reason: str):
        """Store information about tables that failed/have no data"""
        if not session_id:
            return
        
        if session_id not in self.session_corrections:
            self.session_corrections[session_id] = {'corrections': [], 'failed_tables': []}
        
        if 'failed_tables' not in self.session_corrections[session_id]:
            self.session_corrections[session_id]['failed_tables'] = []
        
        self.session_corrections[session_id]['failed_tables'].append({
            'table': table_name,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"📝 Stored failed table: {table_name} ({reason})")
    
    def _suggest_alternative_tables(self, failed_table: str, context: str) -> List[str]:
        """
        Suggest alternative tables based on failed table and context
        Uses table name similarity and column matching
        """
        if not self.schema_parser:
            return []
        
        suggestions = []
        all_tables = self.schema_parser.get_table_names()
        
        # Extract keywords from context
        keywords = set(re.findall(r'\b\w{4,}\b', context.lower()))  # Words 4+ chars
        
        # Find similar table names
        failed_lower = failed_table.lower()
        for table in all_tables:
            table_lower = table.lower()
            
            # Skip the failed table
            if table_lower == failed_lower:
                continue
            
            # Check for similar patterns
            score = 0
            
            # Same prefix/suffix
            if any(part in table_lower for part in failed_lower.split('_') if len(part) > 3):
                score += 2
            
            # Contains context keywords
            table_info = self.schema_parser.get_table_info(table)
            table_text = f"{table} {' '.join([col['field'] for col in table_info])}"
            matching_keywords = keywords & set(re.findall(r'\b\w{4,}\b', table_text.lower()))
            score += len(matching_keywords)
            
            if score > 0:
                suggestions.append((table, score))
        
        # Sort by score and return top 3
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return [table for table, score in suggestions[:3]]
    
    def _is_negative_feedback(self, message: str) -> bool:
        """
        Detect if user is expressing negative feedback/dissatisfaction
        Returns True if message is ONLY negative feedback (not a new question)
        """
        message_lower = message.strip().lower()
        
        # Pure negative feedback patterns (no new question)
        pure_negative_patterns = [
            r'^no[,.\s]*$',
            r'^nope[,.\s]*$',
            r'^wrong[,.\s]*$',
            r'^incorrect[,.\s]*$',
            r'^not right[,.\s]*$',
            r'^this is wrong[,.\s]*$',
            r'^this is not right[,.\s]*$',
            r'^no,?\s*this is not right[,.\s]*$',
            r'^no,?\s*wrong[,.\s]*$',
            r'^that\'?s wrong[,.\s]*$',
            r'^that\'?s not right[,.\s]*$',
        ]
        
        for pattern in pure_negative_patterns:
            if re.match(pattern, message_lower):
                logger.info(f"🚫 Detected pure negative feedback: '{message}'")
                return True
        
        return False
    
    def _detect_user_correction(self, message: str, session_id: Optional[str]) -> bool:
        """
        Detect if user message is a correction/clarification and store it.
        Returns True if it's a correction (so we should handle it specially)
        """
        message_lower = message.lower()
        
        # Patterns that indicate corrections
        correction_indicators = [
            'is wrong', 'not correct', 'should be', 'use instead',
            'correct is', 'the correct', 'actually', 'it\'s actually',
            'column is', 'field is', 'not means', 'doesn\'t mean',
            'table is null', 'table is empty', 'no data in', 'not available in',
            'find in other table', 'check other table', 'different table'
        ]
        
        is_correction = any(indicator in message_lower for indicator in correction_indicators)
        
        if is_correction and session_id:
            # Extract and store correction
            correction_patterns = [
                (r'(\w+)\s+is\s+wrong.*?correct\s+is\s+(\w+)', 'column_name'),
                (r'(\w+)\s+is\s+wrong.*?use\s+(\w+)', 'column_name'),
                (r'not\s+(\w+).*?should\s+be\s+(\w+)', 'column_name'),
                (r'use\s+(\w+)\s+instead', 'instruction'),
                (r'correct\s+is\s+(\w+)', 'column_name'),
                (r'column\s+is\s+(\w+)', 'column_name'),
            ]
            
            for pattern, correction_type in correction_patterns:
                matches = re.finditer(pattern, message_lower, re.IGNORECASE)
                for match in matches:
                    if match.lastindex >= 2:
                        self._store_correction(session_id, match.group(1), match.group(2))
                        logger.info(f"🔧 Stored correction: '{match.group(1)}' → '{match.group(2)}'")
            
            # Check if user says table has no data
            if any(phrase in message_lower for phrase in ['table is null', 'table is empty', 'no data', 'not ready']):
                # Extract table name
                table_pattern = r'([\w_]+)\s+(?:table\s+)?(?:is\s+)?(?:null|empty|not ready)'
                table_match = re.search(table_pattern, message_lower)
                if table_match and session_id:
                    failed_table = table_match.group(1)
                    logger.info(f"⚠️ User reported empty table: {failed_table}")
                    self._store_failed_table(session_id, failed_table, "Empty/no data")
        
        return is_correction
    
    def _extract_conversation_context(self, conversation_history: Optional[List], session_id: Optional[str]) -> Dict[str, Any]:
        """
        Extract important context from conversation history
        - Previous tables mentioned
        - Column name corrections
        - Successful queries
        - User clarifications
        """
        context = {
            'tables_used': set(),
            'columns_mentioned': {},  # table -> columns
            'corrections': [],
            'successful_queries': [],
            'failed_tables': [],  # Tables that have no data
            'previous_results': [],  # Store actual data from previous queries
            'key_info': []
        }
        
        if not conversation_history:
            # Even without conversation history, check RLHF for past corrections
            try:
                rlhf_corrections = self.rlhf_service.get_sql_corrections(limit=10)
                for rlhf_corr in rlhf_corrections:
                    comment = rlhf_corr.get('comment', '')
                    # Extract correction from comment
                    if 'wrong' in comment.lower() and 'correct' in comment.lower():
                        context['key_info'].append(f"Past correction: {comment[:100]}")
            except Exception as e:
                logger.warning(f"Could not retrieve RLHF corrections: {e}")
            
            return context
        
        # Get session-specific corrections and failed tables
        if session_id and session_id in self.session_corrections:
            context['corrections'].extend(self.session_corrections[session_id].get('corrections', []))
            context['failed_tables'].extend(self.session_corrections[session_id].get('failed_tables', []))
        
        # Get cached successful queries with their actual results
        if session_id and session_id in self.session_query_cache:
            recent_queries = self.session_query_cache[session_id][-3:]  # Last 3
            for query_info in recent_queries:
                context['previous_results'].append({
                    'question': query_info['question'],
                    'sql': query_info['sql'],
                    'results_count': query_info.get('results_count', 0),
                    'sample_data': query_info.get('sample_data', [])  # First few rows
                })
        
        # Process conversation history
        for msg in conversation_history[-10:]:  # Last 10 messages for context
            content = msg.content.lower() if hasattr(msg, 'content') else str(msg).lower()
            
            # Extract table names mentioned
            if self.schema_parser:
                for table in self.schema_parser.get_table_names():
                    if table.lower() in content:
                        context['tables_used'].add(table)
            
            # Detect corrections (key patterns)
            correction_patterns = [
                (r'(\w+)\s+is\s+wrong.*?correct\s+is\s+(\w+)', 'column_name'),
                (r'(\w+)\s+is\s+wrong.*?use\s+(\w+)', 'column_name'),
                (r'not\s+(\w+).*?should\s+be\s+(\w+)', 'column_name'),
                (r'use\s+(\w+)\s+instead\s+of\s+(\w+)', 'column_name'),
                (r'column\s+is\s+(\w+)\s+not\s+(\w+)', 'column_name'),
            ]
            
            for pattern, correction_type in correction_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    if match.lastindex >= 2:
                        context['corrections'].append({
                            'wrong': match.group(2) if 'not' in pattern else match.group(1),
                            'correct': match.group(1) if 'column is' in pattern else match.group(2),
                            'type': correction_type
                        })
            
            # Detect clarifications about query logic
            if any(keyword in content for keyword in ['empty bin', 'available bin', 'free bin']):
                context['key_info'].append("User asking about empty/available bins - check ARTICLE_ID='no-sku' in live_inventory_master")
            
            if 'virtual quantity' in content or 'quantity is 0 not means' in content:
                context['key_info'].append("Important: Quantity=0 doesn't mean bin is empty due to virtual quantity allocation")
        
        # Get cached successful queries for this session
        if session_id and session_id in self.session_query_cache:
            context['successful_queries'] = self.session_query_cache[session_id][-3:]  # Last 3 successful queries
        
        logger.info(f"📚 Extracted context: {len(context['tables_used'])} tables, {len(context['corrections'])} corrections, {len(context['key_info'])} insights")
        return context
    
    def _build_context_prompt(self, context: Dict[str, Any]) -> str:
        """Build a prompt section from conversation context"""
        prompt_parts = []
        
        if context['corrections']:
            prompt_parts.append("\n🔧 USER CORRECTIONS (CRITICAL - MUST FOLLOW):")
            for corr in context['corrections']:
                prompt_parts.append(f"  - Use '{corr['correct']}' NOT '{corr['wrong']}'")
        
        if context['failed_tables']:
            prompt_parts.append("\n⚠️ TABLES THAT FAILED/HAVE NO DATA (DO NOT USE):")
            for failed in context['failed_tables']:
                prompt_parts.append(f"  - ❌ {failed['table']} ({failed['reason']})")
            prompt_parts.append("  → Find alternative tables with similar data!")
        
        if context['previous_results']:
            prompt_parts.append("\n📊 PREVIOUS QUERY RESULTS IN THIS CONVERSATION:")
            for i, prev in enumerate(context['previous_results'], 1):
                prompt_parts.append(f"  {i}. Q: {prev['question'][:60]}")
                prompt_parts.append(f"     SQL: {prev['sql'][:80]}...")
                prompt_parts.append(f"     Results: {prev['results_count']} rows")
                if prev.get('sample_data'):
                    sample = prev['sample_data'][:2]  # Show 2 sample rows
                    prompt_parts.append(f"     Sample data: {sample}")
            prompt_parts.append("  → Use this data to answer follow-up questions!")
        
        if context['key_info']:
            prompt_parts.append("\n💡 IMPORTANT CONTEXT FROM CONVERSATION:")
            for info in context['key_info']:
                prompt_parts.append(f"  - {info}")
        
        if context['successful_queries']:
            prompt_parts.append("\n✅ SUCCESSFUL QUERY PATTERNS IN THIS SESSION:")
            for i, query_info in enumerate(context['successful_queries'][-2:], 1):
                prompt_parts.append(f"  {i}. Q: {query_info['question'][:50]}...")
                prompt_parts.append(f"     SQL: {query_info['sql'][:80]}...")
        
        if context['tables_used']:
            prompt_parts.append(f"\n📋 TABLES DISCUSSED: {', '.join(sorted(context['tables_used']))}")
        
        return "\n".join(prompt_parts) if prompt_parts else ""
    
    def _store_successful_query(self, session_id: str, question: str, sql: str, results_count: int, sample_data: List[Dict] = None):
        """Store successful query in session cache with sample data"""
        if not session_id:
            return
        
        if session_id not in self.session_query_cache:
            self.session_query_cache[session_id] = []
        
        self.session_query_cache[session_id].append({
            'question': question,
            'sql': sql,
            'results_count': results_count,
            'sample_data': sample_data[:3] if sample_data else [],  # Store first 3 rows
            'timestamp': pd.Timestamp.now().isoformat()
        })
        
        # Keep only last 10 queries per session
        if len(self.session_query_cache[session_id]) > 10:
            self.session_query_cache[session_id] = self.session_query_cache[session_id][-10:]
    
    def _store_correction(self, session_id: str, wrong: str, correct: str):
        """Store user correction in session"""
        if not session_id:
            return
        
        if session_id not in self.session_corrections:
            self.session_corrections[session_id] = {'corrections': []}
        
        self.session_corrections[session_id]['corrections'].append({
            'wrong': wrong,
            'correct': correct,
            'timestamp': pd.Timestamp.now().isoformat()
        })
    
    def _build_query_guidance(self, intent_info: Dict[str, Any]) -> str:
        """
        Build query-specific guidance based on intent classification.
        Helps LLM understand what type of query to generate.
        """
        guidance_parts = ["\n🎯 QUERY ANALYSIS & GUIDANCE:"]
        
        # Special handling for METADATA queries
        if intent_info.get('is_metadata_query'):
            guidance_parts.append("  🔍 METADATA QUERY DETECTED - User wants schema information, not data!")
            guidance_parts.append("  • Use INFORMATION_SCHEMA.COLUMNS to get column information")
            guidance_parts.append("  • CRITICAL: Add WHERE TABLE_SCHEMA = DATABASE() to filter to current database")
            guidance_parts.append("  • CRITICAL: Use DISTINCT or GROUP BY to avoid duplicate column names")
            guidance_parts.append("  • Show: COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY")
            guidance_parts.append("  • ORDER BY ORDINAL_POSITION for correct column order")
            guidance_parts.append("")
            guidance_parts.append("  ✅ CORRECT PATTERN:")
            guidance_parts.append("     SELECT DISTINCT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY")
            guidance_parts.append("     FROM INFORMATION_SCHEMA.COLUMNS")
            guidance_parts.append("     WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'table_name'")
            guidance_parts.append("     ORDER BY ORDINAL_POSITION;")
            return "\n".join(guidance_parts)
        
        # Intent-specific guidance
        if intent_info['intent'] == 'count':
            guidance_parts.append("  • User wants to COUNT something → Use COUNT(*) or COUNT(DISTINCT column)")
            guidance_parts.append("  • Consider GROUP BY if counting by category")
        elif intent_info['intent'] == 'aggregate':
            guidance_parts.append("  • User wants aggregation → Use SUM(), AVG(), MIN(), MAX()")
            guidance_parts.append("  • GROUP BY relevant dimensions")
        elif intent_info['intent'] == 'retrieve':
            guidance_parts.append("  • User wants to view data → Use SELECT with relevant columns")
            guidance_parts.append("  • Add ORDER BY for better readability")
        
        # Entity-specific hints
        if intent_info['entities']:
            entities_str = ', '.join(intent_info['entities'])
            guidance_parts.append(f"  • Entities involved: {entities_str}")
            
            # Specific entity hints
            if 'bin' in intent_info['entities'] and 'empty' in intent_info['entities']:
                guidance_parts.append("  • For empty bins: Use ARTICLE_ID='no-sku' in live_inventory_master")
            
            if 'order' in intent_info['entities'] and 'sku' in intent_info['entities']:
                guidance_parts.append("  • Orders with SKU details: JOIN wms_to_wcs_order_line_request_data with sku_master")
        
        # JOIN guidance
        if intent_info['join_needed']:
            guidance_parts.append("  ⚠️ MULTIPLE TABLES NEEDED → Check 🔗 SUGGESTED JOIN PATHS below")
            guidance_parts.append("  • Ensure JOIN conditions match exact column names and types")
        
        # Time filter guidance
        if intent_info['time_filter']:
            guidance_parts.append("  • Time filter detected → Use INSERTED_TIMESTAMP or UPDATED_TIMESTAMP")
            guidance_parts.append("  • MySQL date functions: DATE_SUB(NOW(), INTERVAL X DAY/WEEK/MONTH)")
        
        return "\n".join(guidance_parts)
    
    def _get_system_prompt(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate system prompt with intelligent schema and conversation context"""
        # Get intelligent schema with JOIN hints and semantic info
        schema = self._get_relevant_schema(query)
        
        # Classify query intent for guidance
        intent_info = self._classify_query_intent(query)
        
        # Build context prompt if available
        context_prompt = ""
        if context:
            context_prompt = self._build_context_prompt(context)
        
        # Build query-specific guidance
        query_guidance = self._build_query_guidance(intent_info)
        
        # Find similar SQL examples from codebase
        sql_examples = self._find_similar_sql_examples(query, top_k=3)
        sql_examples_prompt = ""
        if sql_examples:
            sql_examples_prompt = "\n\n💡 RELEVANT SQL EXAMPLES FROM CODEBASE:"
            for i, example in enumerate(sql_examples, 1):
                sql_examples_prompt += f"\n\n  Example {i} (from {example['filename']}, similarity: {example['similarity']:.2f}):\n"
                sql_examples_prompt += f"  ```sql\n{example['sql']}\n  ```"
            sql_examples_prompt += "\n\n  ⚠️ These are real queries from the codebase. Use them as reference for:"
            sql_examples_prompt += "\n  - Table names and column names (exact spelling)"
            sql_examples_prompt += "\n  - JOIN patterns and relationships"
            sql_examples_prompt += "\n  - WHERE clause patterns"
            sql_examples_prompt += "\n  - Common query structures"
        
        # Learn from historical queries (successful and failed)
        historical_learning = ""
        if self.chat_history_service:
            try:
                learning_data = self.chat_history_service.learn_from_similar_queries(query, limit=3)
                
                if learning_data['successful_examples']:
                    historical_learning += "\n\n🎓 LEARNED FROM SUCCESSFUL SIMILAR QUERIES:"
                    for i, example in enumerate(learning_data['successful_examples'][:2], 1):
                        historical_learning += f"\n\n  Success Example {i}:"
                        historical_learning += f"\n  Question: {example['query']}"
                        historical_learning += f"\n  SQL: {example['sql'][:200]}..."
                        historical_learning += f"\n  Tables used: {', '.join(example['tables'])}"
                        historical_learning += f"\n  Returned {example['rows']} rows (confidence: {example['confidence']:.0%})"
                
                if learning_data['failed_patterns']:
                    historical_learning += "\n\n⚠️ AVOID THESE PATTERNS (FAILED PREVIOUSLY):"
                    for i, fail in enumerate(learning_data['failed_patterns'][:2], 1):
                        historical_learning += f"\n  • Failed attempt: {fail['query']}"
                        historical_learning += f"\n    Used wrong tables: {', '.join(fail['tables'])}"
                        historical_learning += f"\n    Error: {fail['error'][:100] if fail['error'] else 'Unknown'}"
                
                if learning_data['table_suggestions']:
                    historical_learning += f"\n\n💡 Suggested tables for this query: {', '.join(learning_data['table_suggestions'][:5])}"
                
                if learning_data['column_suggestions']:
                    historical_learning += "\n\n🔧 COLUMN NAME CORRECTIONS (FREQUENTLY NEEDED):"
                    for table, corrections in list(learning_data['column_suggestions'].items())[:3]:
                        for corr in corrections[:2]:
                            historical_learning += f"\n  • {table}: Use '{corr['correct']}' NOT '{corr['wrong']}'"
                
            except Exception as e:
                logger.warning(f"⚠️ Could not retrieve historical learning: {e}")
        
        return f"""You are a SQL expert for the NEO Warehouse Management System.

{query_guidance}
{context_prompt}
{sql_examples_prompt}
{historical_learning}

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

5. BOT MAINTENANCE TASKS:
   - Table: dashboard_log_maintenance_task_master
   - Key columns: MAINTENANCE_TASK_ID (bigint), MAINTENANCE_POINT_BOT_ID (varchar) ⚠️ NOT BOT_ID!
     MAINTENANCE_PICK_POINT_BOT_ID (varchar), TASK_DONE (0=incomplete, 1=complete),
     INSERTED_TIMESTAMP, MAINTENANCE_ID, IS_MP_BOT_HEALTHY
   - ⚠️ CRITICAL: Column is MAINTENANCE_POINT_BOT_ID, NOT BOT_ID

6. BOT INFORMATION & COUNTS:
   - ⚠️ ALWAYS START WITH: bot_master (main bot registry)
   - Key columns: BOT_ID (varchar, primary key), BOT_IP, BOT_TYPE, STATUS, IS_ACTIVE
   - For bot counts: SELECT COUNT(*) FROM bot_master
   - For active bots: WHERE IS_ACTIVE = 1 or STATUS = 'ACTIVE'
   - Related tables: dashboard_bot_master, bot_master_log, bot_alarm_log
   - ⚠️ CRITICAL: Use bot_master as starting point for ALL bot queries (counts, status, lists)

{schema}

IMPORTANT RULES:
1. Use MySQL syntax (CURDATE(), DATE_SUB(), NOW(), etc.)
2. Always add LIMIT clause (default 100, max 1000)
3. Check data types: bin_configuration.bin_id is VARCHAR, bin_info_master.BIN_ID is INT
4. For BOT queries: ALWAYS start from bot_master table
5. For bot counts: COUNT(*) FROM bot_master with appropriate WHERE conditions
6. For dates: use INSERTED_TIMESTAMP, UPDATED_TIMESTAMP, or specific date columns
7. Return ONLY the SQL query, no explanations, no markdown code blocks
8. When joining multiple tables, verify column names match exactly (case-sensitive)
9. For maintenance tasks: Use MAINTENANCE_POINT_BOT_ID, NOT BOT_ID

CRITICAL COLUMN NAME RULES:
⚠️ Common mistakes - ALWAYS use the CORRECT column name:
- live_inventory_master uses: ARTICLE_ID (NOT ArticleId, NOT article_id)
- wms_to_wcs_order_line_request_data uses: ARTICLE_ID (NOT ArticleId)
- For empty/available/free bins: Use ARTICLE_ID='no-sku' in live_inventory_master
- Important: QUANTITY=0 doesn't necessarily mean bin is empty (due to virtual quantity allocation)
- For truly empty bins, use WHERE ARTICLE_ID='no-sku' which indicates no SKU assigned

EXAMPLE QUERIES:

-- Count total bots:
SELECT COUNT(*) AS total_bots FROM bot_master;

-- Count active bots:
SELECT COUNT(*) AS active_bots FROM bot_master WHERE IS_ACTIVE = 1;

-- List all bots with status:
SELECT BOT_ID, BOT_IP, BOT_TYPE, STATUS, IS_ACTIVE 
FROM bot_master 
ORDER BY BOT_ID 
LIMIT 100;

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
ORDER BY order_count DESC LIMIT 10;

-- Incomplete maintenance tasks by bot:
SELECT MAINTENANCE_POINT_BOT_ID AS bot_id, MAINTENANCE_TASK_ID AS task_id, 
       INSERTED_TIMESTAMP AS assigned_date
FROM dashboard_log_maintenance_task_master
WHERE TASK_DONE = 0
ORDER BY INSERTED_TIMESTAMP DESC LIMIT 100;

-- ⚠️ CRITICAL: Count empty/available bins (correct way):
SELECT COUNT(DISTINCT BIN_ID) AS available_bins
FROM live_inventory_master
WHERE ARTICLE_ID = 'no-sku' AND IS_ACTIVE = 1
LIMIT 100;

-- Get list of empty bins:
SELECT BIN_ID
FROM live_inventory_master
WHERE ARTICLE_ID = 'no-sku'
GROUP BY BIN_ID
LIMIT 100;"""
    
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
        1. Extract conversation context and user corrections
        2. Generate SQL from natural language with context
        3. Execute query on database
        4. Validate results with confidence scoring
        5. Retry with different strategy if low confidence
        6. Return formatted results only when confident
        
        Args:
            chat_request: User's chat request with conversation_history
            
        Returns:
            Chat response with validated query results
        """
        start_time = datetime.now()
        chat_id = None
        
        try:
            logger.info(f"🔍 Processing SQL query: {chat_request.message[:50]}...")
            
            if not self.db_available:
                return self._create_error_response(
                    "Database connection is not available. Please check your database configuration.",
                    chat_request.session_id
                )
            
            # Check if user is giving pure negative feedback (like "no" or "wrong")
            if self._is_negative_feedback(chat_request.message):
                logger.info("🚫 Detected pure negative feedback - asking for clarification")
                return ChatResponse(
                    response="""I understand the previous result wasn't correct. To help you better, please clarify:

1. **What was wrong?** (e.g., "wrong table", "wrong columns", "no data")
2. **What are you looking for?** (e.g., "I need bot charging data", "show me alternative table")
3. **Any hints?** (e.g., "the table is empty", "check bot_master table")

**Example responses:**
- "The dashboard_log_bot_charging table is empty, find data in another table"
- "I need to find which bots are at charging stations 37 and 38"
- "Use bot_master table instead"

I'm here to help - just tell me what you need! 💡""",
                    chatbot_type=ChatbotType.SQL_ASSISTANT,
                    session_id=chat_request.session_id or str(uuid.uuid4()),
                    sources=[],
                    confidence_score=0.0,
                    metadata={
                        'type': 'clarification_request',
                        'reason': 'negative_feedback_without_details'
                    }
                )
            
            # Detect if user is providing a correction
            is_correction = self._detect_user_correction(chat_request.message, chat_request.session_id)
            
            # Auto-correct column names using fuzzy matching
            corrected_message, auto_corrections = self._extract_and_correct_column_names(chat_request.message)
            
            # Store auto-corrections in session for learning
            if auto_corrections and chat_request.session_id:
                for corr in auto_corrections:
                    self._store_correction(chat_request.session_id, corr['wrong'], corr['correct'])
            
            # Use corrected message for SQL generation
            original_message = chat_request.message
            if corrected_message != original_message:
                logger.info(f"📝 Using corrected query: {corrected_message[:80]}...")
                query_to_process = corrected_message
            else:
                query_to_process = original_message
            
            # Extract conversation context and corrections
            conversation_context = self._extract_conversation_context(
                chat_request.conversation_history,
                chat_request.session_id
            )
            
            # Try up to 3 strategies to get confident results
            max_attempts = 3
            strategies = ['direct', 'with_context', 'simplified']
            
            for attempt in range(max_attempts):
                strategy = strategies[min(attempt, len(strategies) - 1)]
                logger.info(f"🔄 Attempt {attempt + 1}/{max_attempts} using strategy: {strategy}")
                
                # Step 1: Generate SQL query with conversation context
                # Use corrected query (with auto-corrected column names)
                sql_query = self._generate_sql_with_strategy(
                    query_to_process, 
                    strategy,
                    conversation_context
                )
                
                if not sql_query:
                    continue
                
                # Step 2: Execute query
                results, error = self._execute_query_safe(sql_query)
                
                if error:
                    logger.warning(f"⚠️ Query execution error (attempt {attempt + 1}): {error}")
                    
                    # Log failed query to chat history
                    if self.chat_history_service and attempt == max_attempts - 1:  # Log on last attempt
                        try:
                            response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                            intent_info = self._classify_query_intent(chat_request.message)
                            tables_used = self._extract_tables_from_sql(sql_query)
                            
                            chat_id = self.chat_history_service.log_chat_interaction(
                                session_id=chat_request.session_id or str(uuid.uuid4()),
                                chatbot_type="sql_assistant",
                                user_query=chat_request.message,
                                assistant_response=f"Query failed: {error}",
                                confidence_score=0.0,
                                response_time_ms=response_time_ms
                            )
                            
                            self.chat_history_service.log_sql_query(
                                chat_id=chat_id,
                                session_id=chat_request.session_id or str(uuid.uuid4()),
                                user_query=chat_request.message,
                                generated_sql=sql_query,
                                execution_status='failed',
                                error_message=error[:500],  # Truncate long errors
                                tables_used=tables_used,
                                intent=intent_info.get('intent'),
                                entities=intent_info.get('entities')
                            )
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to log error to chat history: {e}")
                    
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
                        original_message,  # Use original message for display
                        confidence,
                        validation_msg
                    )
                    
                    # Add note about auto-corrections if any were made
                    if auto_corrections:
                        correction_notes = []
                        for corr in auto_corrections:
                            correction_notes.append(f"'{corr['wrong']}' → '{corr['correct']}'")
                        response_text = f"ℹ️ Auto-corrected column names: {', '.join(correction_notes)}\n\n{response_text}"
                    
                    # Calculate response time
                    response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                    
                    # Classify query intent for analytics
                    intent_info = self._classify_query_intent(chat_request.message)
                    
                    # Extract tables and columns from SQL
                    tables_used = self._extract_tables_from_sql(sql_query)
                    columns_used = self._extract_columns_from_sql(sql_query)
                    
                    # Log to comprehensive chat history
                    if self.chat_history_service:
                        try:
                            # Log main chat interaction
                            chat_id = self.chat_history_service.log_chat_interaction(
                                session_id=chat_request.session_id or str(uuid.uuid4()),
                                chatbot_type="sql_assistant",
                                user_query=chat_request.message,
                                assistant_response=response_text,
                                confidence_score=confidence,
                                response_time_ms=response_time_ms
                            )
                            
                            # Log SQL query details
                            self.chat_history_service.log_sql_query(
                                chat_id=chat_id,
                                session_id=chat_request.session_id or str(uuid.uuid4()),
                                user_query=chat_request.message,
                                generated_sql=sql_query,
                                execution_status='success',
                                rows_returned=len(results) if results else 0,
                                execution_time_ms=response_time_ms,
                                tables_used=tables_used,
                                columns_used=columns_used,
                                intent=intent_info.get('intent'),
                                entities=intent_info.get('entities')
                            )
                            
                            # Log auto-corrections
                            for corr in auto_corrections:
                                self.chat_history_service.log_column_correction(
                                    session_id=chat_request.session_id or str(uuid.uuid4()),
                                    table_name=corr.get('table', 'unknown'),
                                    wrong_column=corr['wrong'],
                                    correct_column=corr['correct'],
                                    correction_type='automatic',
                                    similarity_score=corr.get('similarity', 0.0),
                                    chat_id=chat_id
                                )
                            
                            # Update query patterns for learning
                            self.chat_history_service.update_query_pattern(
                                pattern_type='intent',
                                pattern_key=intent_info.get('intent', 'unknown'),
                                pattern_value=chat_request.message[:200],
                                success=True,
                                confidence=confidence
                            )
                            
                            # Log entity-table patterns
                            for entity in intent_info.get('entities', []):
                                if tables_used:
                                    self.chat_history_service.update_query_pattern(
                                        pattern_type='entity_table',
                                        pattern_key=entity,
                                        pattern_value=','.join(tables_used[:3]),
                                        success=True,
                                        confidence=confidence
                                    )
                            
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to log to chat history: {e}")
                    
                    # Store successful query in session cache with sample data
                    self._store_successful_query(
                        chat_request.session_id or str(uuid.uuid4()),
                        chat_request.message,
                        sql_query,
                        len(results) if results else 0,
                        results if results else []
                    )
                    
                    # Record successful query for RLHF learning
                    try:
                        self.rlhf_service.record_feedback(
                            chatbot_type="sql_assistant",
                            query=chat_request.message,
                            response=response_text,
                            feedback_type="neutral",  # Auto-logged on generation
                            rating=None,
                            comment="Auto-generated with high confidence",
                            metadata={
                                "sql_query": sql_query,
                                "confidence": confidence,
                                "row_count": len(results) if results else 0,
                                "strategy": strategy,
                                "attempt": attempt + 1,
                                "auto_corrections": auto_corrections if auto_corrections else None
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Failed to record RLHF feedback: {e}")
                    
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
    
    def _find_closest_column_name(self, user_column: str, table_name: str) -> Optional[str]:
        """
        Find the closest matching column name in the given table.
        Uses fuzzy matching to correct common mistakes like:
        - ArticleId → ARTICLE_ID
        - BinId → BIN_ID
        - orderId → ORDER_ID
        
        Args:
            user_column: Column name as user typed it
            table_name: Table to search in
            
        Returns:
            Closest matching column name or None
        """
        if not self.schema_parser or not table_name:
            return None
        
        try:
            # Get columns for the table
            columns = self.schema_parser.tables.get(table_name, [])
            if not columns:
                return None
            
            column_names = [col['field'] for col in columns]
            user_column_lower = user_column.lower()
            
            # Direct match (case-insensitive)
            for col in column_names:
                if col.lower() == user_column_lower:
                    return col
            
            # Fuzzy matching: Calculate similarity scores
            from difflib import SequenceMatcher
            
            def similarity(a: str, b: str) -> float:
                """Calculate similarity ratio between two strings"""
                return SequenceMatcher(None, a.lower(), b.lower()).ratio()
            
            # Score each column
            matches = []
            for col in column_names:
                score = similarity(user_column, col)
                matches.append((col, score))
            
            # Sort by score (highest first)
            matches.sort(key=lambda x: x[1], reverse=True)
            
            # Return best match if similarity is high enough (>0.6)
            if matches and matches[0][1] > 0.6:
                best_match = matches[0][0]
                logger.info(f"🔍 Fuzzy match: '{user_column}' → '{best_match}' (score: {matches[0][1]:.2f})")
                return best_match
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error finding closest column: {e}")
            return None
    
    def _extract_and_correct_column_names(self, question: str) -> Tuple[str, List[Dict[str, str]]]:
        """
        Extract potential column names from user's query and suggest corrections.
        
        Detects patterns like:
        - "where ArticleId='xyz'"
        - "show me BinId"
        - "order by OrderDate"
        
        Returns:
            Tuple of (corrected_question, list of corrections made)
        """
        corrections = []
        corrected_question = question
        
        if not self.schema_parser:
            return question, corrections
        
        try:
            # Extract table names from question
            question_lower = question.lower()
            tables_mentioned = []
            
            for table in self.schema_parser.get_table_names():
                if table.lower() in question_lower:
                    tables_mentioned.append(table)
            
            if not tables_mentioned:
                return question, corrections
            
            # Pattern to find potential column names in WHERE clauses, ORDER BY, etc.
            # Matches: word followed by = or space (likely column name)
            import re
            column_patterns = [
                r'\bwhere\s+(\w+)\s*[=<>]',  # WHERE column_name =
                r'\band\s+(\w+)\s*[=<>]',    # AND column_name =
                r'\bor\s+(\w+)\s*[=<>]',     # OR column_name =
                r'\border\s+by\s+(\w+)',     # ORDER BY column_name
                r'\bgroup\s+by\s+(\w+)',     # GROUP BY column_name
                r'\bselect\s+(\w+)',         # SELECT column_name
                r'\bshow.*?(\w+Id)',         # show me ArticleId (pattern for Id columns)
                r'\b(\w+Id)\s*[=\'"]',       # ArticleId='value'
                r'\b(\w+_id)\s*[=\'"]',      # article_id='value'
            ]
            
            potential_columns = set()
            for pattern in column_patterns:
                matches = re.finditer(pattern, question, re.IGNORECASE)
                for match in matches:
                    potential_columns.add(match.group(1))
            
            # For each table mentioned, try to find corrections
            for table in tables_mentioned:
                for user_col in potential_columns:
                    # Skip common SQL keywords
                    if user_col.upper() in ['SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'ORDER', 'GROUP', 'BY', 'HAVING']:
                        continue
                    
                    correct_col = self._find_closest_column_name(user_col, table)
                    
                    if correct_col and correct_col != user_col:
                        corrections.append({
                            'table': table,
                            'wrong': user_col,
                            'correct': correct_col
                        })
                        
                        # Replace in question (case-insensitive)
                        corrected_question = re.sub(
                            r'\b' + re.escape(user_col) + r'\b',
                            correct_col,
                            corrected_question,
                            flags=re.IGNORECASE
                        )
            
            if corrections:
                logger.info(f"🔧 Auto-corrected {len(corrections)} column name(s) in query")
                for corr in corrections:
                    logger.info(f"   {corr['table']}: '{corr['wrong']}' → '{corr['correct']}'")
            
            return corrected_question, corrections
            
        except Exception as e:
            logger.error(f"❌ Error extracting column names: {e}")
            return question, corrections
    
    def _generate_sql_with_strategy(self, question: str, strategy: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Generate SQL with different strategies and conversation context"""
        try:
            # Get dynamic system prompt with relevant schema and conversation context
            system_prompt = self._get_system_prompt(question, context)
            
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
    
    def _extract_tables_from_sql(self, sql_query: str) -> List[str]:
        """Extract table names from SQL query"""
        try:
            tables = []
            # Simple regex to find table names after FROM and JOIN
            patterns = [
                r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'INTO\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'UPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, sql_query, re.IGNORECASE)
                tables.extend(matches)
            
            # Remove duplicates and filter out SQL keywords
            sql_keywords = {'SELECT', 'WHERE', 'GROUP', 'ORDER', 'HAVING', 'LIMIT', 'AND', 'OR'}
            tables = [t for t in set(tables) if t.upper() not in sql_keywords]
            
            return tables
        except Exception as e:
            logger.error(f"❌ Error extracting tables from SQL: {e}")
            return []
    
    def _extract_columns_from_sql(self, sql_query: str) -> List[str]:
        """Extract column names from SQL query"""
        try:
            columns = []
            
            # Extract columns from SELECT clause
            select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql_query, re.IGNORECASE | re.DOTALL)
            if select_match:
                select_clause = select_match.group(1)
                # Split by comma but ignore commas in functions
                parts = re.split(r',(?![^()]*\))', select_clause)
                for part in parts:
                    part = part.strip()
                    if part and part != '*':
                        # Extract column name (handle aliases)
                        col_match = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:AS|$)', part, re.IGNORECASE)
                        if col_match:
                            columns.append(col_match.group(1))
                        else:
                            # Try to get just the column name
                            col_match = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)', part)
                            if col_match:
                                columns.append(col_match.group(1))
            
            # Extract columns from WHERE, ORDER BY, GROUP BY
            for clause in ['WHERE', 'ORDER BY', 'GROUP BY']:
                pattern = rf'{clause}\s+(.*?)(?:ORDER BY|GROUP BY|LIMIT|$)'
                matches = re.findall(pattern, sql_query, re.IGNORECASE)
                for match in matches:
                    col_matches = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)', match)
                    columns.extend(col_matches)
            
            # Remove duplicates and SQL keywords
            sql_keywords = {'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'IN', 'LIKE', 
                           'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT', 'ASC', 'DESC'}
            columns = [c for c in set(columns) if c.upper() not in sql_keywords]
            
            return columns
        except Exception as e:
            logger.error(f"❌ Error extracting columns from SQL: {e}")
            return []
