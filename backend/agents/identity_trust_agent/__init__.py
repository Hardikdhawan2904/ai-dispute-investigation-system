"""
Agent 4 — ITIA (Identity & Trust Intelligence Agent) Entry Point.

Job: Read customer profile, KYC match records, device IDs, and dispute logs
     from the database (or in-memory state), pre-run 3 tools, and return a
     trust and risk assessment brief.
"""
import time
from typing import Optional

from agents.identity_trust_agent.graph import identity_trust_graph
from agents.identity_trust_agent.state import IdentityTrustAgentState
from utils.logger import agent_logger


def _read_case_from_db(case_id: str) -> dict:
    """Read dispute case data directly from dispute_cases table by case_id."""
    from database.database import SessionLocal
    from database.models import DisputeCase
    db = SessionLocal()
    try:
        case = db.query(DisputeCase).filter(DisputeCase.case_id == case_id).first()
        if not case:
            raise ValueError(f"Case {case_id} not found in database")
        return {
            "case_id":          case.case_id,
            "customer_id":      case.customer_id,
            "customer_name":    case.customer_name or "",
            "email":            case.email or "",
            "phone":            case.phone or "",
            "transaction_id":   case.transaction_id,
            "transaction_type": case.transaction_type,
            "merchant":         case.merchant or "",
            "amount":           case.amount,
            "currency":         case.currency,
            "transaction_date": case.transaction_date or "",
            "transaction_time": case.transaction_time or "",
            "dispute_reason":   case.dispute_reason or "",
            "fraud_selected":   case.fraud_selected,
            "transaction_metadata": case.transaction_metadata or {},
        }
    finally:
        db.close()


def run_identity_trust_agent(
    dispute_input: dict,
    case_id: Optional[str] = None,
) -> dict:
    """
    Execute the Identity & Trust Intelligence Agent.
    
    If case_id is provided, reads data fresh from the dispute_cases database table.
    Falls back to dispute_input dict if database read fails or case_id is not specified.
    """
    active_case_id = case_id or dispute_input.get("case_id", "")

    # Read from DB if case_id provided
    if active_case_id:
        try:
            dispute_input = _read_case_from_db(active_case_id)
            agent_logger.info(f"Agent 4 reading case {active_case_id} from database")
        except Exception as exc:
            agent_logger.warning(
                f"Agent 4 DB read failed for {active_case_id}, using passed input: {exc}"
            )

    initial: IdentityTrustAgentState = {
        "messages":         [],
        "dispute_input":    dispute_input,
        "case_id":          active_case_id,
        "tool_results":     {},
        "final_output":     {},
        "error":            None,
        "tools_used":       [],
        "agent_metadata":   {},
        "metrics":          {},
        "agent_start_time": time.time(),
    }

    try:
        result = identity_trust_graph.invoke(initial, config={"recursion_limit": 6})
        return result["final_output"]
    except Exception as exc:
        agent_logger.error(f"Identity & Trust Agent graph failed: {exc}", exc_info=True)
        from agents.identity_trust_agent.nodes.pipeline import _fallback_output
        return _fallback_output(
            active_case_id,
            [],
            {
                "agent_name": "Identity & Trust Intelligence Agent",
                "agent_version": "1.0.0",
                "model": "fallback",
            },
            {"total_duration_ms": 0.0, "llm_calls": 0, "tool_calls": 0}
        )
