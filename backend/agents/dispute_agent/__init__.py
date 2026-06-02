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


def run_dispute_agent(dispute_input: dict, document_texts: Optional[List[str]] = None) -> dict:
    """
    Understand a dispute and return a fully structured case dict.
    The LLM calls analytical tools autonomously, then produces the final JSON.
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
    }
    result = dispute_graph.invoke(initial)
    return result["final_case"]
