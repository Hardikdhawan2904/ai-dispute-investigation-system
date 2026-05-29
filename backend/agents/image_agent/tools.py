"""
Image Agent tools — atomic operations the agent graph can invoke.
"""
import base64
from pathlib import Path

from langchain_core.tools import tool

from utils.pii_masker import mask_case_details_for_llm
from utils.helpers import extract_json_from_text

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png"}


@tool
def validate_image_file(file_path: str) -> dict:
    """Check whether a file exists and is a supported image format."""
    path = Path(file_path)
    valid = path.exists() and path.suffix.lower() in SUPPORTED_EXTS
    return {"valid": valid, "reason": "" if valid else f"Missing or unsupported file: {file_path}"}


@tool
def load_and_encode_image(file_path: str) -> dict:
    """Read an image file and return its base64 encoding and MIME type."""
    path = Path(file_path)
    ext = path.suffix.lower()
    mime = "image/jpeg" if ext in {".jpg", ".jpeg"} else "image/png"
    with open(file_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return {"mime_type": mime, "image_b64": b64}


@tool
def mask_vision_case_details(case_details: dict) -> dict:
    """Mask PII from case details before sending to the vision LLM."""
    return mask_case_details_for_llm(case_details)


@tool
def parse_vision_json(raw_response: str) -> dict:
    """Parse structured JSON findings from a vision LLM response."""
    result = extract_json_from_text(raw_response)
    if not result:
        result = {"summary": raw_response[:500], "confidence_adjustment": 0.0, "matches_case": True}
    return result
