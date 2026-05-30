from typing import TypedDict, Optional, List, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class DisputeAgentState(TypedDict):
    # Message channel — orchestrator LLM reads/writes here each turn
    messages: Annotated[List[BaseMessage], add_messages]

    # Passed in at invocation time
    dispute_input: dict
    document_texts: List[str]

    # Populated by extract_final_case after the agent loop finishes
    case_id: str
    final_case: dict
    error: Optional[str]
