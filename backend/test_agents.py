"""
Comprehensive test suite for all agents and workflow.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.planner_agent import study_plan_node
from app.agents.resource_agent import resource_agent_node
from app.agents.quiz_agent import quiz_agent_node
from app.agents.feedback_agent import feedback_agent_node
from app.agents.orchestration.state import AgentEdState
from app.agents.orchestration.workflow import run_workflow
from dotenv import load_dotenv


# ============================================================
# TEST 1: PLANNER AGENT
# ============================================================

async def test_planner_agent():
    """Test Planner Agent"""
    print("\n" + "="*60)
    print("TEST 1: PLANNER AGENT")
    print("="*60)
    
    try:
        state = AgentEdState(
            user_id="507f1f77bcf86cd799439011",
            user_query="Create a 30-day study plan",
            subject_id="507f1f77bcf86cd799439012",
            constraints={"target_days": 30, "daily_hours": 2.0}
        )
        
        result = await study_plan_node(state)
        
        # Validation checks
        assert result is not None, "Result is None"
        assert "messages" in result, "Missing 'messages' field"
        assert isinstance(result["messages"], list), "messages should be a list"
        assert len(result["messages"]) > 0, "messages list is empty"
        
        print("PLANNER AGENT PASSED")
        print(f"   Response: {result['messages'][0][:150]}...")
        return True
        
    except Exception as e:
        print(f"PLANNER AGENT FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# TEST 2: RESOURCE AGENT
# ============================================================

async def test_resource_agent():
    """Test Resource Agent"""
    print("\n" + "="*60)
    print("TEST 2: RESOURCE AGENT")
    print("="*60)
    
    try:
        state = AgentEdState(
            user_id="507f1f77bcf86cd799439011",
            user_query="What is photosynthesis?",
            subject_id="507f1f77bcf86cd799439012",
            session_id="507f1f77bcf86cd799439013"
        )
        
        result = await resource_agent_node(state)
        
        # Validation checks
        assert result is not None, "Result is None"
        assert "messages" in result, "Missing 'messages' field"
        assert isinstance(result["messages"], list), "messages should be a list"
        assert len(result["messages"]) > 0, "messages list is empty"
        
        print("RESOURCE AGENT PASSED")
        print(f"   Response: {result['messages'][0][:150]}...")
        return True
        
    except Exception as e:
        print(f"RESOURCE AGENT FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# TEST 3: QUIZ AGENT
# ============================================================

async def test_quiz_agent():
    """Test Quiz Agent"""
    print("\n" + "="*60)
    print("TEST 3: QUIZ AGENT")
    print("="*60)
    
    try:
        state = AgentEdState(
            user_id="507f1f77bcf86cd799439011",
            user_query="Create a quiz on chapter 1",
            subject_id="507f1f77bcf86cd799439012",
            chapter_number=1
        )
        
        result = await quiz_agent_node(state)
        
        # Validation checks
        assert result is not None, "Result is None"
        assert isinstance(result, dict), "Result should be a dictionary"
        
        # Check for quiz or messages
        has_quiz = "quiz" in result
        has_messages = "messages" in result
        assert has_quiz or has_messages, "Missing both 'quiz' and 'messages' fields"
        
        print("✅ QUIZ AGENT PASSED")
        if has_quiz:
            print(f"   Quiz generated with {len(result.get('quiz', []))} questions")
        if has_messages:
            print(f"   Response: {result['messages'][0][:150]}...")
        return True
        
    except Exception as e:
        print(f"❌ QUIZ AGENT FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# TEST 4: FEEDBACK AGENT
# ============================================================

async def test_feedback_agent():
    """Test Feedback Agent"""
    print("\n" + "="*60)
    print("TEST 4: FEEDBACK AGENT")
    print("="*60)
    
    try:
        state = AgentEdState(
            user_id="507f1f77bcf86cd799439011",
            user_query="Show my quiz results",
            subject_id="507f1f77bcf86cd799439012",
            quiz=[
                {"question_text": "Q1", "correct_answer": "A"},
                {"question_text": "Q2", "correct_answer": "B"}
            ],
            quiz_results={"q1": "A", "q2": "B"}
        )
        
        result = await feedback_agent_node(state)
        
        # Validation checks
        assert result is not None, "Result is None"
        assert isinstance(result, dict), "Result should be a dictionary"
        
        # Check for feedback or messages
        has_feedback = "feedback" in result
        has_messages = "messages" in result
        assert has_feedback or has_messages, "Missing both 'feedback' and 'messages' fields"
        
        print("✅ FEEDBACK AGENT PASSED")
        if has_messages:
            print(f"   Response: {result['messages'][0][:150]}...")
        return True
        
    except Exception as e:
        print(f"❌ FEEDBACK AGENT FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# TEST 5: FULL WORKFLOW
# ============================================================

async def test_full_workflow():
    """Test Full Workflow"""
    print("\n" + "="*60)
    print("TEST 5: FULL WORKFLOW")
    print("="*60)
    
    try:
        result = await run_workflow(
            user_id="507f1f77bcf86cd799439011",
            user_query="Create a 30-day study plan",
            subject_id="507f1f77bcf86cd799439012",
            constraints={"target_days": 30, "daily_hours": 2.0}
        )
        
        # Validation checks
        assert result is not None, "Result is None"
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "messages" in result, "Missing 'messages' field"
        assert "workflow_complete" in result, "Missing 'workflow_complete' field"
        assert "agent_trace" in result, "Missing 'agent_trace' field"
        
        print("✅ FULL WORKFLOW PASSED")
        print(f"   Messages: {len(result['messages'])} items")
        print(f"   Workflow Complete: {result['workflow_complete']}")
        print(f"   Agent Trace: {result['agent_trace']}")
        return True
        
    except Exception as e:
        print(f"❌ FULL WORKFLOW FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# MAIN TEST RUNNER
# ============================================================

async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("AGENTED AGENT TEST SUITE")
    print("="*60)
    
    results = {
        "Planner Agent": await test_planner_agent(),
        "Resource Agent": await test_resource_agent(),
        "Quiz Agent": await test_quiz_agent(),
        "Feedback Agent": await test_feedback_agent(),
        "Full Workflow": await test_full_workflow(),
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    return passed == total


if __name__ == "__main__":
    load_dotenv()
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
    
