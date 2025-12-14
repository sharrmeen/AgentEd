from app.core.state import AgentEdState

def route_supervisor(state: AgentEdState):
    query = state["user_query"].lower()
    
    # Rule 1: If they want to study/quiz -> Quiz Agent
    if "quiz" in query or "test" in query:
        return "quizzer"
    
    # Rule 2: If they ask about schedule -> Planner Agent
    if "plan" in query or "schedule" in query:
        return "planner"
        
    # Rule 3: If they ask "What is..." -> Content Agent
    if "explain" in query or "what is" in query:
        return "content"
        
    return "end"