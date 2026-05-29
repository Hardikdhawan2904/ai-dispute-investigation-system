from agents.document_agent.state import DocumentAgentState
from agents.document_agent.tools import extract_document_text, mask_document_case_details
from utils.logger import agent_logger


def extract_text(state: DocumentAgentState) -> dict:
    text = extract_document_text.invoke({"file_path": state["file_path"]})
    safe = mask_document_case_details.invoke({"case_details": state["case_details"]})

    if not text.strip():
        agent_logger.warning(f"No text extracted from {state['file_path']}")
        return {"extracted_text": "", "safe_case_details": safe, "error": "No readable text found in document"}

    return {"extracted_text": text, "safe_case_details": safe}
