"""
Intelligent Diagnostic Service - AI-Powered Root Cause Analysis
Combines RAG, SQL analysis, and LLM reasoning for smart troubleshooting
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path

from .llm_service import LLMService
from .vector_store_service import VectorStoreService
from .sql_assistant_service import SQLAssistantService
from .diagnostic_support_service import DiagnosticSupportService
from ..models.schemas import ChatRequest, ChatResponse, ChatbotType

logger = logging.getLogger(__name__)


class IntelligentDiagnosticService:
    """
    AI-powered diagnostic service that:
    1. Understands user's problem description
    2. Generates diagnostic SQL queries
    3. Executes queries and analyzes results
    4. Searches documentation for context
    5. Provides intelligent root cause analysis and solutions
    """
    
    def __init__(self):
        """Initialize intelligent diagnostic service"""
        self.llm_service = LLMService()
        self.vector_store = VectorStoreService()
        self.sql_service = SQLAssistantService()
        self.support_service = DiagnosticSupportService()
        
        self.diagnostic_prompt = """You are an expert NEO Warehouse Management System diagnostic engineer.

Your job is to:
1. Understand the user's problem description
2. Generate appropriate SQL diagnostic queries to check the system state
3. Analyze the query results to find root causes
4. Provide clear, actionable solutions

You have access to:
- The NEO database (can run SELECT queries)
- Historical support logs
- Technical documentation
- System architecture knowledge

Be methodical and thorough. Always verify your hypothesis with data before concluding."""

        logger.info("✅ Intelligent Diagnostic Service initialized")
    
    def diagnose_problem(self, chat_request: ChatRequest) -> ChatResponse:
        """
        Main diagnostic workflow (synchronous version):
        1. Understand the problem
        2. Check historical issues
        3. Generate diagnostic queries
        4. Execute and analyze
        5. Search documentation
        6. Synthesize solution
        """
        try:
            problem = chat_request.message
            logger.info(f"🔍 Starting intelligent diagnosis for: {problem[:80]}...")
            
            # Step 1: Extract key information from problem description
            problem_analysis = self._analyze_problem_description(problem)
            
            # Step 2: Check historical support logs for similar issues
            historical_matches = self.support_service.search_issue(problem, None)
            
            # Step 3: Generate diagnostic SQL queries based on problem type
            diagnostic_queries = self._generate_diagnostic_queries(problem_analysis, historical_matches)
            
            # Step 4: Execute queries and collect data
            diagnostic_data = self._execute_diagnostic_queries(diagnostic_queries)
            
            # Step 5: Search documentation for relevant context
            doc_context = self._search_documentation(problem, problem_analysis)
            
            # Step 6: LLM synthesizes all information into root cause analysis
            solution = self._synthesize_solution(
                problem=problem,
                problem_analysis=problem_analysis,
                historical_matches=historical_matches,
                diagnostic_data=diagnostic_data,
                doc_context=doc_context
            )
            
            return ChatResponse(
                response=solution['response'],
                chatbot_type=ChatbotType.DIAGNOSTIC,
                session_id=chat_request.session_id or str(uuid.uuid4()),
                confidence_score=solution['confidence'],
                sources=solution.get('sources', []),
                suggested_actions=[
                    "What should I check next?",
                    "Can you show me the detailed query results?",
                    "How can I prevent this in the future?"
                ]
            )
            
        except Exception as e:
            logger.error(f"❌ Error in intelligent diagnosis: {e}", exc_info=True)
            return ChatResponse(
                response=f"I encountered an error while diagnosing the issue: {str(e)}. Please try rephrasing your problem or contact support.",
                chatbot_type=ChatbotType.DIAGNOSTIC,
                session_id=chat_request.session_id or str(uuid.uuid4()),
                confidence_score=0.0
            )
    
    def _analyze_problem_description(self, problem: str) -> Dict[str, Any]:
        """Use LLM to extract structured information from problem description"""
        try:
            analysis_prompt = f"""Analyze this NEO system issue and extract key information:

Problem: "{problem}"

Extract and categorize:
1. Component Type: (bot, station, task, wave, communication, database, other)
2. Symptom: (stuck, not responding, failed, timeout, error, missing, incorrect)
3. Affected Entity: (specific bot ID, station ID, wave ID, or general)
4. Severity: (critical, high, medium, low)
5. Likely Tables: (which database tables should we check?)
6. Keywords: (key terms for documentation search)

