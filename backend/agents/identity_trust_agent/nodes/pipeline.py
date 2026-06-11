"""
Identity & Trust Intelligence Agent — Graph pipeline nodes.
"""
from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from groq import RateLimitError as GroqRateLimitError
from langchain_groq import ChatGroq
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_exponential

from agents.identity_trust_agent.config import get_llm_config, get_agent_tool_names, load_agent_config
from agents.identity_trust_agent.state import IdentityTrustAgentState
from agents.identity_trust_agent.tools import TOOL_REGISTRY, _active_case_id
from prompts.trust_prompts import SYSTEM_PROMPT, TRUST_DATA_TEMPLATE
from utils.helpers import extract_json_from_text, utc_now_iso, generate_case_id
from utils.logger import agent_logger, log_workflow_event
from utils.pii_masking import mask_name, mask_id, mask_free_text

# ── LLM + tools + agent identity (all sourced from agent.yaml) ───────────────
_cfg        = get_llm_config()
_agent_yaml = load_agent_config()["agent"]
_AGENT_NAME = _agent_yaml["name"]
_AGENT_VER  = str(_agent_yaml["version"])
_tools = [TOOL_REGISTRY[name] for name in get_agent_tool_names()]

_llm = ChatGroq(
    model_name=os.environ.get("LLM_MODEL") or _cfg["model"],
    temperature=_cfg["temperature"],
    max_tokens=int(os.environ.get("LLM_MAX_TOKENS") or _cfg["max_tokens"]),
    api_key=os.environ.get("GROQ_API_KEY"),
)


# ── Node 1 — validate ─────────────────────────────────────────────────────────

def validate_node(state: IdentityTrustAgentState) -> dict:
    d = state["dispute_input"]
    case_id = d.get("case_id") or d.get("_preset_case_id") or generate_case_id()
    return {"case_id": case_id, "agent_start_time": time.time()}


# ── Node 2 — build_context ────────────────────────────────────────────────────

def build_context_node(state: IdentityTrustAgentState) -> dict:
    """Run trust evaluation tools in parallel and format prompt context."""
    d = state["dispute_input"]
    case_id = state["case_id"]
    meta = d.get("transaction_metadata") or {}

    customer_id = d.get("customer_id", "")
    customer_name = d.get("customer_name", "")
    email = d.get("email", "")
    phone = d.get("phone", "")
    device_id = meta.get("device_id") or d.get("device_id") or ""
    location = meta.get("transaction_location") or d.get("location") or ""
    dispute_reason = d.get("dispute_reason", "")

    # Pre-run tools concurrently in parallel threads
    task_defs = {
        "verify_kyc_match": (
            TOOL_REGISTRY["verify_kyc_match"],
            {
                "customer_id": customer_id,
                "name": customer_name,
                "email": email,
                "phone": phone
            }
        ),
        "evaluate_device_fingerprint": (
            TOOL_REGISTRY["evaluate_device_fingerprint"],
            {
                "customer_id": customer_id,
                "device_id": device_id,
                "location": location
            }
        ),
        "analyze_behavioral_patterns": (
            TOOL_REGISTRY["analyze_behavioral_patterns"],
            {
                "customer_id": customer_id
            }
        )
    }

    def _run_one(name: str, tool_fn, args: dict) -> tuple:
        tok = _active_case_id.set(case_id)
        try:
            return name, tool_fn.invoke(args)
        except Exception as exc:
            return name, f"{name.upper()}\n  Error: Tool execution failed — {exc}"
        finally:
            _active_case_id.reset(tok)

    tool_results: dict = {}
    tools_used: list = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {
            ex.submit(_run_one, name, fn, args): name
            for name, (fn, args) in task_defs.items()
        }
        for fut in as_completed(futures):
            name, result = fut.result()
            tool_results[name] = result
            tools_used.append(name)

    # Build human message template with pre-computed tool sections
    _TOOL_ORDER = [
        "verify_kyc_match", "evaluate_device_fingerprint", "analyze_behavioral_patterns"
    ]
    tool_section = "\n\n## PRE-COMPUTED TOOL RESULTS\n(All tools executed — synthesise and produce JSON now)\n"
    for name in _TOOL_ORDER:
        if name in tool_results:
            tool_section += f"\n### {name}\n{tool_results[name]}\n"

    human_content = TRUST_DATA_TEMPLATE.format(
        customer_name    = mask_name(customer_name),
        customer_id      = mask_id(customer_id),
        email            = email,
        phone            = phone,
        device_id        = mask_id(device_id) if device_id else "Not provided",
        location         = location or "Not provided",
        dispute_reason   = dispute_reason,
        case_id          = mask_id(case_id),
        created_at       = utc_now_iso(),
    ) + tool_section

    return {
        "tool_results": tool_results,
        "tools_used":   tools_used,
        "messages": [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=human_content),
        ]
    }


