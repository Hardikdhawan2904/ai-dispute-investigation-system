from typing import TypedDict, Optional


class ImageAgentState(TypedDict):
    # ── Input ───────────────────────────────────────────────────────────────────
    image_path: str
    case_details: dict

    # ── Derived in load_image ──────────────────────────────────────────────────
    mime_type: str
    image_b64: str
    safe_case_details: dict

    # ── Derived in run_vision ──────────────────────────────────────────────────
    raw_response: str

    # ── Derived in parse_findings ──────────────────────────────────────────────
    findings: Optional[dict]

    # ── Error channel ──────────────────────────────────────────────────────────
    error: Optional[str]
