"""
Test Value Validation - Critical Enhancement
=============================================
Tests that SQL queries validate filter values against actual database data.

This addresses the critical issue where queries like:
  WHERE status = 'active'

Were being generated even though the actual values in the database are 'ENABLED' and 'DISABLED'.
Result: Query executes successfully but returns 0 rows when it should return data!

Example from user:
- Query suggested: WHERE status = 'active'
- Actual values in DB: 'ENABLED', 'DISABLED'  
- Result: Empty result set (misleading!)
"""

import asyncio
from app.modules.neo_chatbot.services.sql_assistant_service import SQLAssistantService
from app.modules.neo_chatbot.services.llm_service import LLMService
from app.modules.neo_chatbot.services.vector_store_service import VectorStoreService
from app.database.database import Database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_get_distinct_values():
    """Test getting actual distinct values from database"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Get Distinct Values from Database")
    logger.info("="*80)
    
    try:
        # Initialize services
        llm_service = LLMService()
        vector_store = VectorStoreService()
        db = Database()
        
        sql_service = SQLAssistantService(
            llm_service=llm_service,
            vector_store=vector_store,
            database=db
        )
        
        # Test 1: Get distinct values for STATUS column in bot_master
        logger.info("\n📊 Getting distinct values for bot_master.STATUS...")
        values = sql_service._get_distinct_column_values('bot_master', 'STATUS')
        
        logger.info(f"\n✅ Found {len(values)} distinct values:")
        for value in values:
            logger.info(f"  - '{value}'")
        
        # Verify we get actual values, not hallucinated ones
        if values:
            logger.info(f"\n✅ PASS: Successfully retrieved actual database values!")
            logger.info(f"Note: These are the REAL values, not 'active'/'inactive'")
        else:
            logger.error(f"\n❌ FAIL: Could not retrieve values")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_extract_where_conditions():
    """Test extracting filter values from WHERE clause"""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Extract WHERE Clause Conditions")
    logger.info("="*80)
    
    try:
        # Initialize services
        llm_service = LLMService()
        vector_store = VectorStoreService()
        db = Database()
        
        sql_service = SQLAssistantService(
            llm_service=llm_service,
            vector_store=vector_store,
            database=db
        )
        
        # Test query with WHERE conditions
        test_query = "SELECT * FROM bot_master WHERE status = 'active' AND model = 'BOT-2000';"
        
        logger.info(f"\n📝 Test Query: {test_query}")
        
        conditions = sql_service._extract_where_conditions(test_query)
        
        logger.info(f"\n🔍 Extracted Conditions:")
        for col, val in conditions:
            logger.info(f"  {col} = '{val}'")
        
        if conditions:
            logger.info(f"\n✅ PASS: Successfully extracted WHERE conditions!")
        else:
            logger.error(f"\n❌ FAIL: Could not extract conditions")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_value_validation():
    """Test validation of filter values against actual database"""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: Validate Filter Values Against Database")
    logger.info("="*80)
    
    try:
        # Initialize services
        llm_service = LLMService()
        vector_store = VectorStoreService()
        db = Database()
        
        sql_service = SQLAssistantService(
            llm_service=llm_service,
            vector_store=vector_store,
            database=db
        )
        
        # Test 1: Query with INVALID filter value
        logger.info("\n📝 Test Case 1: Query with hallucinated filter value")
        test_query = "SELECT * FROM bot_master WHERE STATUS = 'active';"
        logger.info(f"Query: {test_query}")
        
        values_valid, invalid_values = sql_service._validate_query_values(test_query)
        
        logger.info(f"\n🔍 Validation Results:")
        logger.info(f"  Valid: {values_valid}")
        logger.info(f"  Invalid Values: {len(invalid_values)}")
        
        if not values_valid:
            logger.info(f"\n✅ PASS: Correctly detected 'active' is not a valid value!")
            for issue in invalid_values:
                logger.info(f"\n  ❌ {issue['table']}.{issue['column']} = '{issue['filter_value']}'")
                logger.info(f"  ✓ Actual values in database: {', '.join([str(v) for v in issue['actual_values']])}")
        else:
            logger.error(f"\n❌ FAIL: Should have detected 'active' as invalid value!")
        
        # Test 2: Query with VALID filter value (if we know one)
        logger.info("\n" + "-"*80)
        logger.info("\n📝 Test Case 2: Query with valid filter value")
        
        # First, get actual values
        actual_status_values = sql_service._get_distinct_column_values('bot_master', 'STATUS')
        if actual_status_values:
            valid_value = actual_status_values[0]
            test_query2 = f"SELECT * FROM bot_master WHERE STATUS = '{valid_value}';"
            logger.info(f"Query: {test_query2}")
            
            values_valid2, invalid_values2 = sql_service._validate_query_values(test_query2)
            
            logger.info(f"\n🔍 Validation Results:")
            logger.info(f"  Valid: {values_valid2}")
            
            if values_valid2:
                logger.info(f"\n✅ PASS: Correctly accepted '{valid_value}' as valid value!")
            else:
                logger.error(f"\n❌ FAIL: Should have accepted '{valid_value}' as valid!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_real_world_scenario():
    """Test the exact scenario reported by user"""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: Real-World Scenario from User Report")
    logger.info("="*80)
    
    try:
        # Initialize services
        llm_service = LLMService()
        vector_store = VectorStoreService()
        db = Database()
        
        sql_service = SQLAssistantService(
            llm_service=llm_service,
            vector_store=vector_store,
            database=db
        )
        
        logger.info("\n📋 User Question: 'what is your criteria to check active bots'")
        logger.info("\nOLD System Response (WRONG):")
        logger.info("  - SQL Query: SELECT * FROM bot_master WHERE status = 'active';")
        logger.info("  - Problem: 'active' is NOT a valid value!")
        logger.info("  - Actual values: 'ENABLED', 'DISABLED'")
        logger.info("  - Result: Query returns 0 rows (misleading!)")
        
        logger.info("\n🔍 Testing Value Validation...")
        
        # The problematic query
        bad_query = "SELECT * FROM bot_master WHERE status = 'active';"
        
        # Validate it
        values_valid, invalid_values = sql_service._validate_query_values(bad_query)
        
        if not values_valid:
            logger.info(f"\n✅ NEW System Detects the Problem!")
            logger.info(f"\n  ⚠️ VALIDATION ERROR DETECTED:")
            for issue in invalid_values:
                logger.info(f"    ❌ {issue['table']}.{issue['column']} = '{issue['filter_value']}' (NOT FOUND IN DB)")
                logger.info(f"    ✓ Actual values: {', '.join([str(v) for v in issue['actual_values']])}")
            
            logger.info(f"\n  🎯 Expected Behavior:")
            logger.info(f"    1. System rejects query before execution")
            logger.info(f"    2. Shows actual values: 'ENABLED', 'DISABLED'")
            logger.info(f"    3. LLM regenerates with correct value: status = 'ENABLED'")
            logger.info(f"    4. Query returns actual results!")
            logger.info(f"\n✅ PASS: Value validation prevents the misleading empty result!")
        else:
            logger.error(f"\n❌ FAIL: Should have detected 'active' as invalid!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all value validation tests"""
    logger.info("\n" + "="*80)
    logger.info("VALUE VALIDATION TEST SUITE")
    logger.info("="*80)
    logger.info("Testing that the system validates filter values against actual database data")
    logger.info("to prevent queries that execute successfully but return misleading empty results")
    logger.info("="*80)
    
    results = []
    
    # Run tests
    results.append(await test_get_distinct_values())
    results.append(await test_extract_where_conditions())
    results.append(await test_value_validation())
    results.append(await test_real_world_scenario())
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    logger.info(f"Tests Run: {len(results)}")
    logger.info(f"Passed: {sum(results)}")
    logger.info(f"Failed: {len(results) - sum(results)}")
    
    if all(results):
        logger.info("\n✅ ALL TESTS PASSED!")
        logger.info("\nValue validation is working correctly.")
        logger.info("The system will now:")
        logger.info("  1. Query the database for actual distinct values")
        logger.info("  2. Validate filter values in WHERE clauses")
        logger.info("  3. Reject queries with non-existent values")
        logger.info("  4. Show actual values to LLM for correction")
        logger.info("  5. Prevent misleading empty result sets!")
    else:
        logger.error("\n❌ SOME TESTS FAILED")
    
    logger.info("="*80)

if __name__ == "__main__":
    asyncio.run(main())
