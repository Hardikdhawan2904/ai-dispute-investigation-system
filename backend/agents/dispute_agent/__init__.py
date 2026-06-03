"""
Agent 1 — ARIA (Dispute Understanding Agent)

Job: Read the customer's submission + evidence, use 4 analytical tools to
     gather structured intelligence, then classify the dispute and score
     confidence. Nothing more — investigation is Agent 2's responsibility.

Pattern: validate → build_evidence → ReAct loop (agent ↔ tools) → finalize

Tools (understanding only, no DB):
  analyze_transaction_risk   → amount tier, time-of-day, card-not-present signals
  score_fraud_indicators     → metadata checklist + comment keyword analysis
  verify_evidence_match      → document corroboration check (called if docs attached)
  compute_confidence_score   → calibrated confidence from all tool findings
"""
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from agents.dispute_agent.graph import dispute_graph
from agents.dispute_agent.state import DisputeAgentState
from services.dispute_understanding_fallback_service import (
    classify_failure,
    generate_agent1_fallback,
)
from utils.logger import agent_logger


def run_dispute_agent(dispute_input: dict, document_texts: Optional[List[str]] = None) -> dict:
    """
    Understand a dispute and return a fully structured case dict.
    The LLM calls analytical tools autonomously, then produces the final JSON.
    Always returns a valid dict — falls back gracefully if the graph fails.
    """
    initial: DisputeAgentState = {
        "messages":            [],
        "dispute_input":       dispute_input,
        "document_texts":      document_texts or [],
        "case_id":             "",
        "supporting_evidence": "",
        "document_section":    "",
        "final_case":          {},
        "error":               None,
        "tools_used":          [],
        "agent_metadata":      {},
        "metrics":             {},
        "agent_start_time":    0.0,
    }
    try:
        result = dispute_graph.invoke(initial, config={"recursion_limit": 12})
        return result["final_case"]
    except Exception as exc:
        failure_reason = classify_failure(exc)
        agent_logger.error(
            f"Agent 1 graph failed ({failure_reason}): {exc}",
            exc_info=True,
        )
        return generate_agent1_fallback(dispute_input, failure_reason)
