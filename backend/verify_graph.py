from backend.app.agents.orchestration.graph import app  
test_input = {
    "user_query": "I need a study plan for next week", 
    "messages": [],
    "syllabus_topics": [],
    "student_profile": {}
}

print("🧪 STARTING TEST: Routing to Planner Agent...")
print("-" * 50)

try:
    result = app.invoke(test_input)
    print("-" * 50)
    print("✅ TEST COMPLETE")
    print(f"Final Route Taken: {result.get('next_step')}")
    print(f"Planner Output: {result.get('study_plan')}")
    print(f"System Messages: {result.get('messages')}")

except Exception as e:
    print(f"❌ TEST FAILED: {e}")