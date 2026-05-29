from pathlib import Path

from agents.image_agent.state import ImageAgentState
from agents.image_agent.tools import parse_vision_json
from utils.logger import agent_logger


def parse_findings(state: ImageAgentState) -> dict:
    if not state.get("raw_response"):
        return {"findings": None}

    findings = parse_vision_json.invoke({"raw_response": state["raw_response"]})

    agent_logger.info(
        "Image analysis complete",
        extra={
            "file":       Path(state["image_path"]).name,
            "doc_type":   findings.get("document_type"),
            "adjustment": findings.get("confidence_adjustment"),
        },
    )
    return {"findings": findings}
