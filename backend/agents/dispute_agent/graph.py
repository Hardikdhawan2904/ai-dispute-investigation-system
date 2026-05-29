from langgraph.graph import StateGraph, END

from agents.dispute_agent.state import DisputeAgentState
from agents.dispute_agent.nodes.validate_input import validate_input
from agents.dispute_agent.nodes.build_evidence import build_evidence
from agents.dispute_agent.nodes.run_llm import run_llm
from agents.dispute_agent.nodes.enrich_output import enrich_output


def build_dispute_graph():
    g = StateGraph(DisputeAgentState)

    g.add_node("validate_input", validate_input)
    g.add_node("build_evidence", build_evidence)
    g.add_node("run_llm",        run_llm)
    g.add_node("enrich_output",  enrich_output)

    g.set_entry_point("validate_input")
    g.add_edge("validate_input", "build_evidence")
    g.add_edge("build_evidence", "run_llm")
    g.add_edge("run_llm",        "enrich_output")
    g.add_edge("enrich_output",  END)

    return g.compile()


dispute_graph = build_dispute_graph()
