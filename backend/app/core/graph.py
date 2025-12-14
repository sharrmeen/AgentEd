from langgraph.graph import StateGraph, END
from app.core.state import AgentEdState
from app.agents.planner import planner_agent_node
from app.core.router import route_supervisor
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