"""
Agent 1 (ARIA) understanding tools — 4 deterministic analysers.

These tools process input data only — no DB queries, no external calls.
They give ARIA's LLM structured intelligence to reason from before
producing the final classification JSON.

Wiring (same pattern as Agent 2):
  agent.yaml     → agent_tools names
  config.py      → get_agent_tool_names() reads YAML
  TOOL_REGISTRY  → name : callable
  pipeline.py    → TOOL_REGISTRY[name] → bind_tools
  graph.py       → TOOL_REGISTRY[name] → ToolNode
"""
from datetime import datetime

from langchain_core.tools import tool


# ── Tool 1 — Transaction risk analysis ────────────────────────────────────────

@tool
def assess_transaction_context(
    amount: float,
    transaction_type: str,
    merchant: str,
    transaction_date: str,
    transaction_time: str = "",
) -> str:
    """Assess the full transaction context for risk signals.
    Computes amount tier, off-hours flag, card-not-present risk,
    weekend flag, and international merchant pattern.
    Returns a structured context summary with active signals.
    Call this FIRST for every dispute — it anchors the risk baseline."""
    signals = []

    # Amount tier
    if amount > 100_000:
        amount_tier = "CRITICAL"
        signals.append(f"Very high-value transaction (INR {amount:,.0f})")
    elif amount > 50_000:
        amount_tier = "HIGH"
        signals.append(f"High-value transaction (INR {amount:,.0f})")
    elif amount > 10_000:
        amount_tier = "MEDIUM"
    else:
        amount_tier = "LOW"

    # Hour-of-day analysis
    hour = -1
    if transaction_time:
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                hour = datetime.strptime(transaction_time.split(".")[0], fmt).hour
                break
            except ValueError:
                continue

    off_hours = 0 <= hour <= 5
    if off_hours:
        signals.append(f"Transaction at unusual hour ({hour:02d}:xx — midnight-to-dawn window)")

    # Weekend
    weekend = False
    if transaction_date:
        try:
            if datetime.strptime(transaction_date, "%Y-%m-%d").weekday() >= 5:
                weekend = True
                signals.append("Transaction on weekend")
        except ValueError:
            pass

    # Card-not-present
    cnp_types = {"UPI", "Net Banking", "Online Purchase", "International"}
    is_cnp = transaction_type in cnp_types
    if is_cnp:
        signals.append(f"Card-not-present transaction ({transaction_type})")

    # International merchant pattern
    intl_patterns = {".com", "paypal", "apple", "google play", "itunes",
                     "netflix", "spotify", "steam", "alibaba", "amazon.com"}
    merchant_lower = merchant.lower()
    is_intl = any(p in merchant_lower for p in intl_patterns)
    if is_intl:
        signals.append("Merchant matches international pattern")

    # Composite risk level
    risk_score = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}[amount_tier]
    if off_hours: risk_score += 2
    if is_cnp:    risk_score += 1
    if is_intl:   risk_score += 1

    risk_level = "HIGH" if risk_score >= 7 else "MEDIUM" if risk_score >= 4 else "LOW"
    signals_str = "\n".join(f"  • {s}" for s in signals) if signals else "  None detected"

    return (
        "TRANSACTION RISK ANALYSIS\n"
        f"  Amount               : INR {amount:,.2f} (Tier: {amount_tier})\n"
        f"  Type                 : {transaction_type} ({'Card-Not-Present' if is_cnp else 'Standard'})\n"
        f"  Merchant             : {merchant} ({'International pattern' if is_intl else 'Domestic'})\n"
        f"  Date                 : {transaction_date} ({'Weekend' if weekend else 'Weekday'})\n"
        f"  Hour                 : {f'{hour:02d}:xx' if hour >= 0 else 'Not provided'} "
        f"({'OFF-HOURS — high risk' if off_hours else 'Normal business hours'})\n"
        f"  Risk Level           : {risk_level}\n"
        f"  Active Risk Signals:\n{signals_str}"
    )


