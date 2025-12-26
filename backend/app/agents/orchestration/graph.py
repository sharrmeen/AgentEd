from langgraph.graph import StateGraph, END
from backend.app.agents.orchestration.state import AgentEdState
from backend.app.agents.planner_agent import planner_agent_node
from backend.app.agents.orchestration.router import route_supervisor
# import future nodes...

# initialize
workflow = StateGraph(AgentEdState)

# add Nodes
workflow.add_node("planner", planner_agent_node)
# workflow.add_node("quizzer", quiz_node) ...

# define the Router (Conditional Edge)
# "start" is a dummy node or just the entry point logic
workflow.set_conditional_entry_point(
    route_supervisor,
    {
        "planner": "planner",
        # "quizzer": "quizzer",
        # "content": "content",
        "end": END
    }
)

app = workflow.compile()