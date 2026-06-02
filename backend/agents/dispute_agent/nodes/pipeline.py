"""
Agent 1 (ARIA) — ReAct pipeline nodes.

validate_node       : extract case_id from submission
build_evidence_node : format fraud-indicator checklist + document text,
                      then build the initial [SystemMessage, HumanMessage] to start the loop
call_model          : agent node — invoke LLM with 4 understanding tools bound
should_continue     : route to 'tools' if tool calls pending, else to 'finalize'
finalize_node       : parse the LLM's final JSON, stamp server-owned fields, return final_case
"""
from __future__ import annotations

import os
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from tenacity import retry, stop_after_attempt, wait_exponential

from agents.dispute_agent.config import get_llm_config, get_agent_tool_names
from agents.dispute_agent.state import DisputeAgentState
from agents.dispute_agent.tools import TOOL_REGISTRY
from prompts.dispute_prompts import SYSTEM_PROMPT, DISPUTE_DATA_TEMPLATE
from utils.helpers import extract_json_from_text, utc_now_iso, generate_case_id
from utils.logger import agent_logger, log_workflow_event

# ── LLM + tools (both sourced from agent.yaml) ────────────────────────────────
_cfg   = get_llm_config()
_tools = [TOOL_REGISTRY[name] for name in get_agent_tool_names()]

_llm = ChatGroq(
    model_name=_cfg["model"],
    temperature=_cfg["temperature"],
    max_tokens=_cfg["max_tokens"],
    api_key=os.environ.get("GROQ_API_KEY"),
)
_llm_with_tools = _llm.bind_tools(_tools)


# ── Node 1 — validate ─────────────────────────────────────────────────────────

def validate_node(state: DisputeAgentState) -> dict:
    d = state["dispute_input"]
    case_id = d.get("case_id") or d.get("_preset_case_id") or generate_case_id()
    return {"case_id": case_id}


# ── Node 2 — build_evidence ───────────────────────────────────────────────────

def build_evidence_node(state: DisputeAgentState) -> dict:
    """Format fraud checklist + document section, then build initial messages."""
    meta = state["dispute_input"].get("transaction_metadata") or {}
    d    = state["dispute_input"]

    def yn(val) -> str:
        if val is True:  return "Yes"
        if val is False: return "No"
        return str(val) if val else "Not provided"

    supporting_evidence = (
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

    doc_texts = state.get("document_texts") or []
    if doc_texts:
        parts = [t[:3000] + ("..." if len(t) > 3000 else "") for t in doc_texts if t.strip()]
        document_section = "\n\n".join(parts) if parts else "No documents attached."
    else:
        document_section = "No documents attached."

    # Build initial messages for the ReAct loop
    human_content = DISPUTE_DATA_TEMPLATE.format(
        customer_name    = d.get("customer_name", "N/A"),
        customer_id      = d.get("customer_id", "N/A"),
        transaction_type = d.get("transaction_type", "N/A"),
        merchant         = d.get("merchant", "N/A"),
        amount           = d.get("amount", 0),
        currency         = d.get("currency", "INR"),
        transaction_date = d.get("transaction_date", "N/A"),
        transaction_time = d.get("transaction_time", "N/A"),
        dispute_reason   = d.get("dispute_reason", "N/A"),
        fraud_selected   = d.get("fraud_selected", False),
        customer_comment = d.get("customer_comment", ""),
        supporting_evidence = supporting_evidence,
        document_section = document_section,
        case_id          = state["case_id"],
        created_at       = utc_now_iso(),
    )

    return {
        "supporting_evidence": supporting_evidence,
        "document_section":    document_section,
        "messages": [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=human_content),
        ],
    }


# ── Node 3 — agent (ReAct loop) ───────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def call_model(state: DisputeAgentState) -> dict:
    """Agent node — invoke LLM with all 4 understanding tools bound."""
    response = _llm_with_tools.invoke(state["messages"])
    agent_logger.debug(
        "ARIA LLM response received",
        extra={"tool_calls": len(getattr(response, "tool_calls", None) or [])},
    )
    return {"messages": [response]}


def should_continue(state: DisputeAgentState) -> Literal["tools", "finalize"]:
    """Conditional edge — tool calls pending → tools node, otherwise → finalize."""
    last: AIMessage = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return "finalize"


# ── Node 4 — finalize ─────────────────────────────────────────────────────────

def finalize_node(state: DisputeAgentState) -> dict:
    """Parse the LLM's final JSON, stamp server-owned fields, assemble final_case."""
    case_id = state["case_id"]
    d       = state["dispute_input"]

    last = state["messages"][-1]
    raw  = last.content if hasattr(last, "content") else ""
    parsed = extract_json_from_text(raw) if raw else None

    if not parsed:
        agent_logger.warning("ARIA JSON parse failed — using fallback", extra={"case_id": case_id})
        amount = float(d.get("amount", 0))
        fraud  = bool(d.get("fraud_selected", False))
        return {"final_case": _fallback_case(d, case_id, amount, fraud)}

    parsed["case_id"]        = case_id
    parsed["customer_id"]    = d.get("customer_id", "")
    parsed["transaction_id"] = d.get("transaction_id", "")
    parsed.setdefault("status",         "Dispute Raised")
    parsed.setdefault("workflow_ready", True)
    parsed.setdefault("created_at",     utc_now_iso())

    log_workflow_event(
        agent_logger,
        event="AGENT_ANALYSIS_COMPLETE",
        stage="dispute_understanding",
        case_id=case_id,
        customer_id=d.get("customer_id"),
        extra={
            "dispute_category": parsed.get("dispute_category"),
            "priority":         parsed.get("priority"),
            "confidence_score": parsed.get("confidence_score"),
            "fraud_suspicion":  parsed.get("fraud_suspicion"),
            "evidence_match":   parsed.get("evidence_match"),
        },
    )
    return {"final_case": parsed}


# ── Fallback ───────────────────────────────────────────────────────────────────

def _priority(amount: float, fraud: bool) -> str:
    if fraud and amount > 50_000: return "CRITICAL"
    if fraud or amount > 50_000:  return "HIGH"
    if amount > 10_000:           return "MEDIUM"
    return "LOW"


def _fallback_case(d: dict, case_id: str, amount: float, fraud: bool) -> dict:
    return {
        "case_id":                 case_id,
        "customer_id":             d.get("customer_id", ""),
        "transaction_id":          d.get("transaction_id", ""),
        "transaction_type":        d.get("transaction_type", ""),
        "merchant":                d.get("merchant", ""),
        "amount":                  amount,
        "currency":                d.get("currency", "INR"),
        "dispute_category":        "Other",
        "fraud_suspicion":         fraud,
        "customer_intent_summary": (
            "Automated analysis failed — manual review required. "
            f"Customer reported: {d.get('dispute_reason', 'N/A')}"
        ),
        "priority":                _priority(amount, fraud),
        "confidence_score":        0.1,
        "risk_tags":               ["HIGH_PRIORITY_CASE"] if fraud else [],
        "structured_reasoning":    "AI analysis could not be completed. Manual investigation required.",
        "evidence_match":          None,
        "evidence_match_note":     "",
        "status":                  "Dispute Raised",
        "workflow_ready":          True,
        "created_at":              utc_now_iso(),
    }
