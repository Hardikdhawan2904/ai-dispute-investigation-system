from typing import Annotated, List, Optional, TypedDict

from langgraph.graph.message import add_messages


class DisputeAgentState(TypedDict):
    messages:            Annotated[list, add_messages]  # full ReAct tool-call / response history
    dispute_input:       dict        # raw submission fields
    document_texts:      List[str]   # OCR-extracted evidence files
    case_id:             str         # assigned before LLM call
    supporting_evidence: str         # formatted fraud-indicator checklist
    document_section:    str         # formatted document block passed to LLM
    final_case:          dict        # parsed + stamped output for DB
    error:               Optional[str]
