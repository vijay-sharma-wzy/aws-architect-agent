"""
LangGraph StateGraph definition for the AWS Architecture Agent.

Graph topology:
  START → architect → tool_node → critic → explainer → END
                ↑          (revise)  ↓
                └──────────────────┘
"""

from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, START, END

from arch_agent.state import ArchState
from arch_agent.nodes import architect, critic, explainer, tool_node

MAX_REVISIONS = 2


### Conditional edge functions

def route_architect(state: ArchState) -> str:
    """After architect runs: if it made tool calls, go to tool_node. Else END."""
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tool_node"
    return END


def route_critic(state: ArchState) -> str:
    """After critic runs: approve → explainer, revise → architect (with cap)."""
    revision_count = state.get("revision_count", 0)

    if revision_count >= MAX_REVISIONS:
        return "explainer"

    critique = state.get("critique", "")
    if critique.startswith("APPROVED"):
        return "explainer"

    return "architect"


### Graph wiring

def build_graph():
    graph = StateGraph(ArchState)

    graph.add_node("architect", architect)
    graph.add_node("tool_node", tool_node)
    graph.add_node("critic", critic)
    graph.add_node("explainer", explainer)

    graph.add_edge(START, "architect")

    graph.add_conditional_edges(
        "architect",
        route_architect,
        {"tool_node": "tool_node", END: END},
    )

    graph.add_edge("tool_node", "critic")

    graph.add_conditional_edges(
        "critic",
        route_critic,
        {"explainer": "explainer", "architect": "architect"},
    )

    graph.add_edge("explainer", END)

    return graph.compile()


app = build_graph()
