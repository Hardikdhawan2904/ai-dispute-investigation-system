"""
Post-processing node — runs after the agent loop ends.
Reads all ToolMessage outputs from state["messages"], extracts tool results
by name, and assembles the final structured DisputeCase dict.
"""
from langchain_core.messages import AIMessage, ToolMessage

from agents.dispute_agent.state import DisputeAgentState
from agents.dispute_agent.tools import calculate_priority, clamp_score
from utils.helpers import extract_json_from_text, utc_now_iso, generate_case_id
from utils.logger import agent_logger, log_workflow_event


def _collect_tool_outputs(messages: list) -> dict[str, str]:
    """Map tool_name → last output string by correlating ToolMessages with their tool_call_ids."""
    # Build tool_call_id → tool_name index from AIMessages
    call_id_to_name: dict[str, str] = {}
    for msg in messages:
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                call_id_to_name[tc["id"]] = tc["name"]

    # Collect ToolMessage content keyed by tool name
    outputs: dict[str, str] = {}
    for msg in messages:
        if isinstance(msg, ToolMessage):
            name = call_id_to_name.get(msg.tool_call_id) or getattr(msg, "name", None)
            if name:
                outputs[name] = msg.content  # last write wins if called >once

    return outputs


def _fallback_case(d: dict, case_id: str) -> dict:
    amount = float(d.get("amount", 0))
    fraud = bool(d.get("fraud_selected", False))
    priority = calculate_priority.invoke({"amount": amount, "fraud_suspicion": fraud, "risk_tags": []})
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
        "priority":                priority,
        "confidence_score":        0.1,
        "risk_tags":               ["HIGH_PRIORITY_CASE"] if fraud else [],
        "structured_reasoning":    "AI analysis could not be completed. Manual investigation required.",
        "status":                  "Dispute Raised",
        "workflow_ready":          True,
        "created_at":              utc_now_iso(),
    }


def extract_final_case(state: DisputeAgentState) -> dict:
    d = state["dispute_input"]
    tool_outputs = _collect_tool_outputs(state["messages"])

    # ── Case ID ────────────────────────────────────────────────────────────────
    case_id = (tool_outputs.get("validate_dispute_input") or "").strip()
    if not case_id:
        case_id = d.get("case_id") or generate_case_id()

    # ── Parse LLM analysis ─────────────────────────────────────────────────────
    raw_llm = tool_outputs.get("run_dispute_analysis", "")
    parsed = extract_json_from_text(raw_llm) if raw_llm else None

    if not parsed:
        agent_logger.warning("Failed to parse LLM JSON — using fallback", extra={"case_id": case_id})
        return {"final_case": _fallback_case(d, case_id), "case_id": case_id}

    # ── Inject guaranteed fields ───────────────────────────────────────────────
    parsed["case_id"]        = case_id
    parsed["customer_id"]    = d.get("customer_id", "")
    parsed["transaction_id"] = d.get("transaction_id", "")
    parsed.setdefault("status",         "Dispute Raised")
    parsed.setdefault("workflow_ready", True)
    parsed.setdefault("created_at",     utc_now_iso())

    # ── Confidence score — use tool output if available, else invoke tool ──────
    clamped_raw = tool_outputs.get("clamp_score", "")
    try:
        parsed["confidence_score"] = float(clamped_raw)
    except (ValueError, TypeError):
        parsed["confidence_score"] = clamp_score.invoke({
            "score": float(parsed.get("confidence_score", 0.5))
        })

    # ── Priority — use tool output if available, else invoke tool ─────────────
    valid_priorities = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
    if parsed.get("priority") not in valid_priorities:
        priority_raw = tool_outputs.get("calculate_priority", "")
        parsed["priority"] = (
            priority_raw if priority_raw in valid_priorities
            else calculate_priority.invoke({
                "amount":          float(d.get("amount", 0)),
                "fraud_suspicion": parsed.get("fraud_suspicion", False),
                "risk_tags":       parsed.get("risk_tags", []),
            })
        )

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
        },
    )

    return {"final_case": parsed, "case_id": case_id}
