from utils.helpers import generate_case_id
from utils.logger import agent_logger, log_workflow_event
from agents.dispute_agent.state import DisputeAgentState


def validate_input(state: DisputeAgentState) -> dict:
    dispute = state["dispute_input"]
    case_id = dispute.get("case_id") or generate_case_id()

    log_workflow_event(
        agent_logger,
        event="AGENT_ANALYSIS_START",
        stage="dispute_understanding",
        case_id=case_id,
        customer_id=dispute.get("customer_id"),
    )

    return {"case_id": case_id, "error": None}
