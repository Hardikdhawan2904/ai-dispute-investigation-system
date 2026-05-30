"""
Prepare the initial HumanMessage that kicks off the agentic ReAct loop.
All dispute data and document text is embedded here so the orchestrator LLM
has full context when it decides which tools to call and in what order.
"""
import json

from langchain_core.messages import HumanMessage

from agents.dispute_agent.state import DisputeAgentState
from utils.helpers import utc_now_iso
from utils.logger import agent_logger, log_workflow_event

_MAX_DOC_CHARS = 3000  # Per-document truncation guard against token overflow


def prepare_input(state: DisputeAgentState) -> dict:
    d = state["dispute_input"]
    doc_texts = state.get("document_texts") or []

    # Build document section (truncated per doc to avoid token overflow)
    if doc_texts:
        parts = []
        for i, t in enumerate(doc_texts):
            if t.strip():
                body = t[:_MAX_DOC_CHARS] + ("..." if len(t) > _MAX_DOC_CHARS else "")
                parts.append(f"Document {i + 1}:\n{body}")
        document_section = "\n\n".join(parts) if parts else "No documents attached."
    else:
        document_section = "No documents attached."

    meta = d.get("transaction_metadata") or {}
    meta_json_str = json.dumps(meta)

    # Dispute fields the orchestrator will pass to run_dispute_analysis
    dispute_fields = {
        "customer_name":    d.get("customer_name", "Unknown"),
        "customer_id":      d.get("customer_id", ""),
        "transaction_type": d.get("transaction_type", ""),
        "merchant":         d.get("merchant", ""),
        "amount":           d.get("amount", 0),
        "currency":         d.get("currency", "INR"),
        "transaction_date": d.get("transaction_date", ""),
        "transaction_time": d.get("transaction_time", ""),
        "dispute_reason":   d.get("dispute_reason", ""),
        "fraud_selected":   d.get("fraud_selected", False),
        "customer_comment": d.get("customer_comment", ""),
    }
    dispute_input_json_str = json.dumps(dispute_fields)

    log_workflow_event(
        agent_logger,
        event="AGENT_ANALYSIS_START",
        stage="dispute_understanding",
        case_id=d.get("case_id", "PENDING"),
        customer_id=d.get("customer_id"),
    )

    task = (
        "You are a BFSI dispute resolution agent. Process the following dispute by calling "
        "the provided tools in this exact sequence:\n\n"

        "STEP 1 — Call validate_dispute_input:\n"
        f'  customer_id     = "{d.get("customer_id", "")}"\n'
        f'  existing_case_id = "{d.get("case_id", "")}"\n\n'

        "STEP 2 — Call build_evidence_summary:\n"
        "  Pass the following string exactly as the metadata_json argument:\n"
        f"  {meta_json_str}\n\n"

        "STEP 3 — Call run_dispute_analysis using the outputs from steps 1 and 2:\n"
        "  case_id           = <result from step 1>\n"
        "  supporting_evidence = <result from step 2>\n"
        "  document_section  = (see document text below)\n"
        "  dispute_input_json = pass the following string exactly:\n"
        f"  {dispute_input_json_str}\n\n"

        "  DOCUMENT SECTION to pass as document_section:\n"
        f"{document_section}\n\n"

        "STEP 4 — From the JSON returned by run_dispute_analysis, extract the confidence_score "
        "value and call clamp_score:\n"
        "  score = <confidence_score from step 3 JSON>\n\n"

        "STEP 5 — If the priority in the step 3 JSON is NOT one of CRITICAL/HIGH/MEDIUM/LOW, "
        "call calculate_priority:\n"
        f"  amount          = {d.get('amount', 0)}\n"
        f"  fraud_suspicion = {str(bool(d.get('fraud_selected', False))).lower()}\n"
        "  risk_tags       = []\n\n"

        "Execute all steps now, starting with Step 1."
    )

    return {"messages": [HumanMessage(content=task)]}
