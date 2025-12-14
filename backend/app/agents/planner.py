from app.core.state import AgentEdState
from langchain_core.messages import SystemMessage, HumanMessage
#assume llm

def planner_agent_node(state: AgentEdState):
    print("--- 📅 PLANNER AGENT: Working... ---")
    
    #Get Data from State
    topics = state.get("syllabus_topics", [])
    profile = state.get("student_profile", {})
    
    # Construct Prompt
    system_prompt = f"""
    You are an academic planner. 
    The student is weak in: {profile.get('weak_topics', 'None')}.
    Create a study plan for these topics: {topics}.
    Prioritize the weak topics. Output strictly valid JSON.
    """
    
    # todo:call llm
    # response = llm.invoke([SystemMessage(content=system_prompt)])
    # new_plan = parse_json(response.content)
    
    #mock responses
    new_plan = {
        "Monday": "Linear Algebra (Weakness)", 
        "Tuesday": "Calculus"
    }
    
    #update state
    return {
        "study_plan": new_plan,
        "messages": ["I have updated your plan to focus on Linear Algebra."],
        "next_step": "end"
    }