# ── Node 3 — agent ────────────────────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(min=1, max=5),
    retry=retry_if_not_exception_type(GroqRateLimitError),
    reraise=True,
)
def call_model(state: IdentityTrustAgentState) -> dict:
    """Agent node — single LLM call to synthesize pre-computed inputs."""
    response = _llm.invoke(state["messages"])
    agent_logger.debug("ITIA LLM response received")
    return {"messages": [response]}


def should_continue(state: IdentityTrustAgentState) -> Literal["finalize"]:
    """Pre-computed pattern immediately routes to finalize."""
    return "finalize"


# ── Node 4 — finalize ─────────────────────────────────────────────────────────

def finalize_node(state: IdentityTrustAgentState) -> dict:
    """Parse output, perform server-side validations on trust and risk scores."""
    case_id = state["case_id"]
    d       = state["dispute_input"]

    start_time  = state.get("agent_start_time") or 0.0
    duration_ms = round((time.time() - start_time) * 1000, 1) if start_time else 0.0

    messages       = state.get("messages") or []
    tools_used     = list(state.get("tools_used") or [])
    llm_call_count = 1
    tool_msg_count = len(tools_used)

    metrics = {
        "total_duration_ms": duration_ms,
        "llm_calls":         llm_call_count,
        "tool_calls":        tool_msg_count,
        "retry_count":       0,
    }
    agent_metadata = {
        "name":        _AGENT_NAME,
        "version":     _AGENT_VER,
        "model":       _cfg["model"],
        "timestamp":   utc_now_iso(),
        "duration_ms": duration_ms,
    }

    # Parse JSON
    last = messages[-1] if messages else None
    raw  = last.content if last and hasattr(last, "content") else ""
    parsed = extract_json_from_text(raw) if raw else None

    if not parsed:
        agent_logger.warning("ITIA JSON parse failed — using fallback", extra={"case_id": case_id})
        parsed = _fallback_output(case_id, tools_used, agent_metadata, metrics)
        return {"final_output": parsed, "tools_used": tools_used, "agent_metadata": agent_metadata, "metrics": metrics}

    # Stamping server-owned fields
    parsed["case_id"]        = case_id
    parsed["tools_used"]     = tools_used
    parsed["agent_metadata"] = agent_metadata
    parsed["metrics"]        = metrics

    # ── Server-Side Trust & Risk Score Validations ──────────────────────────
    # Ensure trust_score and risk_score match our explicit scoring constraints.
    # LLMs can make arithmetic mistakes; we recalculate it deterministically.
    
    # Read tool outputs from state
    tool_results = state.get("tool_results") or {}
    kyc_report = str(tool_results.get("verify_kyc_match", ""))
    device_report = str(tool_results.get("evaluate_device_fingerprint", ""))
    behavior_report = str(tool_results.get("analyze_behavioral_patterns", ""))

    # Parse KYC match
    kyc_status = "VERIFIED"
    if "Verification     : FAILED" in kyc_report:
        kyc_status = "FAILED"
    elif "Verification     : SUSPICIOUS" in kyc_report:
        kyc_status = "SUSPICIOUS"

    # Parse Device Risk
    device_risk = "LOW"
    if "Device Risk          : HIGH" in device_report:
        device_risk = "HIGH"
    elif "Device Risk          : MEDIUM" in device_report:
        device_risk = "MEDIUM"

    # Parse Dispute Behavior
    friendly_fraud_risk = "LOW"
    if "Friendly Fraud Risk  : HIGH" in behavior_report:
        friendly_fraud_risk = "HIGH"
    elif "Friendly Fraud Risk  : MEDIUM" in behavior_report:
        friendly_fraud_risk = "MEDIUM"

    prior_disputes = 0
    if "Prior Disputes       : " in behavior_report:
        try:
            line = [ln for ln in behavior_report.split("\n") if "Prior Disputes" in ln][0]
            prior_disputes = int(line.split(":")[-1].strip())
        except Exception:
            pass

    velocity_breach = "Velocity Breach      : Yes" in behavior_report

    # Recalculate Trust Score
    trust = 1.0
    if kyc_status == "SUSPICIOUS":    trust -= 0.30
    elif kyc_status == "FAILED":      trust -= 0.70
    
    if device_risk == "MEDIUM":       trust -= 0.20
    elif device_risk == "HIGH":       trust -= 0.50
    
    if prior_disputes >= 3:           trust -= 0.10
    if friendly_fraud_risk == "HIGH" or velocity_breach: trust -= 0.20
    trust_score = round(max(0.00, min(1.00, trust)), 2)

    # Recalculate Risk Score
    risk = 0.0
    if prior_disputes >= 3:           risk += 0.20
    if velocity_breach:               risk += 0.30
    if friendly_fraud_risk == "HIGH": risk += 0.40
    if device_risk == "MEDIUM":       risk += 0.20
    if device_risk == "HIGH":         risk += 0.50
    if kyc_status == "SUSPICIOUS":    risk += 0.30
    if kyc_status == "FAILED":        risk += 0.70
    risk_score = round(max(0.00, min(1.00, risk)), 2)

    parsed["user_trust_score"] = trust_score
    parsed["behavioral_risk_score"] = risk_score
    parsed["identity_verification"] = kyc_status

    log_workflow_event(
        agent_logger,
        event="ITIA_TRUST_EVALUATION_COMPLETE",
        stage="identity_trust",
        case_id=case_id,
        customer_id=d.get("customer_id"),
        extra={
            "user_trust_score":      trust_score,
            "behavioral_risk_score": risk_score,
            "identity_verification": kyc_status,
            "duration_ms":           duration_ms
        }
    )

    return {
        "final_output": parsed,
        "tools_used":   tools_used,
        "agent_metadata": agent_metadata,
        "metrics":        metrics,
    }


def _fallback_output(
    case_id: str, tools_used: list, agent_metadata: dict, metrics: dict
) -> dict:
    """Minimal safe fallback returned if LLM fails or output cannot be parsed."""
    return {
        "case_id":                    case_id,
        "user_trust_score":           0.50,
        "behavioral_risk_score":      0.50,
        "identity_verification":      "SUSPICIOUS",
        "kyc_checks": {
            "name_match":             False,
            "contact_match":          False,
            "join_date":              "N/A"
        },
        "device_fingerprint": {
            "recognized_device":      False,
            "location_consistent":    False,
            "device_risk":            "MEDIUM"
        },
        "dispute_behavior": {
            "prior_dispute_count":    0,
            "velocity_breach_detected": False,
            "friendly_fraud_risk":    "MEDIUM"
        },
        "trust_reasoning": [
            "Trust evaluation failed — JSON parse error. Falling back to default risk settings."
        ],
        "trust_summary": "Trust brief generation failed. Standard safety review limits trust score.",
        "tools_used":                 tools_used,
        "agent_metadata":             agent_metadata,
        "metrics":                    metrics
    }
