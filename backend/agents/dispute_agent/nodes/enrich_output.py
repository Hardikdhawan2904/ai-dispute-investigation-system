from agents.dispute_agent.state import DisputeAgentState
from agents.dispute_agent.tools import calculate_priority, clamp_score
from utils.helpers import extract_json_from_text, utc_now_iso, determine_priority
from utils.logger import agent_logger, log_workflow_event


def _fallback(dispute_input: dict, case_id: str, reason: str) -> dict:
    amount = float(dispute_input.get("amount", 0))
    fraud = dispute_input.get("fraud_selected", False)
    return {
        "case_id":                case_id,
        "customer_id":            dispute_input.get("customer_id", ""),
        "transaction_id":         dispute_input.get("transaction_id", ""),
        "transaction_type":       dispute_input.get("transaction_type", ""),
        "merchant":               dispute_input.get("merchant", ""),
        "amount":                 amount,
        "currency":               dispute_input.get("currency", "INR"),
        "dispute_category":       "Other",
        "fraud_suspicion":        fraud,
        "customer_intent_summary": (
            f"Automated analysis failed — manual review required. "
            f"Customer reported: {dispute_input.get('dispute_reason', 'N/A')}"
        ),
        "priority":               determine_priority(amount, fraud, []),
        "confidence_score":       0.1,
        "risk_tags":              ["HIGH_PRIORITY_CASE"] if fraud else [],
        "structured_reasoning":   f"AI analysis could not be completed: {reason}. Manual investigation required.",
        "status":                 "Dispute Raised",
        "workflow_ready":         True,
        "created_at":             utc_now_iso(),
    }


def enrich_output(state: DisputeAgentState) -> dict:
    d = state["dispute_input"]
    case_id = state["case_id"]

    if state.get("error") or not state.get("raw_llm_response"):
        return {"final_case": _fallback(d, case_id, state.get("error") or "LLM returned empty response")}

    parsed = extract_json_from_text(state["raw_llm_response"])
    if not parsed:
        agent_logger.warning("Failed to parse LLM JSON — using fallback", extra={"case_id": case_id})
        return {"final_case": _fallback(d, case_id, "JSON parse failure")}

    # Guaranteed fields — injected here, not echoed by LLM
    parsed["case_id"]        = case_id
    parsed["customer_id"]    = d.get("customer_id", "")
    parsed["transaction_id"] = d.get("transaction_id", "")
    parsed.setdefault("status", "Dispute Raised")
    parsed.setdefault("workflow_ready", True)
    parsed.setdefault("created_at", utc_now_iso())

    # Clamp confidence via tool
    parsed["confidence_score"] = clamp_score.invoke({"score": float(parsed.get("confidence_score", 0.5))})

    # Priority via tool if LLM didn't return a valid one
    valid_priorities = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
    if parsed.get("priority") not in valid_priorities:
        parsed["priority"] = calculate_priority.invoke({
            "amount":          float(d.get("amount", 0)),
            "fraud_suspicion": parsed.get("fraud_suspicion", False),
            "risk_tags":       parsed.get("risk_tags", []),
        })

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

    return {"final_case": parsed}
