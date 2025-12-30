from langgraph.graph import StateGraph, END
from backend.app.agents.orchestration.state import AgentEdState
from backend.app.agents.planner_agent import planner_agent_node
from backend.app.agents.quiz_agent import quiz_agent_node
from backend.app.agents.resource_agent import resource_agent_node
from backend.app.agents.feedback_agent import feedback_agent_node
from backend.app.agents.orchestration.router import (
    route_supervisor, route_from_study_plan, route_from_content, route_from_quiz
)

# initialize
workflow = StateGraph(AgentEdState)

# add Nodes
workflow.add_node("study_plan", planner_agent_node)
workflow.add_node("quiz", quiz_agent_node)
workflow.add_node("content", resource_agent_node)
workflow.add_node("feedback", feedback_agent_node)

# define the Router (Conditional Entry Point)
workflow.set_conditional_entry_point(
    route_supervisor,
    {
        "study_plan": "study_plan",
        "quiz": "quiz",
        "content": "content",
        "feedback": "feedback",
        "__end__": END
    }
)

# define routes after each agent
workflow.add_conditional_edges(
    "study_plan",
    route_from_study_plan,
    {
        "content": "content",
        "quiz": "quiz",
        "__end__": END
    }
)

workflow.add_conditional_edges(
    "content",
    route_from_content,
    {
        "quiz": "quiz",
        "study_plan": "study_plan",
        "__end__": END
    }
)

workflow.add_conditional_edges(
    "quiz",
    route_from_quiz,
    {
        "feedback": "feedback",
        "__end__": END
    }
)

# feedback always ends
workflow.add_edge("feedback", END)

app = workflow.compile()