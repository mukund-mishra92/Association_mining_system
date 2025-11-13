"""
RLHF Service - Reinforcement Learning from Human Feedback
Learns from user feedback to improve chatbot responses across all modules
"""

import logging
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)


class RLHFService:
    """
    Central RLHF service that learns from human feedback
    
    Features:
    - Feedback collection with detailed ratings
    - Reward model for response quality
    - Pattern learning and preference tracking
    - Response optimization suggestions
    - Performance analytics
    """
    
    def __init__(self):
        """Initialize RLHF service"""
        self.data_dir = Path(__file__).parent.parent / "data" / "rlhf"
        self.base_path = self.data_dir  # Add alias for backward compatibility
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.feedback_file = self.data_dir / "feedback_history.jsonl"
        self.rewards_file = self.data_dir / "reward_model.json"
        self.patterns_file = self.data_dir / "learned_patterns.json"
        
        # Load existing data
        self.reward_model = self._load_reward_model()
        self.learned_patterns = self._load_learned_patterns()
        
        logger.info("✅ RLHF Service initialized")
    
    def record_feedback(
        self,
        chatbot_type: str,
        query: str,
        response: str,
        feedback_type: str,
        rating: Optional[int] = None,
        comment: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Record user feedback for a chatbot response
        
        Args:
            chatbot_type: Type of chatbot (sql_assistant, knowledge_base, diagnostic)
            query: User's original query
            response: Chatbot's response
            feedback_type: Type of feedback (positive, negative, neutral)
            rating: Numerical rating 1-5 (optional)
            comment: User's text comment (optional)
            metadata: Additional context (SQL query, sources, etc.)
        
        Returns:
            Feedback record with calculated reward
        """
        try:
            feedback_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            # Calculate reward score based on feedback
            reward_score = self._calculate_reward(feedback_type, rating, comment)
            
            feedback_record = {
                "feedback_id": feedback_id,
                "timestamp": timestamp,
                "chatbot_type": chatbot_type,
                "query": query,
                "response": response[:500],  # Truncate long responses
                "feedback_type": feedback_type,
                "rating": rating,
                "comment": comment,
                "reward_score": reward_score,
                "metadata": metadata or {}
            }
            
            # Save to feedback history
            self._append_feedback(feedback_record)
            
            # Update reward model
            self._update_reward_model(chatbot_type, feedback_record)
            
            # Learn patterns from feedback
            self._learn_patterns(chatbot_type, query, response, reward_score, metadata)
            
            logger.info(f"📝 Feedback recorded: {chatbot_type} | {feedback_type} | Reward: {reward_score:.2f}")
            
            return feedback_record
            
        except Exception as e:
            logger.error(f"❌ Error recording feedback: {e}", exc_info=True)
            return {}
    
    def get_response_suggestions(
        self,
        chatbot_type: str,
        query: str,
        current_response: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Get suggestions to improve response based on learned patterns
        
        Args:
            chatbot_type: Type of chatbot
            query: User's query
            current_response: Current generated response
            metadata: Additional context
        
        Returns:
            Suggestions for improvement
        """
        try:
            # Find similar queries with high rewards
            similar_patterns = self._find_similar_patterns(chatbot_type, query)
            
            suggestions = {
                "similar_patterns_count": len(similar_patterns),
                "suggestion_score": 0.0,
                "similar_patterns": [],
                "improvement_tips": []
            }
            
            if similar_patterns:
                avg_reward = np.mean([p['reward'] for p in similar_patterns])
                suggestions["suggestion_score"] = round(avg_reward, 2)
                
                # Extract high reward patterns
                high_reward_patterns = [p for p in similar_patterns if p['reward'] > 0.7]
                
                # Add similar pattern details
                for pattern in similar_patterns[:5]:
                    suggestions["similar_patterns"].append({
                        "query": pattern['query'],
                        "response_snippet": pattern['response'][:200],
                        "reward_score": round(pattern['reward'], 3),
                        "similarity_score": pattern.get('similarity', 1.0)
                    })
                
                # Generate improvement tips
                suggestions["improvement_tips"] = self._generate_improvement_tips(
                    chatbot_type, query, current_response, high_reward_patterns
                )
            
            return suggestions
            
        except Exception as e:
            logger.error(f"❌ Error getting suggestions: {e}", exc_info=True)
            return {
                "similar_patterns_count": 0,
                "suggestion_score": 0.0,
                "similar_patterns": [],
                "improvement_tips": []
            }
    
    def get_analytics(
        self,
        chatbot_type: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get RLHF analytics and performance metrics
        
        Args:
            chatbot_type: Filter by chatbot type (optional)
            days: Number of days to analyze
        
        Returns:
            Analytics data
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            feedbacks = self._load_recent_feedback(cutoff_date, chatbot_type)
            
            if not feedbacks:
                return {
                    "total_feedback": 0,  # Changed from total_feedbacks
                    "average_reward": 0.0,
                    "feedback_distribution": {},
                    "weekly_trends": [],  # Changed from improvement_trend
                    "top_patterns": [],
                    "needs_improvement": [],
                    "learning_rate": 0.0
                }
            
            # Calculate metrics
            total = len(feedbacks)
            avg_reward = np.mean([f['reward_score'] for f in feedbacks])
            
            feedback_dist = defaultdict(int)
            for f in feedbacks:
                feedback_dist[f['feedback_type']] += 1
            
            # Calculate improvement trend (week by week)
            trend = self._calculate_trend(feedbacks)
            
            # Top performing patterns
            top_patterns = self._get_top_patterns(chatbot_type, limit=5)
            
            # Areas needing improvement
            low_reward_queries = [
                {"query": f['query'], "reward": f['reward_score']}
                for f in feedbacks
                if f['reward_score'] < 0.3
            ][:10]
            
            analytics = {
                "total_feedback": total,  # Changed from total_feedbacks to match API expectations
                "average_reward": round(avg_reward, 2),
                "feedback_distribution": dict(feedback_dist),
                "weekly_trends": trend,  # Changed from improvement_trend for clarity
                "top_patterns": top_patterns,
                "needs_improvement": low_reward_queries,
                "learning_rate": self._calculate_learning_rate(feedbacks)
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"❌ Error calculating analytics: {e}", exc_info=True)
            return {}
    
    def _calculate_reward(
        self,
        feedback_type: str,
        rating: Optional[int],
        comment: Optional[str]
    ) -> float:
        """
        Calculate reward score from feedback
        
        Reward scale: -1.0 to 1.0
        """
        # Base reward from feedback type
        base_rewards = {
            "positive": 0.8,
            "neutral": 0.0,
            "negative": -0.8
        }
        
        reward = base_rewards.get(feedback_type, 0.0)
        
        # Adjust based on rating (1-5 scale)
        if rating is not None:
            # Convert 1-5 to -1 to 1 scale
            rating_reward = (rating - 3) / 2.0  # 1→-1, 3→0, 5→1
            reward = (reward + rating_reward) / 2.0  # Average the two
        
        # Boost for detailed comments (shows engagement)
        if comment and len(comment) > 20:
            reward += 0.1
        
        # Clamp to [-1, 1]
        return max(-1.0, min(1.0, reward))
    
    def _update_reward_model(self, chatbot_type: str, feedback: Dict):
        """Update the reward model with new feedback"""
        if chatbot_type not in self.reward_model:
            self.reward_model[chatbot_type] = {
                "total_feedbacks": 0,
                "total_reward": 0.0,
                "average_reward": 0.0,
                "last_updated": None
            }
        
        model = self.reward_model[chatbot_type]
        model["total_feedbacks"] += 1
        model["total_reward"] += feedback["reward_score"]
        model["average_reward"] = model["total_reward"] / model["total_feedbacks"]
        model["last_updated"] = feedback["timestamp"]
        
        self._save_reward_model()
    
    def _learn_patterns(
        self,
        chatbot_type: str,
        query: str,
        response: str,
        reward: float,
        metadata: Optional[Dict]
    ):
        """Learn patterns from successful/unsuccessful interactions"""
        if chatbot_type not in self.learned_patterns:
            self.learned_patterns[chatbot_type] = []
        
        # Extract query features
        query_lower = query.lower()
        query_length = len(query.split())
        
        pattern = {
            "query": query,
            "query_keywords": self._extract_keywords(query),
            "query_length": query_length,
            "response": response[:500],
            "response_length": len(response),
            "reward": reward,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        # Store pattern
        self.learned_patterns[chatbot_type].append(pattern)
        
        # Keep only recent patterns (last 1000)
        if len(self.learned_patterns[chatbot_type]) > 1000:
            self.learned_patterns[chatbot_type] = sorted(
                self.learned_patterns[chatbot_type],
                key=lambda x: x['timestamp'],
                reverse=True
            )[:1000]
        
        self._save_learned_patterns()
    
    def _find_similar_patterns(
        self,
        chatbot_type: str,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:
        """Find similar queries with their rewards"""
        if chatbot_type not in self.learned_patterns:
            return []
        
        patterns = self.learned_patterns[chatbot_type]
        query_keywords = set(self._extract_keywords(query))
        
        # Calculate similarity scores
        scored_patterns = []
        for pattern in patterns:
            pattern_keywords = set(pattern['query_keywords'])
            
            # Jaccard similarity
            if not query_keywords or not pattern_keywords:
                similarity = 0.0
            else:
                similarity = len(query_keywords & pattern_keywords) / len(query_keywords | pattern_keywords)
            
            if similarity > 0.1:  # Minimum similarity threshold
                scored_patterns.append({
                    **pattern,
                    'similarity': similarity
                })
        
        # Sort by similarity and reward
        scored_patterns.sort(
            key=lambda x: (x['similarity'] * 0.6 + x['reward'] * 0.4),
            reverse=True
        )
        
        return scored_patterns[:top_k]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        # Simple keyword extraction (could be enhanced with NLP)
        stopwords = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = text.lower().split()
        keywords = [w for w in words if len(w) > 3 and w not in stopwords]
        return keywords[:10]  # Top 10 keywords
    
    def _generate_improvement_tips(
        self,
        chatbot_type: str,
        query: str,
        current_response: str,
        high_reward_patterns: List[Dict]
    ) -> List[str]:
        """Generate specific improvement tips"""
        tips = []
        
        if not high_reward_patterns:
            return tips
        
        # Analyze successful patterns
        avg_response_length = np.mean([len(p['response']) for p in high_reward_patterns])
        current_length = len(current_response)
        
        if current_length < avg_response_length * 0.5:
            tips.append("Consider providing more detailed information based on successful similar queries")
        elif current_length > avg_response_length * 2:
            tips.append("Response might be too verbose - successful similar queries were more concise")
        
        # Check for common elements in successful responses
        if chatbot_type == "sql_assistant":
            if any("LIMIT" in p['metadata'].get('sql_query', '') for p in high_reward_patterns):
                tips.append("Successful queries often include LIMIT clause for better performance")
        
        elif chatbot_type == "knowledge_base":
            if any(len(p['metadata'].get('sources', [])) > 2 for p in high_reward_patterns):
                tips.append("Highly rated responses typically cite multiple source documents")
        
        return tips
    
    def _calculate_trend(self, feedbacks: List[Dict]) -> List[Dict]:
        """Calculate weekly improvement trend"""
        weekly_rewards = defaultdict(list)
        
        for f in feedbacks:
            timestamp = datetime.fromisoformat(f['timestamp'])
            week = timestamp.strftime("%Y-W%U")
            weekly_rewards[week].append(f['reward_score'])
        
        trend = []
        for week in sorted(weekly_rewards.keys()):
            trend.append({
                "week": week,
                "average_reward": round(np.mean(weekly_rewards[week]), 2),
                "feedback_count": len(weekly_rewards[week])
            })
        
        return trend
    
    def _calculate_learning_rate(self, feedbacks: List[Dict]) -> float:
        """Calculate how fast the system is improving"""
        if len(feedbacks) < 10:
            return 0.0
        
        # Split into first half and second half
        mid = len(feedbacks) // 2
        first_half_reward = np.mean([f['reward_score'] for f in feedbacks[:mid]])
        second_half_reward = np.mean([f['reward_score'] for f in feedbacks[mid:]])
        
        improvement = second_half_reward - first_half_reward
        return round(improvement, 3)
    
    def _get_top_patterns(self, chatbot_type: Optional[str], limit: int) -> List[Dict]:
        """Get top performing patterns"""
        all_patterns = []
        
        if chatbot_type:
            patterns = self.learned_patterns.get(chatbot_type, [])
            all_patterns.extend([{**p, 'chatbot_type': chatbot_type} for p in patterns])
        else:
            for ctype, patterns in self.learned_patterns.items():
                all_patterns.extend([{**p, 'chatbot_type': ctype} for p in patterns])
        
        # Sort by reward
        all_patterns.sort(key=lambda x: x['reward'], reverse=True)
        
        return [
            {
                "chatbot_type": p['chatbot_type'],
                "query": p['query'],
                "reward": p['reward'],
                "timestamp": p['timestamp']
            }
            for p in all_patterns[:limit]
        ]
    
    def _append_feedback(self, feedback: Dict):
        """Append feedback to JSONL file"""
        with open(self.feedback_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(feedback) + '\n')
    
    def _load_recent_feedback(
        self,
        cutoff_date: datetime,
        chatbot_type: Optional[str] = None
    ) -> List[Dict]:
        """Load recent feedback from file"""
        if not self.feedback_file.exists():
            return []
        
        feedbacks = []
        with open(self.feedback_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    feedback = json.loads(line.strip())
                    timestamp = datetime.fromisoformat(feedback['timestamp'])
                    
                    if timestamp >= cutoff_date:
                        if chatbot_type is None or feedback['chatbot_type'] == chatbot_type:
                            feedbacks.append(feedback)
                except Exception as e:
                    logger.warning(f"Error parsing feedback line: {e}")
        
        return feedbacks
    
    def _load_reward_model(self) -> Dict:
        """Load reward model from file"""
        if self.rewards_file.exists():
            try:
                with open(self.rewards_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading reward model: {e}")
        
        return {}
    
    def _save_reward_model(self):
        """Save reward model to file"""
        try:
            with open(self.rewards_file, 'w', encoding='utf-8') as f:
                json.dump(self.reward_model, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving reward model: {e}")
    
    def _load_learned_patterns(self) -> Dict:
        """Load learned patterns from file"""
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading learned patterns: {e}")
        
        return {}
    
    def _save_learned_patterns(self):
        """Save learned patterns to file"""
        try:
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(self.learned_patterns, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving learned patterns: {e}")
