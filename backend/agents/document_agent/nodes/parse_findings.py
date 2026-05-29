from pathlib import Path

from agents.document_agent.state import DocumentAgentState
from agents.document_agent.tools import parse_document_json
from utils.logger import agent_logger


def parse_findings(state: DocumentAgentState) -> dict:
    if not state.get("raw_response"):
        return {"findings": None}

    findings = parse_document_json.invoke({"raw_response": state["raw_response"]})

    agent_logger.info(
        "Document analysis complete",
        extra={
            "file":       Path(state["file_path"]).name,
            "doc_type":   findings.get("document_type"),
            "adjustment": findings.get("confidence_adjustment"),
        },
    )
    return {"findings": findings}
