"""
All dispute agent capabilities exposed as @tool functions.
The orchestrator LLM calls these in sequence via .bind_tools() / ToolNode.

Tool execution order:
  1. validate_dispute_input   → case_id
  2. build_evidence_summary   → supporting_evidence string
  3. run_dispute_analysis     → raw LLM JSON (dispute classification)
  4. clamp_score              → validated confidence_score
  5. calculate_priority       → priority (only if LLM omitted or gave invalid value)
"""
import json
import os
import time
from typing import List

from langchain_core.tools import tool

from utils.helpers import determine_priority, generate_case_id, utc_now_iso
from utils.logger import agent_logger


# ── Tool 1: Input validation ───────────────────────────────────────────────────

@tool
def validate_dispute_input(customer_id: str, existing_case_id: str = "") -> str:
    """Validate the dispute submission and return a case ID.
    Pass existing_case_id if one was pre-generated; otherwise leave empty to auto-generate.
    Returns the case ID string to use for all subsequent tool calls."""
    return existing_case_id.strip() if existing_case_id.strip() else generate_case_id()


# ── Tool 2: Evidence builder ───────────────────────────────────────────────────

@tool
def build_evidence_summary(metadata_json: str) -> str:
    """Build a formatted evidence summary from the transaction metadata.
    Pass the transaction_metadata field as a JSON string.
    Returns a formatted multi-line evidence string for the dispute analysis prompt."""
    try:
        meta = json.loads(metadata_json)
    except Exception:
        meta = {}

    def yn(val) -> str:
        if val is True:  return "Yes"
        if val is False: return "No"
        return str(val) if val else "Not provided"

    return (
        f"  OTP Received (for this txn)  : {yn(meta.get('otp_received'))}\n"
        f"  Card / Account Blocked       : {yn(meta.get('card_blocked'))}\n"
        f"  Bank Already Contacted       : {yn(meta.get('bank_contacted'))}\n"
        f"  Transaction Location         : {meta.get('transaction_location') or 'Not provided'}\n"
        f"  OTP Shared with 3rd Party    : {yn(meta.get('otp_shared'))}\n"
        f"  Bank Impersonation Call      : {yn(meta.get('bank_impersonation'))}\n"
        f"  Remote Access App Installed  : {yn(meta.get('remote_access'))}\n"
        f"  Phishing Link Clicked        : {yn(meta.get('phishing_link'))}\n"
        f"  SIM Swap Suspected           : {yn(meta.get('sim_swap_suspected'))}\n"
        f"  Device Lost / Stolen         : {yn(meta.get('device_lost'))}\n"
        f"  Card Lost / Stolen           : {yn(meta.get('card_lost'))}\n"
        f"  Unknown Beneficiary Added    : {yn(meta.get('unknown_beneficiary'))}\n"
        f"  UPI Collect Fraud            : {yn(meta.get('upi_collect_fraud'))}\n"
        f"  Steps Already Taken          : {meta.get('fraud_additional_details') or 'None stated'}\n"
    )


# ── Tool 3: Core dispute analysis (calls Groq internally) ─────────────────────

@tool
def run_dispute_analysis(
    case_id: str,
    dispute_input_json: str,
    supporting_evidence: str,
    document_section: str,
) -> str:
    """Analyze the dispute using the AI model. Call AFTER validate_dispute_input and build_evidence_summary.
    - case_id: value returned by validate_dispute_input
    - dispute_input_json: JSON string containing customer_name, customer_id, transaction_type,
      merchant, amount, currency, transaction_date, transaction_time, dispute_reason,
      fraud_selected, customer_comment
    - supporting_evidence: value returned by build_evidence_summary
    - document_section: formatted text from uploaded documents (pass as provided in the initial context)
    Returns structured JSON with dispute category, fraud assessment, priority, risk tags, and reasoning."""
    from langchain_groq import ChatGroq
    from langchain_core.messages import SystemMessage, HumanMessage
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    from prompts.dispute_prompts import SYSTEM_PROMPT, DISPUTE_ANALYSIS_PROMPT

    try:
        d = json.loads(dispute_input_json)
    except Exception:
        d = {}

    llm = ChatGroq(
        model_name=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
        groq_api_key=os.getenv("GROQ_API_KEY"),
        temperature=0,
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", 2048)),
    )

    prompt_text = DISPUTE_ANALYSIS_PROMPT.format(
        customer_name=d.get("customer_name", "Unknown"),
        customer_id=d.get("customer_id", ""),
        transaction_type=d.get("transaction_type", ""),
        merchant=d.get("merchant", ""),
        amount=d.get("amount", 0),
        currency=d.get("currency", "INR"),
        transaction_date=d.get("transaction_date", ""),
        transaction_time=d.get("transaction_time", ""),
        dispute_reason=d.get("dispute_reason", ""),
        fraud_selected=d.get("fraud_selected", False),
        customer_comment=d.get("customer_comment", ""),
        supporting_evidence=supporting_evidence,
        document_section=document_section,
        case_id=case_id,
        created_at=utc_now_iso(),
    )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def _call():
        return llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt_text),
        ]).content

    start = time.time()
    result = _call()
    agent_logger.info(
        f"LLM responded in {(time.time() - start) * 1000:.0f}ms",
        extra={"agent": "dispute_understanding", "case_id": case_id},
    )
    return result


# ── Tool 4: Confidence score clamping ─────────────────────────────────────────

@tool
def clamp_score(score: float) -> float:
    """Clamp a confidence score to the valid [0.0, 1.0] range.
    Pass the confidence_score value from the run_dispute_analysis JSON result."""
    return max(0.0, min(1.0, score))


# ── Tool 5: Priority calculation ──────────────────────────────────────────────

@tool
def calculate_priority(amount: float, fraud_suspicion: bool, risk_tags: List[str]) -> str:
    """Determine case priority from amount and fraud indicators.
    Call this only if the priority in run_dispute_analysis output is missing or not one of CRITICAL/HIGH/MEDIUM/LOW.
    Returns one of: CRITICAL, HIGH, MEDIUM, LOW."""
    return determine_priority(amount, fraud_suspicion, risk_tags)