# ── Tool 2 — Fraud indicator scoring ──────────────────────────────────────────

_FRAUD_KEYWORDS = {
    "didn't do", "did not do", "i did not", "not me", "not mine",
    "unauthorized", "not authorised", "not authorized", "without my",
    "someone else", "hacked", "stolen", "stole", "fraud", "scam",
    "deceived", "cheated", "tricked", "phishing", "otp", "vishing",
    "sim swap", "account takeover", "no idea", "i never", "never did",
}


@tool
def score_fraud_indicators(
    customer_comment: str,
    otp_received: str,
    otp_shared: str,
    bank_impersonation: str,
    remote_access: str,
    phishing_link: str,
    sim_swap_suspected: str,
    card_lost: str,
    device_lost: str,
    bank_contacted: str,
    card_blocked: str,
) -> str:
    """Score fraud indicators from the customer's statement and metadata checklist.
    Analyses keyword patterns in the comment and active metadata flags.
    Returns a fraud signal level (NONE/LOW/MEDIUM/HIGH/CRITICAL) and list of
    active indicators. Call this for EVERY dispute.
    Pass "Yes", "No", or "Not provided" for each metadata flag."""
    def is_yes(v: str) -> bool:
        return str(v).strip().lower() in {"yes", "true", "1"}

    score = 0.0
    indicators = []

    # Comment keyword scan
    comment_lower = customer_comment.lower()
    matched = [kw for kw in _FRAUD_KEYWORDS if kw in comment_lower]
    if matched:
        score += min(len(matched) * 1.5, 4.5)
        indicators.append(f"Fraud language detected: {', '.join(matched[:5])}")

    # Metadata flags
    if is_yes(otp_shared):
        score += 4
        indicators.append("OTP shared with third party — social engineering confirmed")
    if is_yes(bank_impersonation):
        score += 4
        indicators.append("Bank impersonation call — vishing attack pattern")
    if is_yes(remote_access):
        score += 4
        indicators.append("Remote access app installed — device compromise likely")
    if is_yes(phishing_link):
        score += 3
        indicators.append("Phishing link clicked — credential theft risk")
    if is_yes(sim_swap_suspected):
        score += 4
        indicators.append("SIM swap suspected — account takeover via telecom carrier")
    if is_yes(card_lost):
        score += 3
        indicators.append("Card lost or stolen — physical theft vector")
    if is_yes(device_lost):
        score += 3
        indicators.append("Device lost or stolen — physical access to account")
    if is_yes(otp_received) and any(k in comment_lower for k in ("didn't do", "not me", "unauthorized", "did not")):
        score += 2
        indicators.append("OTP received but customer denies transaction — social engineering pattern")

    # Protective actions
    protective = []
    if is_yes(bank_contacted): protective.append("bank contacted")
    if is_yes(card_blocked):   protective.append("card blocked")

    level = (
        "CRITICAL" if score >= 10 else
        "HIGH"     if score >= 6  else
        "MEDIUM"   if score >= 3  else
        "LOW"      if score >= 1  else
        "NONE"
    )

    indicators_str = "\n".join(f"  • {i}" for i in indicators) if indicators else "  None detected"

    return (
        "FRAUD INDICATOR ANALYSIS\n"
        f"  Fraud Signal Level   : {level} (score: {score:.1f})\n"
        f"  Active Indicators:\n{indicators_str}\n"
        f"  Protective Steps     : {', '.join(protective) if protective else 'None taken'}\n"
        f"  Recommendation       : "
        f"{'Escalate as fraud immediately' if level in ('CRITICAL', 'HIGH') else 'Verify with customer — moderate signals present' if level == 'MEDIUM' else 'Low fraud risk — process as standard dispute'}"
    )


# ── Tool 3 — Evidence document verification ───────────────────────────────────