Respond in JSON format:
{{
    "component": "...",
    "symptom": "...",
    "entity": "...",
    "severity": "...",
    "likely_tables": ["table1", "table2"],
    "keywords": ["keyword1", "keyword2"]
}}"""

            messages = [{"role": "user", "content": analysis_prompt}]
            response = self.llm_service.generate_response(
                messages=messages,
                system_prompt="You are a NEO system diagnostic expert. Extract structured information from problem descriptions.",
                max_tokens=500,
                temperature=0.3
            )
            
            # Parse JSON response
            import json
            try:
                analysis = json.loads(response)
            except:
                # Fallback to basic analysis
                problem_lower = problem.lower()
                analysis = {
                    "component": "bot" if "bot" in problem_lower else "station" if "station" in problem_lower else "unknown",
                    "symptom": "not_responding" if "not responding" in problem_lower else "stuck" if "stuck" in problem_lower else "unknown",
                    "entity": "general",
                    "severity": "high" if any(word in problem_lower for word in ["critical", "urgent", "stuck", "stopped"]) else "medium",
                    "likely_tables": ["task_master", "bot_master", "order_bin_mapping"],
                    "keywords": problem_lower.split()[:5]
                }
            
            logger.info(f"📊 Problem analysis: {analysis}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing problem: {e}")
            return {
                "component": "unknown",
                "symptom": "unknown",
                "entity": "general",
                "severity": "medium",
                "likely_tables": [],
                "keywords": []
            }
    
    def _generate_diagnostic_queries(self, problem_analysis: Dict, historical_matches: List[Dict]) -> List[Dict[str, str]]:
        """Generate SQL queries to diagnose the issue"""
        queries = []
        component = problem_analysis.get('component', '')
        symptom = problem_analysis.get('symptom', '')
        
        # Bot-related diagnostics
        if 'bot' in component.lower() or 'stuck' in symptom.lower():
            queries.extend([
                {
                    "purpose": "Check bot inventory and status",
                    "query": "SELECT COUNT(*) as total_bots, SUM(CASE WHEN STATUS='ACTIVE' THEN 1 ELSE 0 END) as active_bots FROM bot_master;"
                },
                {
                    "purpose": "Check active and pending tasks",
                    "query": "SELECT STATUS, COUNT(*) as count FROM task_master GROUP BY STATUS;"
                },
                {
                    "purpose": "Check recent bot assignments",
                    "query": "SELECT * FROM task_master WHERE STATUS IN ('ASSIGNED', 'IN_PROGRESS') LIMIT 5;"
                }
            ])
        
        # Station-related diagnostics
        if 'station' in component.lower() or 'pick' in symptom.lower():
            queries.extend([
                {
                    "purpose": "Check station pick tasks",
                    "query": "SELECT STATUS, COUNT(*) as count FROM station_pick_task_master GROUP BY STATUS;"
                },
                {
                    "purpose": "Check pending bin mappings",
                    "query": "SELECT * FROM order_bin_mapping WHERE STATUS = 'PENDING' LIMIT 5;"
                },
                {
                    "purpose": "Check POST_ON_STATION bins",
                    "query": "SELECT * FROM order_bin_mapping WHERE BIN_LOCATION = 'POST_ON_STATION' LIMIT 5;"
                }
            ])
        
        # General system health - always check
        queries.append({
            "purpose": "Check overall system task status",
            "query": "SELECT COUNT(*) as total_tasks FROM task_master;"
        })
        
        logger.info(f"Generated {len(queries)} diagnostic queries for {component}/{symptom}")
        return queries
    
    def _execute_diagnostic_queries(self, queries: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Execute all diagnostic queries and collect results"""
        results = []
        
        for query_info in queries:
            try:
                query = query_info['query']
                purpose = query_info['purpose']
                
                logger.info(f"🔍 Executing: {purpose}")
                
                # Execute using SQL service
                query_results, error = self.sql_service._execute_query_safe(query)
                
                if error:
                    # Query failed (table doesn't exist, syntax error, etc.)
                    logger.warning(f"⚠️ Query failed: {error}")
                    results.append({
                        "purpose": purpose,
                        "query": query,
                        "success": False,
                        "error": error,
                        "row_count": 0,
                        "data": [],
                        "is_empty": False  # Failed vs empty
                    })
                else:
                    # Query succeeded
                    row_count = len(query_results)
                    is_empty = row_count == 0
                    
                    results.append({
                        "purpose": purpose,
                        "query": query,
                        "success": True,
                        "error": None,
                        "row_count": row_count,
                        "data": query_results[:20],  # Limit to first 20 rows
                        "is_empty": is_empty
                    })
                    
                    if is_empty:
                        logger.info(f"⚠️ Query succeeded but returned 0 records")
                    else:
                        logger.info(f"✅ Found {row_count} records")
                
            except Exception as e:
                logger.error(f"Error executing query: {e}")
                results.append({
                    "purpose": purpose,
                    "query": query,
                    "success": False,
                    "error": str(e),
                    "row_count": 0,
                    "data": [],
                    "is_empty": False
                })
        
        return results
    
    def _search_documentation(self, problem: str, problem_analysis: Dict) -> str:
        """Search documentation for relevant context"""
        try:
            # Create enhanced search query
            keywords = problem_analysis.get('keywords', [])
            component = problem_analysis.get('component', '')
            search_query = f"{problem} {component} {' '.join(keywords[:3])}"
            
            # Get embedding and search
            query_embedding = self.llm_service.generate_embedding(search_query)
            search_results = self.vector_store.search(query_embedding, top_k=5)
            
            # Format context
            context_parts = []
            for i, result in enumerate(search_results[:3], 1):
                context_parts.append(f"[Doc {i}] {result['content'][:300]}...")
            
            return "\n\n".join(context_parts) if context_parts else "No relevant documentation found."
            
        except Exception as e:
            logger.error(f"Error searching documentation: {e}")
            return "Documentation search unavailable."
    
    def _synthesize_solution(self, problem: str, problem_analysis: Dict, 
                                   historical_matches: List[Dict], diagnostic_data: List[Dict],
                                   doc_context: str) -> Dict[str, Any]:
        """Use LLM to synthesize all data into intelligent root cause analysis"""
        try:
            # Build comprehensive context for LLM
            synthesis_prompt = f"""{self.diagnostic_prompt}

**USER'S PROBLEM:**
{problem}

**PROBLEM ANALYSIS:**
Component: {problem_analysis.get('component')}
Symptom: {problem_analysis.get('symptom')}
Severity: {problem_analysis.get('severity')}

**DIAGNOSTIC QUERY RESULTS:**
"""
            
            # Add diagnostic data - only successful queries
            successful_queries = [r for r in diagnostic_data if r['success'] and r['row_count'] > 0]
            failed_queries = [r for r in diagnostic_data if not r['success']]
            
            if successful_queries:
                synthesis_prompt += f"\n\n**DIAGNOSTIC DATA ({len(successful_queries)} queries successful):**\n"
                for result in successful_queries:
                    synthesis_prompt += f"\n{'-' * 40}\n"
                    synthesis_prompt += f"Query: {result['purpose']}\n"
                    synthesis_prompt += f"Found: {result['row_count']} records\n"
                    if result['row_count'] > 0:
                        synthesis_prompt += f"Sample: {result['data'][:3]}\n"
            else:
                synthesis_prompt += f"\n\n**NOTE:** No diagnostic queries returned data. Provide general troubleshooting advice.\n"
            
            # Add historical context
            if historical_matches:
                synthesis_prompt += f"\n\n**HISTORICAL SIMILAR ISSUES:**\n"
                for i, match in enumerate(historical_matches[:2], 1):
                    synthesis_prompt += f"\n{i}. {match['problem']}\n"
                    synthesis_prompt += f"   Solution: {match['solution'][:200]}...\n"
            
            # Add documentation context
            synthesis_prompt += f"\n\n**RELEVANT DOCUMENTATION:**\n{doc_context}\n"
            
            # Request structured analysis
            synthesis_prompt += """

**PROVIDE A CONCISE DIAGNOSIS (MAX 300 WORDS):**

## Root Cause
[1-2 sentences: What's wrong based on the data]

## What I Found
[3-4 bullet points of actual findings from queries]

## Solution
[3-5 numbered steps to fix it]

## Next Steps
[2-3 immediate actions]

Be specific and concise. Reference actual data. Skip generic advice about schema."""

            # Generate response
            messages = [{"role": "user", "content": synthesis_prompt}]
            response_text = self.llm_service.generate_response(
                messages=messages,
                system_prompt=self.diagnostic_prompt,
                max_tokens=2000,
                temperature=0.5
            )
            
            # Calculate confidence based on data quality
            confidence = self._calculate_confidence(diagnostic_data, historical_matches)
            
            return {
                "response": response_text,
                "confidence": confidence,
                "sources": []
            }
            
        except Exception as e:
            logger.error(f"Error synthesizing solution: {e}")
            return {
                "response": f"I was able to gather diagnostic data but encountered an error synthesizing the solution: {str(e)}",
                "confidence": 0.3,
                "sources": []
            }
    
    def _calculate_confidence(self, diagnostic_data: List[Dict], historical_matches: List[Dict]) -> float:
        """Calculate confidence score based on available data"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence if queries succeeded
        successful_queries = sum(1 for d in diagnostic_data if d['success'])
        total_queries = len(diagnostic_data)
        if total_queries > 0:
            confidence += 0.2 * (successful_queries / total_queries)
        
        # Increase if we found relevant data
        queries_with_data = sum(1 for d in diagnostic_data if d.get('row_count', 0) > 0)
        if queries_with_data > 0:
            confidence += 0.2
        
        # Increase if historical matches exist
        if historical_matches and len(historical_matches) > 0:
            confidence += 0.1
        
        return min(confidence, 0.95)  # Cap at 95%
