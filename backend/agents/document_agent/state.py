from typing import TypedDict, Optional


class DocumentAgentState(TypedDict):
    # ── Input ───────────────────────────────────────────────────────────────────
    file_path: str
    case_details: dict

    # ── Derived in extract_text ────────────────────────────────────────────────
    extracted_text: str
    safe_case_details: dict

    # ── Derived in run_llm ─────────────────────────────────────────────────────
    raw_response: str

    # ── Derived in parse_findings ──────────────────────────────────────────────
    findings: Optional[dict]

    # ── Error channel ──────────────────────────────────────────────────────────
    error: Optional[str]
