"""
Diagnostic Service - Automated troubleshooting and issue resolution
Helps users diagnose and solve NEO system issues
"""

import logging
import json
import csv
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path

from .llm_service import LLMService
from ..models.schemas import ChatRequest, ChatResponse, ChatbotType, DiagnosticIssue, SystemHealthStatus

logger = logging.getLogger(__name__)


class DiagnosticService:
    """
    Service for system diagnostics and troubleshooting
    Loads issue knowledge base and provides guided support
    """
    
    def __init__(self):
        """Initialize diagnostic service"""
        self.llm_service = LLMService()
        self.issues_db = self._load_issues_database()
        
        self.system_prompt = """You are a troubleshooting expert for the NEO Warehouse Management System.

When helping users with issues:
1. Listen to their problem description carefully
2. Match symptoms to known issues
3. Guide them through diagnostic steps one at a time
4. Provide clear, step-by-step solutions
5. Explain what each step does
6. Offer prevention tips

Be patient, clear, and supportive. Break down complex solutions into simple steps."""

        logger.info(f"✅ Diagnostic Service initialized with {len(self.issues_db)} known issues")
    
    def _load_issues_database(self) -> List[Dict[str, Any]]:
        """Load support issues from JSON or CSV file"""
        try:
            base_path = Path(__file__).parent.parent / "data" / "support"
            
            # Try JSON first
            json_path = base_path / "issues.json"
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    issues = data.get("issues", [])
                    logger.info(f"📂 Loaded {len(issues)} issues from {json_path}")
                    return issues
            
            # Try CSV
            csv_path = base_path / "issues.csv"
            if csv_path.exists():
                issues = []
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Parse pipe-separated fields
                        issue = {
                            "issue_id": row.get("issue_id", ""),
                            "issue_name": row.get("issue_name", ""),
                            "category": row.get("category", ""),
                            "severity": row.get("severity", "medium"),
                            "symptoms": row.get("symptoms", "").split("|"),
                            "root_causes": row.get("root_causes", "").split("|"),
                            "diagnostic_steps": row.get("diagnostic_steps", "").split("|"),
                            "solution_1_title": row.get("solution_1_title", ""),
                            "solution_1_steps": row.get("solution_1_steps", ""),
                            "solution_1_type": row.get("solution_1_type", ""),
                            "solution_2_title": row.get("solution_2_title", ""),
                            "solution_2_steps": row.get("solution_2_steps", ""),
                            "solution_2_type": row.get("solution_2_type", ""),
                            "prevention": row.get("prevention", "").split("|")
                        }
                        issues.append(issue)
                logger.info(f"📂 Loaded {len(issues)} issues from {csv_path}")
                return issues
            
            logger.warning("⚠️ No issues.json or issues.csv found in data/support/")
            return []
            
        except Exception as e:
            logger.error(f"❌ Error loading issues database: {e}")
            return []
    
    def process_query(self, chat_request: ChatRequest) -> ChatResponse:
        """
        Process diagnostic query and provide troubleshooting guidance
        
        Args:
            chat_request: User's chat request
            
        Returns:
            Chat response with diagnostic guidance
        """
        try:
            logger.info(f"🔍 Processing diagnostic query: {chat_request.message[:50]}...")
            
            # Check if we have issues in the database
            if not self.issues_db:
                return self._handle_no_issues_db(chat_request)
            
            # Find matching issues based on symptoms
            matching_issues = self._find_matching_issues(chat_request.message)
            
            if matching_issues:
                # Guide user through the most relevant issue
                best_match = matching_issues[0]
                response_text = self._generate_diagnostic_response(best_match, chat_request.message)
            else:
                # No direct match, use LLM for general troubleshooting
                response_text = self._generate_general_diagnostic_response(chat_request)
            
            return ChatResponse(
                response=response_text,
                chatbot_type=ChatbotType.DIAGNOSTIC,
                session_id=chat_request.session_id or str(uuid.uuid4()),
                confidence_score=0.9 if matching_issues else 0.5,
                suggested_actions=self._generate_diagnostic_actions(matching_issues)
            )
            
        except Exception as e:
            logger.error(f"❌ Error processing diagnostic query: {e}", exc_info=True)
            return ChatResponse(
                response="I apologize, but I encountered an error while processing your diagnostic request. Please describe your issue in more detail.",
                chatbot_type=ChatbotType.DIAGNOSTIC,
                session_id=chat_request.session_id or str(uuid.uuid4()),
                confidence_score=0.0
            )
    
    def _handle_no_issues_db(self, chat_request: ChatRequest) -> ChatResponse:
        """Handle case when no issues database is available"""
        return ChatResponse(
            response="""I don't have a support issues database loaded yet.

To enable diagnostic support:
1. Create a file: app/modules/neo_chatbot/data/support/issues.json (or issues.csv)
2. Add your common issues, symptoms, and solutions
3. See the README in that folder for templates

Currently I can still help with:
- General troubleshooting advice
- System best practices
- Documentation questions

What issue are you experiencing?""",
            chatbot_type=ChatbotType.DIAGNOSTIC,
            session_id=chat_request.session_id or str(uuid.uuid4()),
            confidence_score=0.0,
            suggested_actions=["Create issues database", "Ask general question", "View documentation"]
        )
    
    def _find_matching_issues(self, query: str) -> List[Dict[str, Any]]:
        """Find issues matching the user's query"""
        query_lower = query.lower()
        matches = []
        
        for issue in self.issues_db:
            score = 0
            
            # Check issue name
            if issue.get("issue_name", "").lower() in query_lower:
                score += 10
            
            # Check category
            if issue.get("category", "").lower() in query_lower:
                score += 5
            
            # Check symptoms
            symptoms = issue.get("symptoms", [])
            if isinstance(symptoms, str):
                symptoms = symptoms.split("|")
            
            for symptom in symptoms:
                if symptom.strip().lower() in query_lower:
                    score += 3
            
            # Check keywords
            keywords = ["error", "fail", "not working", "issue", "problem", "broken"]
            for keyword in keywords:
                if keyword in query_lower and keyword in issue.get("issue_name", "").lower():
                    score += 2
            
            if score > 0:
                matches.append({"issue": issue, "score": score})
        
        # Sort by score
        matches.sort(key=lambda x: x["score"], reverse=True)
        return [m["issue"] for m in matches[:3]]  # Return top 3 matches
    
    def _generate_diagnostic_response(self, issue: Dict[str, Any], user_query: str) -> str:
        """Generate diagnostic response for a specific issue"""
        response_parts = []
        
        # Issue identification
        response_parts.append(f"🔍 **Issue Identified: {issue.get('issue_name', 'Unknown Issue')}**")
        response_parts.append(f"Category: {issue.get('category', 'Unknown')} | Severity: {issue.get('severity', 'Unknown').upper()}")
        response_parts.append("")
        
        # Symptoms confirmation
        symptoms = issue.get("symptoms", [])
        if isinstance(symptoms, str):
            symptoms = symptoms.split("|")
        
        if symptoms:
            response_parts.append("**Symptoms you might be experiencing:**")
            for symptom in symptoms[:3]:  # Show top 3
                response_parts.append(f"• {symptom.strip()}")
            response_parts.append("")
        
        # Diagnostic steps
        diagnostic_steps = issue.get("diagnostic_steps", [])
        if isinstance(diagnostic_steps, str):
            diagnostic_steps = diagnostic_steps.split("|")
        
        if diagnostic_steps:
            response_parts.append("**Let's diagnose this step by step:**")
            for i, step in enumerate(diagnostic_steps[:3], 1):  # Show first 3 steps
                response_parts.append(f"{i}. {step.strip()}")
            response_parts.append("")
        
        # Solution 1
        sol1_title = issue.get("solution_1_title", "")
        sol1_steps = issue.get("solution_1_steps", "")
        sol1_type = issue.get("solution_1_type", "")
        
        if sol1_title and sol1_steps:
            response_parts.append(f"**Solution 1: {sol1_title}** ({sol1_type})")
            response_parts.append(f"Steps: {sol1_steps}")
            response_parts.append("")
        
        # Solution 2 (if available)
        sol2_title = issue.get("solution_2_title", "")
        sol2_steps = issue.get("solution_2_steps", "")
        
        if sol2_title and sol2_steps:
            response_parts.append(f"**Alternative Solution: {sol2_title}**")
            response_parts.append(f"Steps: {sol2_steps}")
            response_parts.append("")
        
        # Prevention tips
        prevention = issue.get("prevention", [])
        if isinstance(prevention, str):
            prevention = prevention.split("|")
        
        if prevention:
            response_parts.append("**Prevention Tips:**")
            for tip in prevention:
                if tip.strip():
                    response_parts.append(f"• {tip.strip()}")
        
        response_parts.append("\n📝 **Need more help?** Let me know which step you need clarification on, or if the issue persists.")
        
        return "\n".join(response_parts)
    
    def _generate_general_diagnostic_response(self, chat_request: ChatRequest) -> str:
        """Generate general diagnostic response using LLM"""
        messages = [{
            "role": "user",
            "content": f"""A user is reporting this issue with the NEO system:

"{chat_request.message}"

Provide troubleshooting guidance:
1. What might be causing this
2. Step-by-step diagnostic steps
3. Possible solutions
4. Prevention tips"""
        }]
        
        return self.llm_service.generate_response(
            messages=messages,
            system_prompt=self.system_prompt,
            max_tokens=800,
            temperature=0.7
        )
    
    def _generate_diagnostic_actions(self, matching_issues: List[Dict[str, Any]]) -> List[str]:
        """Generate suggested actions based on matching issues"""
        if not matching_issues:
            return [
                "Describe your issue in more detail",
                "Check system logs",
                "Contact support"
            ]
        
        actions = []
        for issue in matching_issues[:2]:
            category = issue.get("category", "")
            if category == "database":
                actions.append("Check database connection")
            elif category == "scheduler":
                actions.append("Verify scheduler status")
            elif category == "mining":
                actions.append("Review mining parameters")
        
        actions.append("View detailed diagnostics")
        return actions[:3]
    
    def check_system_health(self) -> SystemHealthStatus:
        """
        Check overall system health
        
        Returns:
            System health status with component statuses and issues
        """
        # This is a placeholder - would connect to actual system monitoring
        components = {
            "database": "healthy",
            "api": "healthy",
            "scheduler": "healthy",
            "mining_engine": "healthy"
        }
        
        return SystemHealthStatus(
            overall_status="healthy",
            components=components,
            issues=[]
        )
    
    def get_issue_by_id(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific issue by ID"""
        for issue in self.issues_db:
            if issue.get("issue_id") == issue_id:
                return issue
        return None
    
    def get_issues_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all issues in a specific category"""
        return [issue for issue in self.issues_db if issue.get("category") == category]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get diagnostic service statistics"""
        categories = {}
        severities = {}
        
        for issue in self.issues_db:
            cat = issue.get("category", "unknown")
            sev = issue.get("severity", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
            severities[sev] = severities.get(sev, 0) + 1
        
        return {
            "total_issues": len(self.issues_db),
            "categories": categories,
            "severities": severities,
            "llm_provider": self.llm_service.get_provider_info()
        }