@tool
def verify_evidence_match(
    document_text: str,
    claimed_amount: str,
    claimed_merchant: str,
    dispute_description: str,
) -> str:
    """Verify whether submitted evidence documents support the customer's claim.
    Pass the full document text (OCR output), the claimed amount as a string,
    the claimed merchant name, and a brief description of the dispute.
    Returns MATCH, PARTIAL_MATCH, or MISMATCH with an explanation.
    Call this ONLY when documents are attached — skip if "No documents attached."."""
    doc_lower = document_text.lower().strip()

    if not doc_lower or doc_lower in {"no documents attached.", "no documents attached"}:
        return (
            "EVIDENCE VERIFICATION\n"
            "  Verdict              : NO_DOCUMENTS\n"
            "  Evidence Match       : null\n"
            "  Note                 : No documents were submitted with this dispute."
        )

    # Amount matching
    amount_clean = (
        str(claimed_amount)
        .replace(",", "").replace("INR", "").replace("₹", "")
        .replace("Rs", "").strip()
    )
    amount_match = bool(amount_clean) and amount_clean in document_text

    # Merchant matching (any word > 3 chars)
    merchant_words = [w.lower() for w in claimed_merchant.split() if len(w) > 3]
    merchant_match = any(w in doc_lower for w in merchant_words) if merchant_words else False

    # Dispute type keyword matching
    category_keywords = {
        "unauthorized": ["transaction", "charged", "debit", "not mine", "account"],
        "duplicate":    ["charged twice", "double", "duplicate", "same amount"],
        "refund":       ["refund", "cancelled", "cancellation", "return"],
        "product":      ["order", "delivery", "not received", "not delivered", "tracking"],
        "atm":          ["cash", "atm", "dispensed", "withdrawal"],
        "merchant":     ["invoice", "receipt", "overcharg", "wrong amount"],
    }
    desc_lower = dispute_description.lower()
    keyword_match = any(
        any(keyword_part in desc_lower for keyword_part in [cat_key])
        and any(k in doc_lower for k in kws)
        for cat_key, kws in category_keywords.items()
    )

    # Contradiction checks
    contradictions = []
    if "approved" in doc_lower and "unauthorized" in desc_lower:
        contradictions.append("document shows customer approval for claimed unauthorized transaction")
    if "delivered" in doc_lower and "not received" in desc_lower:
        contradictions.append("document shows delivery confirmation while customer claims non-delivery")

    if contradictions:
        verdict      = "MISMATCH"
        match_value  = "false"
        note = f"Document contradicts the claim: {'; '.join(contradictions)}."
    elif sum([amount_match, merchant_match, keyword_match]) >= 2:
        verdict     = "MATCH"
        match_value = "true"
        parts = (
            (["amount corroborated"] if amount_match else []) +
            (["merchant name found"] if merchant_match else []) +
            (["content consistent with dispute type"] if keyword_match else [])
        )
        note = f"Document supports the claim: {', '.join(parts)}."
    elif amount_match or merchant_match or keyword_match:
        verdict     = "PARTIAL_MATCH"
        match_value = "true"
        note = "Document partially supports the claim — single matching element, inconclusive but not contradictory."
    else:
        verdict     = "MISMATCH"
        match_value = "false"
        note = "Document does not clearly support the claim — content does not match transaction details or dispute type."

    return (
        "EVIDENCE VERIFICATION\n"
        f"  Verdict              : {verdict}\n"
        f"  Evidence Match       : {match_value}\n"
        f"  Amount Match         : {'Yes' if amount_match else 'No'}\n"
        f"  Merchant Match       : {'Yes' if merchant_match else 'No'}\n"
        f"  Keyword Match        : {'Yes' if keyword_match else 'No'}\n"
        f"  Note                 : {note}"
    )


# ── Tool 4 — Confidence score calculator ─────────────────────────────────────

