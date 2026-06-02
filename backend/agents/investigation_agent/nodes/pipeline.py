"""
Investigation Intelligence Agent — ReAct pipeline nodes.

call_model      : invoke LLM with all 5 tools bound (via TOOL_REGISTRY + agent.yaml)
should_continue : route to 'tools' if tool calls pending, else to 'finalize'
finalize_node   : parse the LLM's final JSON, extract tool_results from message history,
                  stamp server-owned fields, assemble final_output
"""
from __future__ import annotations

import os
from typing import Literal

from langchain_core.messages import AIMessage, ToolMessage
from langchain_groq import ChatGroq
from tenacity import retry, stop_after_attempt, wait_exponential

from agents.investigation_agent.config import get_llm_config, get_agent_tool_names
from agents.investigation_agent.state import InvestigationAgentState
from agents.investigation_agent.tools import TOOL_REGISTRY
from utils.helpers import extract_json_from_text, utc_now_iso
from utils.logger import agent_logger, log_workflow_event

# ── LLM + tools (both sourced from agent.yaml) ───────────────────────────────
_cfg   = get_llm_config()
_tools = [TOOL_REGISTRY[name] for name in get_agent_tool_names()]

_llm = ChatGroq(
    model_name=_cfg["model"],
    temperature=_cfg["temperature"],
    max_tokens=_cfg["max_tokens"],
    api_key=os.environ.get("GROQ_API_KEY"),
)
_llm_with_tools = _llm.bind_tools(_tools)


# ── Nodes ──────────────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def call_model(state: InvestigationAgentState) -> dict:
    """Agent node — invoke LLM with all 5 investigative tools bound."""
    response = _llm_with_tools.invoke(state["messages"])
    agent_logger.debug(
        "IIA LLM response received",
        extra={"tool_calls": len(getattr(response, "tool_calls", None) or [])},
    )
    return {"messages": [response]}


def should_continue(state: InvestigationAgentState) -> Literal["tools", "finalize"]:
    """Conditional edge — tool calls pending → tools node, otherwise → finalize."""
    last: AIMessage = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return "finalize"


def finalize_node(state: InvestigationAgentState) -> dict:
    """
    Parse the LLM's final JSON investigation plan.
    Extract tool_results from ToolMessages in the history for audit.
    Stamp server-owned fields and assemble final_output.
    """
    a1      = state["agent1_output"]
    case_id = a1.get("case_id", "")

    # ── Extract tool results from message history (audit trail) ───────────────
    tool_results: dict = {}
    for msg in state["messages"]:
        if isinstance(msg, ToolMessage) and getattr(msg, "name", None):
            tool_results[msg.name] = msg.content

    # ── Parse LLM final JSON ──────────────────────────────────────────────────
    last   = state["messages"][-1]
    raw    = last.content if hasattr(last, "content") else ""
    parsed = extract_json_from_text(raw) if raw else None

    if not parsed:
        agent_logger.warning(
            "IIA JSON parse failed — using fallback",
            extra={"case_id": case_id},
        )
        return {
            "final_output":  _fallback_output(a1, case_id),
            "tool_results":  tool_results,
        }

    # ── Stamp server-owned fields ─────────────────────────────────────────────
    parsed["case_id"]    = case_id
    parsed["created_at"] = utc_now_iso()

    log_workflow_event(
        agent_logger,
        event="IIA_INVESTIGATION_COMPLETE",
        stage="investigation_intelligence",
        case_id=case_id,
        customer_id=a1.get("customer_id"),
        extra={
            "recommended_queue":        parsed.get("recommended_queue"),
            "investigation_complexity": parsed.get("investigation_complexity"),
            "manual_review_required":   parsed.get("manual_review_required"),
            "duplicate_found":          parsed.get("duplicate_found"),
            "confidence_score":         parsed.get("confidence_score"),
            "tools_called":             list(tool_results.keys()),
        },
    )

    return {
        "final_output": parsed,
        "tool_results": tool_results,
    }


# ── Fallback ───────────────────────────────────────────────────────────────────

def _fallback_output(a1: dict, case_id: str) -> dict:
    """Minimal safe investigation plan returned when JSON parsing fails."""
    fraud   = a1.get("fraud_suspicion", False)
    amount  = float(a1.get("amount", 0))
    cat     = a1.get("dispute_category", "Other")

    if fraud and amount > 50_000:
        queue      = "CRITICAL_QUEUE"
        complexity = "CRITICAL"
    elif fraud:
        queue      = "FRAUD_QUEUE"
        complexity = "HIGH"
    elif amount > 50_000:
        queue      = "HIGH_VALUE_QUEUE"
        complexity = "HIGH"
    elif cat in ("Merchant Dispute", "Refund Not Received", "Product Not Received", "Subscription Abuse"):
        queue      = "MERCHANT_QUEUE"
        complexity = "MEDIUM"
    elif cat == "ATM Cash Issue":
        queue      = "ATM_QUEUE"
        complexity = "MEDIUM"
    else:
        queue      = "STANDARD_QUEUE"
        complexity = "MEDIUM"

    return {
        "case_id":                  case_id,
        "recommended_queue":        queue,
        "investigation_complexity": complexity,
        "manual_review_required":   True,
        "customer_risk_profile":    {"risk_level": "UNKNOWN", "assessment": "Tool execution failed"},
        "merchant_risk_profile":    {"merchant_risk": "UNKNOWN", "assessment": "Tool execution failed"},
        "duplicate_found":          False,
        "related_case_id":          None,
        "related_cases":            {"similar_cases": 0, "resolution_rate": 0.0},
        "required_documents":       ["Bank statement (last 3 months)", "Supporting documentation"],
        "recommended_steps":        [
            "Manual review required — automated investigation failed",
            "Gather all available evidence from customer",
            "Escalate to senior analyst",
        ],
        "investigation_summary":    (
            "Automated investigation could not be completed. "
            "Manual review has been flagged. Senior analyst should conduct full investigation."
        ),
        "confidence_score":         0.1,
        "created_at":               utc_now_iso(),
    }
