from typing import List, Optional

from agents.dispute_agent.graph import dispute_graph
from agents.dispute_agent.state import DisputeAgentState


def run_dispute_agent(dispute_input: dict, document_texts: Optional[List[str]] = None) -> dict:
    """
    Entry point — run the full agentic dispute understanding pipeline.
    The orchestrator LLM calls tools (validate → evidence → analyse → clamp → priority)
    in a ReAct loop, then extract_final_case assembles the structured result.

    document_texts: extracted text from each uploaded file (OCR, PDF, XLSX, CSV).
    Returns the structured case dict ready for DB storage.
    """
    initial: DisputeAgentState = {
        "messages":      [],
        "dispute_input": dispute_input,
        "document_texts": document_texts or [],
        "case_id":       "",
        "final_case":    {},
        "error":         None,
    }
    result = dispute_graph.invoke(initial)
    return result["final_case"]
