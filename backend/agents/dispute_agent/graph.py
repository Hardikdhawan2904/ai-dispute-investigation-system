"""
Dispute Agent graph — ReAct (agent-tools loop) pattern.

  agent ──(tool calls?)──► tools ──► agent   (loop)
  agent ──(no tool calls)─► finalize ──► END
"""
from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from agents.dispute_agent.state import DisputeAgentState
from agents.dispute_agent.tools import TOOLS
from agents.dispute_agent.nodes.pipeline import call_model, should_continue, finalize_node


def build_dispute_graph():
    g = StateGraph(DisputeAgentState)

    g.add_node("agent",    call_model)
    g.add_node("tools",    ToolNode(TOOLS))
    g.add_node("finalize", finalize_node)

    g.set_entry_point("agent")

    g.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "finalize": "finalize"},
    )
    g.add_edge("tools",    "agent")
    g.add_edge("finalize", END)

    return g.compile()


dispute_graph = build_dispute_graph()
