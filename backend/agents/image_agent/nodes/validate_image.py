from agents.image_agent.state import ImageAgentState
from agents.image_agent.tools import validate_image_file


def validate_image(state: ImageAgentState) -> dict:
    result = validate_image_file.invoke({"file_path": state["image_path"]})
    if not result["valid"]:
        return {"error": result["reason"]}
    return {"error": None}
