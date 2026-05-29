from langgraph.graph import StateGraph, END

from agents.document_agent.state import DocumentAgentState
from agents.document_agent.nodes.validate_document import validate_document
from agents.document_agent.nodes.extract_text import extract_text
from agents.document_agent.nodes.run_llm import run_llm
from agents.document_agent.nodes.parse_findings import parse_findings


def _route_after_validate(state: DocumentAgentState) -> str:
    return "end" if state.get("error") else "extract_text"


def _route_after_extract(state: DocumentAgentState) -> str:
    return "end" if state.get("error") else "run_llm"


def build_document_graph():
    g = StateGraph(DocumentAgentState)

    g.add_node("validate_document", validate_document)
    g.add_node("extract_text",      extract_text)
    g.add_node("run_llm",           run_llm)
    g.add_node("parse_findings",    parse_findings)

    g.set_entry_point("validate_document")
    g.add_conditional_edges(
        "validate_document",
        _route_after_validate,
        {"extract_text": "extract_text", "end": END},
    )
    g.add_conditional_edges(
        "extract_text",
        _route_after_extract,
        {"run_llm": "run_llm", "end": END},
    )
    g.add_edge("run_llm",        "parse_findings")
    g.add_edge("parse_findings", END)

    return g.compile()


document_graph = build_document_graph()
