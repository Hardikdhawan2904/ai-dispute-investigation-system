from typing import Optional

from agents.document_agent.graph import document_graph
from agents.document_agent.state import DocumentAgentState


def run_document_agent(file_path: str, case_details: dict) -> Optional[dict]:
    """
    Entry point — run the full document analysis pipeline.
    Returns structured findings dict, or None if the file is invalid/unreadable.
    """
    initial: DocumentAgentState = {
        "file_path":         file_path,
        "case_details":      case_details,
        "extracted_text":    "",
        "safe_case_details": {},
        "raw_response":      "",
        "findings":          None,
        "error":             None,
    }
    result = document_graph.invoke(initial)
    return result.get("findings")