@tool
def compute_confidence_score(
    fields_complete: bool,
    comment_quality: str,
    fraud_signal_level: str,
    fraud_category_consistent: bool,
    evidence_verdict: str,
    has_contradictions: bool,
) -> str:
    """Compute a calibrated confidence score for the dispute classification.
    Call this LAST — after analyze_transaction_risk, score_fraud_indicators,
    and verify_evidence_match (if applicable) — and use their outputs as inputs.

    fields_complete: true if amount, merchant, comment, and date are all present
    comment_quality: "DETAILED" | "MODERATE" | "VAGUE"
    fraud_signal_level: one of CRITICAL/HIGH/MEDIUM/LOW/NONE (from score_fraud_indicators)
    fraud_category_consistent: true if fraud signals align with the dispute category
    evidence_verdict: "MATCH" | "PARTIAL_MATCH" | "MISMATCH" | "NO_DOCUMENTS"
    has_contradictions: true if any fields or statements contradict each other

    Returns the final confidence score (0.10–1.00) with a full breakdown.
    Use this score as the confidence_score field in your final JSON output."""
    score = 0.50  # base
    breakdown = []

    if fields_complete:
        score += 0.10
        breakdown.append("+0.10 all required fields present and complete")
    else:
        score -= 0.10
        breakdown.append("-0.10 incomplete transaction or customer details")

    if comment_quality == "DETAILED":
        score += 0.10
        breakdown.append("+0.10 detailed and specific customer description")
    elif comment_quality == "VAGUE":
        score -= 0.10
        breakdown.append("-0.10 vague or too-short customer comment")

    if fraud_category_consistent and fraud_signal_level in ("HIGH", "CRITICAL"):
        score += 0.15
        breakdown.append("+0.15 strong fraud signals consistent with dispute category")
    elif fraud_category_consistent and fraud_signal_level == "MEDIUM":
        score += 0.08
        breakdown.append("+0.08 moderate fraud signals consistent with dispute category")
    elif not fraud_category_consistent and fraud_signal_level in ("HIGH", "CRITICAL"):
        score -= 0.10
        breakdown.append("-0.10 high fraud signals but inconsistent with stated dispute type")

    if evidence_verdict == "MATCH":
        score += 0.20
        breakdown.append("+0.20 submitted documents clearly corroborate the claim")
    elif evidence_verdict == "PARTIAL_MATCH":
        score += 0.08
        breakdown.append("+0.08 submitted documents partially corroborate the claim")
    elif evidence_verdict == "MISMATCH":
        score -= 0.20
        breakdown.append("-0.20 submitted documents contradict or do not support the claim")
    # NO_DOCUMENTS: no adjustment

    if has_contradictions:
        score -= 0.15
        breakdown.append("-0.15 contradictions detected between submission fields")

    score = max(0.10, min(1.0, round(score, 2)))

    breakdown_str = "\n".join(f"  {b}" for b in breakdown)
    interp = (
        "High confidence — classification is well-supported" if score >= 0.75 else
        "Moderate confidence — classification is supported but verify" if score >= 0.55 else
        "Low confidence — manual review strongly recommended"
    )

    return (
        "CONFIDENCE SCORE CALCULATION\n"
        f"  Final Score          : {score:.2f} ({score * 100:.0f}%)\n"
        f"  Breakdown:\n{breakdown_str}\n"
        f"  Interpretation       : {interp}"
    )


# ── Registry ──────────────────────────────────────────────────────────────────
# graph.py and pipeline.py resolve callables by reading agent_tools from agent.yaml
# and looking each name up here. Add a new tool here + in agent.yaml — nowhere else.

TOOL_REGISTRY: dict = {
    "assess_transaction_context": assess_transaction_context,
    "score_fraud_indicators":   score_fraud_indicators,
    "verify_evidence_match":    verify_evidence_match,
    "compute_confidence_score": compute_confidence_score,
}

TOOLS = list(TOOL_REGISTRY.values())
