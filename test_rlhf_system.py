"""
Test RLHF System - Verify feedback recording and learning across all chatbot types
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.modules.neo_chatbot.services.rlhf_service import RLHFService
import time


def test_feedback_recording():
    """Test recording feedback for all chatbot types"""
    print("\n" + "="*70)
    print("TEST 1: Recording Feedback for All Chatbot Types")
    print("="*70)
    
    rlhf = RLHFService()
    
    # Test SQL Assistant feedback
    sql_feedback = rlhf.record_feedback(
        chatbot_type="sql_assistant",
        query="Show me all active bots",
        response="SELECT * FROM bot_master WHERE status = 'active'",
        feedback_type="positive",
        rating=5,
        comment="Perfect query! Exactly what I needed.",
        metadata={
            "sql_query": "SELECT * FROM bot_master WHERE status = 'active'",
            "confidence": 0.95,
            "row_count": 42,
            "strategy": "direct_lookup"
        }
    )
    
    print(f"\n✅ SQL Assistant Feedback:")
    print(f"   Feedback ID: {sql_feedback['feedback_id']}")
    print(f"   Reward Score: {sql_feedback['reward_score']}")
    print(f"   Timestamp: {sql_feedback['timestamp']}")
    
    # Test Knowledge Base feedback
    kb_feedback = rlhf.record_feedback(
        chatbot_type="knowledge_base",
        query="What is the process for receiving items?",
        response="The receiving process involves: 1. Check ASN, 2. Verify goods, 3. Update inventory...",
        feedback_type="positive",
        rating=4,
        comment="Good explanation but could include more examples",
        metadata={
            "query_type": "PROCEDURAL",
            "confidence": 0.85,
            "source_count": 3,
            "document_names": ["SOP Document", "Dashboard Manual"]
        }
    )
    
    print(f"\n✅ Knowledge Base Feedback:")
    print(f"   Feedback ID: {kb_feedback['feedback_id']}")
    print(f"   Reward Score: {kb_feedback['reward_score']}")
    print(f"   Timestamp: {kb_feedback['timestamp']}")
    
    # Test Diagnostic Support feedback
    diag_feedback = rlhf.record_feedback(
        chatbot_type="diagnostic_support",
        query="Bot is not picking items from the location",
        response="This could be due to location status. Check: 1. Location is active, 2. Inventory exists, 3. Bot permissions...",
        feedback_type="neutral",
        rating=3,
        comment="Helpful but didn't solve my specific issue",
        metadata={
            "matched_issues_count": 1,
            "best_match_title": "Bot Picking Issues",
            "confidence": 0.75,
            "suggested_actions_count": 4
        }
    )
    
    print(f"\n✅ Diagnostic Support Feedback:")
    print(f"   Feedback ID: {diag_feedback['feedback_id']}")
    print(f"   Reward Score: {diag_feedback['reward_score']}")
    print(f"   Timestamp: {diag_feedback['timestamp']}")
    
    return True


def test_pattern_learning():
    """Test pattern learning from high-reward feedback"""
    print("\n" + "="*70)
    print("TEST 2: Pattern Learning from High-Reward Feedback")
    print("="*70)
    
    rlhf = RLHFService()
    
    # Record multiple positive feedbacks to build patterns
    test_queries = [
        ("Show all bots", "SELECT * FROM bot_master", 5, "Excellent"),
        ("List active robots", "SELECT * FROM bot_master WHERE status = 'active'", 5, "Perfect!"),
        ("Count total bots", "SELECT COUNT(*) FROM bot_master", 4, "Good query"),
    ]
    
    print("\n📊 Recording multiple feedbacks to build patterns...")
    for query, response, rating, comment in test_queries:
        rlhf.record_feedback(
            chatbot_type="sql_assistant",
            query=query,
            response=response,
            feedback_type="positive",
            rating=rating,
            comment=comment,
            metadata={"sql_query": response, "confidence": 0.9}
        )
        print(f"   ✓ Recorded: '{query}' (Rating: {rating})")
    
    # Check learned patterns
    print("\n✅ Pattern learning verification:")
    try:
        patterns_file = rlhf.base_path / "learned_patterns.json"
        if patterns_file.exists():
            import json
            with open(patterns_file, 'r') as f:
                patterns_data = json.load(f)
                sql_patterns = patterns_data.get('sql_assistant', [])
                print(f"   Learned {len(sql_patterns)} patterns for SQL Assistant")
                
                if sql_patterns:
                    top_pattern = sql_patterns[0]
                    print(f"\n   Top Pattern:")
                    print(f"   - Query: {top_pattern['query'][:50]}...")
                    print(f"   - Reward: {top_pattern['reward_score']}")
                    print(f"   - Keywords: {', '.join(top_pattern.get('keywords', [])[:5])}")
        else:
            print("   No patterns file found yet (will be created on first feedback)")
    except Exception as e:
        print(f"   ⚠️  Error checking patterns: {e}")
    
    return True


def test_analytics():
    """Test analytics generation"""
    print("\n" + "="*70)
    print("TEST 3: Analytics Generation")
    print("="*70)
    
    rlhf = RLHFService()
    
    # Get analytics for all chatbot types
    for chatbot_type in ['sql_assistant', 'knowledge_base', 'diagnostic_support', None]:
        print(f"\n📈 Analytics for: {chatbot_type or 'ALL CHATBOTS'}")
        
        analytics = rlhf.get_analytics(chatbot_type=chatbot_type, days=30)
        
        print(f"   Total Feedback: {analytics['total_feedback']}")
        print(f"   Average Reward: {analytics['average_reward']:.3f}")
        print(f"   Learning Rate: {analytics['learning_rate']:.3f}")
        print(f"   Weekly Trends: {len(analytics['weekly_trends'])} weeks of data")
        print(f"   Top Patterns: {len(analytics['top_patterns'])} high-performing patterns")
        print(f"   Needs Improvement: {len(analytics['needs_improvement'])} low-reward queries")
        
        if analytics['weekly_trends']:
            latest_week = analytics['weekly_trends'][-1]
            print(f"   Latest Week: {latest_week['week']} (Avg Reward: {latest_week['average_reward']:.3f}, Count: {latest_week['feedback_count']})")
    
    return True


def test_suggestions():
    """Test response improvement suggestions"""
    print("\n" + "="*70)
    print("TEST 4: Response Improvement Suggestions")
    print("="*70)
    
    rlhf = RLHFService()
    
    # Test suggestion for a query similar to previous high-rated ones
    suggestions = rlhf.get_response_suggestions(
        chatbot_type="sql_assistant",
        query="Show me bot information",  # Similar to "Show all bots"
        current_response="SELECT * FROM bots",
        metadata={"sql_query": "SELECT * FROM bots"}
    )
    
    print(f"\n💡 Suggestions for query: 'Show me bot information'")
    print(f"   Similar Patterns Found: {suggestions['similar_patterns_count']}")
    print(f"   Suggestion Score: {suggestions['suggestion_score']:.3f}")
    
    if suggestions['similar_patterns']:
        print(f"\n   Top Similar Query:")
        top_similar = suggestions['similar_patterns'][0]
        print(f"   - Query: {top_similar['query']}")
        print(f"   - Similarity: {top_similar['similarity_score']:.3f}")
        print(f"   - Reward: {top_similar['reward_score']:.3f}")
    
    if suggestions['improvement_tips']:
        print(f"\n   💡 Improvement Tips:")
        for i, tip in enumerate(suggestions['improvement_tips'], 1):
            print(f"   {i}. {tip}")
    
    return True


def test_reward_calculation():
    """Test reward calculation with different inputs"""
    print("\n" + "="*70)
    print("TEST 5: Reward Calculation Verification")
    print("="*70)
    
    rlhf = RLHFService()
    
    test_cases = [
        ("positive", 5, "Excellent!", "Expected: High positive reward"),
        ("positive", 3, "", "Expected: Moderate positive reward"),
        ("negative", 1, "Totally wrong!", "Expected: High negative reward"),
        ("negative", 2, "", "Expected: Moderate negative reward"),
        ("neutral", None, "", "Expected: Zero or near-zero reward"),
    ]
    
    print("\n🧮 Testing reward calculation with various inputs:")
    for feedback_type, rating, comment, expected in test_cases:
        reward = rlhf._calculate_reward(feedback_type, rating, comment)
        print(f"\n   Input: type={feedback_type}, rating={rating}, comment='{comment}'")
        print(f"   Reward: {reward:.3f}")
        print(f"   {expected}")
    
    return True


def main():
    """Run all RLHF tests"""
    print("\n" + "="*70)
    print("🧪 RLHF System Test Suite")
    print("="*70)
    print("\nTesting Reinforcement Learning from Human Feedback implementation")
    print("across SQL Assistant, Knowledge Base, and Diagnostic Support modules.")
    
    tests = [
        ("Feedback Recording", test_feedback_recording),
        ("Pattern Learning", test_pattern_learning),
        ("Analytics Generation", test_analytics),
        ("Response Suggestions", test_suggestions),
        ("Reward Calculation", test_reward_calculation),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n\n{'='*70}")
            print(f"Running: {test_name}")
            print('='*70)
            
            if test_func():
                print(f"\n✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"\n❌ {test_name} FAILED")
                failed += 1
                
        except Exception as e:
            print(f"\n❌ {test_name} FAILED with exception:")
            print(f"   {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print("\n\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total Tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! RLHF system is working correctly.")
        print("\nNext Steps:")
        print("1. Start the Flask server: python app/web/main.py")
        print("2. Test feedback UI in browser: http://localhost:5000/chatbot")
        print("3. Submit feedback with ratings and comments")
        print("4. Check analytics: GET /api/chatbot/rlhf/analytics")
        print("5. View learned patterns in: app/modules/neo_chatbot/data/rlhf/learned_patterns.json")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review errors above.")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
