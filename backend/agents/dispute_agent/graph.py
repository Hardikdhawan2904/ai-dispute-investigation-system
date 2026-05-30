"""
Dispute Agent — ReAct (Reasoning + Acting) LangGraph.

Graph topology:
  prepare_input → agent ──[has tool calls]──► tools ──► agent  (loop)
                       └──[no tool calls]──► extract_final_case → END

  prepare_input     : builds the initial HumanMessage with all dispute context
  agent             : orchestrator LLM bound to all 5 tools; decides what to call
  tools             : ToolNode executes whichever tool the LLM requested
  extract_final_case: post-processes tool outputs → structured DisputeCase dict
"""
import os

from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_groq import ChatGroq

from agents.dispute_agent.state import DisputeAgentState
from agents.dispute_agent.nodes.prepare_input import prepare_input
from agents.dispute_agent.nodes.extract_final_case import extract_final_case
from agents.dispute_agent.tools import (
    validate_dispute_input,
    build_evidence_summary,
    run_dispute_analysis,
    clamp_score,
    calculate_priority,
)

# ── Tool registry (shown as edges in the graph) ────────────────────────────────

DISPUTE_TOOLS = [
    validate_dispute_input,
    build_evidence_summary,
    run_dispute_analysis,
    clamp_score,
    calculate_priority,
]

# ── Orchestrator LLM node ──────────────────────────────────────────────────────

def _make_orchestrator():
    llm = ChatGroq(
        model_name=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
        groq_api_key=os.getenv("GROQ_API_KEY"),
        temperature=0,
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", 2048)),
    )
    llm_with_tools = llm.bind_tools(DISPUTE_TOOLS)

    def agent_node(state: DisputeAgentState) -> dict:
        """Orchestrator: reads messages, decides which tool to call next."""
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    return agent_node


# ── Graph assembly ─────────────────────────────────────────────────────────────

def build_dispute_graph():
    g = StateGraph(DisputeAgentState)

    g.add_node("prepare_input",      prepare_input)
    g.add_node("agent",              _make_orchestrator())
    g.add_node("tools",              ToolNode(DISPUTE_TOOLS))
    g.add_node("extract_final_case", extract_final_case)

    g.set_entry_point("prepare_input")

    g.add_edge("prepare_input", "agent")

    # Conditional: if agent emitted tool_calls → execute them, else → finish
    g.add_conditional_edges(
        "agent",
        tools_condition,
        {
            "tools": "tools",
            END:     "extract_final_case",
        },
    )

    g.add_edge("tools",              "agent")           # tool results loop back to agent
    g.add_edge("extract_final_case", END)

    return g.compile()


dispute_graph = build_dispute_graph()
