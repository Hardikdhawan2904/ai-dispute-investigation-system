from agents.image_agent.state import ImageAgentState
from agents.image_agent.tools import load_and_encode_image, mask_vision_case_details


def load_image(state: ImageAgentState) -> dict:
    encoded = load_and_encode_image.invoke({"file_path": state["image_path"]})
    safe    = mask_vision_case_details.invoke({"case_details": state["case_details"]})
    return {
        "mime_type":         encoded["mime_type"],
        "image_b64":         encoded["image_b64"],
        "safe_case_details": safe,
    }
