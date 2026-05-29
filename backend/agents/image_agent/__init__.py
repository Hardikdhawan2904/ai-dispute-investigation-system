from typing import Optional

from agents.image_agent.graph import image_graph
from agents.image_agent.state import ImageAgentState


def run_image_agent(image_path: str, case_details: dict) -> Optional[dict]:
    """
    Entry point — run the full image analysis pipeline.
    Returns structured findings dict, or None if the file is invalid.
    """
    initial: ImageAgentState = {
        "image_path":        image_path,
        "case_details":      case_details,
        "mime_type":         "",
        "image_b64":         "",
        "safe_case_details": {},
        "raw_response":      "",
        "findings":          None,
        "error":             None,
    }
    result = image_graph.invoke(initial)
    return result.get("findings")
