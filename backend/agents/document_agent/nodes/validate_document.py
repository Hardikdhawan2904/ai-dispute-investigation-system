from agents.document_agent.state import DocumentAgentState
from agents.document_agent.tools import validate_document_file


def validate_document(state: DocumentAgentState) -> dict:
    result = validate_document_file.invoke({"file_path": state["file_path"]})
    if not result["valid"]:
        return {"error": result["reason"]}
    return {"error": None}
