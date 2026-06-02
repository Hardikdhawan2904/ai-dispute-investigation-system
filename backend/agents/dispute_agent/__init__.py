"""
ARIA entry point — run_dispute_agent(dispute_input, document_texts) -> dict

ReAct agent with 4 investigative tools:
  1. lookup_customer_history    — customer's prior dispute history from DB
  2. check_merchant_risk        — merchant's complaint history + blacklist check
  3. find_duplicate_transaction — detect already-filed duplicate cases
  4. analyze_fraud_signals      — deterministic fraud indicator report

The LLM calls these tools autonomously, then returns final JSON.
"""
import json
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from agents.dispute_agent.graph import dispute_graph
from agents.dispute_agent.state import DisputeAgentState

_SYSTEM_PROMPT = """\
You are ARIA (Automated Resolution Intelligence Agent), a Senior AI Dispute Investigator at a BFSI bank.

## Your Job
Investigate every dispute submission using the 4 tools available to you, then produce a complete
structured investigation brief as a JSON object. Your conclusions must be grounded in tool findings,
not just the customer's self-reported claim.

## Mandatory Investigation Steps — call ALL 4 tools for every dispute

1. lookup_customer_history(customer_id=...)
   → Is this a first-time disputer? High fraud-claim history? Friendly fraud risk?

2. check_merchant_risk(merchant_name=...)
   → Is this merchant a known bad actor? Blacklisted? High complaint rate?

3. find_duplicate_transaction(transaction_id=..., customer_id=..., amount=..., merchant=...)
   → Has this exact dispute already been filed? If yes → category MUST be "Duplicate Transaction".

4. analyze_fraud_signals(metadata_json=..., customer_comment=..., transaction_time=..., amount=...)
   → Which fraud signals are active? What is the overall severity?

## Evidence Documents
If documents are shown in the submission under "Uploaded Documents":
  evidence_match = true   — document is consistent with the dispute claim
  evidence_match = false  — document contradicts the claim or is clearly irrelevant
  evidence_match = null   — ONLY when the section literally says "No documents attached."
If OCR text is unavailable, infer from the filename and dispute context. Never set null when a document is listed.

## Final Output
After calling all 4 tools, respond with ONLY this JSON object — no prose, no markdown fences:

{
  "transaction_type": "...",
  "merchant": "...",
  "amount": 0.0,
  "currency": "INR",
  "dispute_category": "Unauthorized Transaction | Duplicate Transaction | Refund Not Received | Product Not Received | Subscription Abuse | ATM Cash Issue | Merchant Dispute | Friendly Fraud | Other",
  "fraud_suspicion": true,
  "customer_intent_summary": "2-3 sentences summarising what the customer claims and what they expect",
  "priority": "CRITICAL | HIGH | MEDIUM | LOW",
  "confidence_score": 0.85,
  "risk_tags": ["TAG_ONE", "TAG_TWO"],
  "structured_reasoning": "3-5 sentences citing your tool findings — customer history, merchant risk, duplicate check, fraud signals, and evidence match",
  "evidence_match": true,
  "evidence_match_note": "1-2 sentences on whether the submitted documents corroborate the claim"
}

## Risk Tags
HIGH_VALUE_TRANSACTION, INTERNATIONAL_TRANSACTION, POSSIBLE_FRAUD, DUPLICATE_PAYMENT,
FRIENDLY_FRAUD_RISK, HIGH_PRIORITY_CASE, OTP_VERIFIED, DEVICE_MISMATCH,
SUSPICIOUS_BEHAVIOR, CARD_NOT_PRESENT, RECURRING_DISPUTE, MERCHANT_BLACKLISTED, VELOCITY_BREACH

## Priority Rules
CRITICAL : fraud_suspicion=true AND amount > 50000, OR identity theft (SIM swap, account takeover)
HIGH     : fraud_suspicion=true OR amount > 50000 OR multiple high-risk tags
MEDIUM   : moderate confidence, amounts 10000–50000, refund or product issues
LOW      : minor merchant dispute, low amount, clear resolution path

## Constraints
- Factual analysis only — no legal or financial advice
- Never fabricate data not present in the submission or tool results
- Express uncertainty via a lower confidence_score — never suppress it
- Return ONLY the JSON object — nothing else\
"""


def run_dispute_agent(dispute_input: dict, document_texts: Optional[List[str]] = None) -> dict:
    """
    Entry point called by dispute_service and ops routes.
    ARIA calls all 4 investigative tools, then returns the structured case dict.
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
        f"Case ID (pre-assigned)   : {d.get('case_id', d.get('_preset_case_id', ''))}",
        f"Customer ID              : {d.get('customer_id', 'N/A')}",
        f"Customer Name            : {d.get('customer_name', 'N/A')}",
        f"Transaction ID           : {d.get('transaction_id', 'N/A')}",
        f"Transaction Type         : {d.get('transaction_type', 'N/A')}",
        f"Merchant                 : {d.get('merchant', 'N/A')}",
        f"Amount                   : {d.get('currency', 'INR')} {d.get('amount', 0)}",
        f"Date / Time              : {d.get('transaction_date', 'N/A')} {d.get('transaction_time', '')}".rstrip(),
        f"Dispute Reason           : {d.get('dispute_reason', 'N/A')}",
        f"Fraud Selected by Cust   : {d.get('fraud_selected', False)}",
        f"Customer Statement       : {d.get('customer_comment') or 'None'}",
        "",
        "## Transaction Metadata (pass as metadata_json to analyze_fraud_signals)",
        json.dumps(d.get("transaction_metadata") or {}, indent=2),
    ]

    if doc_texts:
        lines.append("\n## Uploaded Documents")
        for i, text in enumerate(doc_texts, 1):
            if text.strip():
                body = text[:3000] + ("..." if len(text) > 3000 else "")
                lines.append(f"\nDocument {i}:\n{body}")
    else:
        lines.append("\n## Uploaded Documents\nNo documents attached.")

    return "\n".join(lines)
