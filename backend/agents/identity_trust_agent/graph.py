"""
Identity & Trust Intelligence Agent graph assembly.
"""
from langgraph.graph import StateGraph, END

from agents.identity_trust_agent.state import IdentityTrustAgentState
from agents.identity_trust_agent.nodes.pipeline import (
    validate_node,
    build_context_node,
    call_model,
    finalize_node,
)


def build_identity_trust_graph():
    g = StateGraph(IdentityTrustAgentState)

    # Register nodes
    g.add_node("validate",      validate_node)
    g.add_node("build_context", build_context_node)
    g.add_node("agent",         call_model)
    g.add_node("finalize",      finalize_node)

    # Entry point
    g.set_entry_point("validate")

    # Linear pre-computed flow
    g.add_edge("validate",      "build_context")
    g.add_edge("build_context", "agent")
    g.add_edge("agent",         "finalize")
    g.add_edge("finalize",      END)

    return g.compile()


identity_trust_graph = build_identity_trust_graph()
