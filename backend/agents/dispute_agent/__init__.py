"""
ARIA entry point.

run_dispute_agent builds the initial message list (SystemMessage + HumanMessage)
and invokes the LangGraph ReAct loop. The LLM calls all 4 tools autonomously —
validate_dispute_input, build_evidence_summary, calculate_priority, clamp_score —
in whatever order it decides, then produces the final JSON.
"""
import json
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from agents.dispute_agent.graph import dispute_graph
from agents.dispute_agent.state import DisputeAgentState

_SYSTEM_PROMPT = """\
You are ARIA (Automated Resolution Intelligence Agent), a Senior AI Dispute Analyst at a BFSI bank.

## Your goal
Analyze the customer dispute submission and produce a complete, accurate investigation brief as a JSON object.

## Tools available — use them as you see fit
- validate_dispute_input    : confirms or generates a case_id for this submission
- build_evidence_summary    : builds a fraud-indicator checklist from transaction metadata
- calculate_priority        : validates a priority level against business rules
- clamp_score               : ensures a confidence score stays within the valid [0.0, 1.0] range

Use whichever tools you need, in whatever order makes sense given what you observe.
You may call a tool more than once if needed. You may skip a tool if it is not relevant.

## Output — when you are done reasoning, respond with ONLY this JSON object
{
  "transaction_type":        "UPI | NEFT | IMPS | Card | ATM | etc.",
  "merchant":                "merchant or payee name",
  "amount":                  0.0,
  "currency":                "INR",
  "dispute_category":        "Unauthorized Transaction | Duplicate Transaction | Refund Not Received | Product Not Received | Subscription Abuse | ATM Cash Issue | Merchant Dispute | Friendly Fraud | Other",
  "fraud_suspicion":         true,
  "customer_intent_summary": "2-3 sentence plain-language summary of the customer claim",
  "priority":                "CRITICAL | HIGH | MEDIUM | LOW",
  "confidence_score":        0.85,
  "risk_tags":               ["TAG_ONE", "TAG_TWO"],
  "structured_reasoning":    "3-5 sentence audit trail explaining your classification",
  "evidence_match":          true,
  "evidence_match_note":     "1-2 sentence note on document relevance"
}

## Priority reference
- CRITICAL : fraud_suspicion=true AND amount > 50000, OR identity theft indicators
- HIGH     : fraud_suspicion=true OR amount > 50000 OR multiple high-risk tags
- MEDIUM   : moderate-confidence dispute, amounts 10000–50000, refund/product issues
- LOW      : minor merchant disputes, low amounts, clear resolution path

## Constraints
- Factual analysis only — no legal or financial advice
- Never fabricate transaction details not present in the input
- Return ONLY valid parseable JSON — no markdown, no prose, no code fences
- Express uncertainty via confidence_score — never suppress it\
"""


def run_dispute_agent(dispute_input: dict, document_texts: Optional[List[str]] = None) -> dict:
    """
    Entry point called by dispute_service / ops routes.
    The LLM calls all 4 tools autonomously via the ReAct loop.
    Returns the fully structured case dict ready for DB storage.
    """
    docs = document_texts or []
    initial: DisputeAgentState = {
        "messages": [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=_build_human_message(dispute_input, docs)),
        ],
        "dispute_input":  dispute_input,
        "document_texts": docs,
        "final_case":     {},
        "error":          None,
    }
    result = dispute_graph.invoke(initial)
    return result["final_case"]


def _build_human_message(d: dict, doc_texts: list) -> str:
    lines = [
        "## Dispute Submission",
        f"Customer ID    : {d.get('customer_id', 'N/A')}",
        f"Customer Name  : {d.get('customer_name', 'N/A')}",
        f"Transaction ID : {d.get('transaction_id', 'N/A')}",
        f"Type           : {d.get('transaction_type', 'N/A')}",
        f"Merchant       : {d.get('merchant', 'N/A')}",
        f"Amount         : {d.get('currency', 'INR')} {d.get('amount', 0)}",
        f"Date / Time    : {d.get('transaction_date', 'N/A')} {d.get('transaction_time', '')}".rstrip(),
        f"Dispute Reason : {d.get('dispute_reason', 'N/A')}",
        f"Fraud Selected : {d.get('fraud_selected', False)}",
        f"Customer Note  : {d.get('customer_comment') or 'None'}",
        "",
        "## Transaction Metadata",
        json.dumps(d.get("transaction_metadata") or {}, indent=2),
    ]

    if doc_texts:
        lines.append("\n## Uploaded Documents")
        for i, text in enumerate(doc_texts, 1):
            if text.strip():
                body = text[:3000] + ("..." if len(text) > 3000 else "")
                lines.append(f"\nDocument {i}:\n{body}")

    return "\n".join(lines)
