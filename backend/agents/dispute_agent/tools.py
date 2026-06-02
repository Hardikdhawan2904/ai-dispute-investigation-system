"""
ARIA investigative tools — 4 tools that query real data so the LLM reasons
over actual intelligence, not just the customer's self-reported submission.

Tool contract:
  - No LLM call inside any tool
  - Every DB-touching tool opens its own session and closes it on exit
  - Every tool returns a human-readable string the LLM cites in its reasoning
"""
import json
from collections import Counter
from datetime import datetime, timezone, timedelta
from typing import List

from langchain_core.tools import tool

from utils.helpers import generate_case_id
from utils.logger import agent_logger


# ── Tool 1 — Customer history ─────────────────────────────────────────────────

@tool
def lookup_customer_history(customer_id: str) -> str:
    """Query the bank's case database for this customer's full dispute history.
    Returns total disputes, fraud-flag rate, most common categories, and a risk assessment.
    Call this first to detect repeat disputers, friendly fraud risk, or first-time claimants."""
    from database.database import SessionLocal
    from database.models import DisputeCase

    db = SessionLocal()
    try:
        cases = db.query(DisputeCase).filter(DisputeCase.customer_id == customer_id).all()

        if not cases:
            return (
                f"Customer History — ID: {customer_id}\n"
                "  Total Prior Disputes : 0\n"
                "  Assessment           : First-time disputer. No prior dispute history."
            )

        total      = len(cases)
        fraud_count = sum(1 for c in cases if c.fraud_suspicion)
        cats        = [c.dispute_category for c in cases if c.dispute_category]
        top_cats    = Counter(cats).most_common(3)
        avg_conf    = sum(c.confidence_score for c in cases if c.confidence_score) / total
        fraud_rate  = fraud_count / total

        if fraud_rate > 0.5 and total >= 3:
            risk = "HIGH — majority of disputes were fraud-flagged; verify claim carefully"
        elif total >= 5:
            risk = "MEDIUM — frequent disputer; review for friendly fraud risk"
        else:
            risk = "LOW — normal dispute pattern"

        return (
            f"Customer History — ID: {customer_id}\n"
            f"  Total Prior Disputes     : {total}\n"
            f"  Fraud-Flagged Disputes   : {fraud_count} ({fraud_rate:.0%})\n"
            f"  Top Categories           : {', '.join(f'{c}({n})' for c, n in top_cats) or 'None'}\n"
            f"  Avg Confidence Score     : {avg_conf:.2f}\n"
            f"  Risk Assessment          : {risk}"
        )
    finally:
        db.close()


# ── Tool 2 — Merchant risk ────────────────────────────────────────────────────

_RISKY_PATTERNS = {
    "flash", "lucky", "prize", "win", "reward", "lottery", "crypto",
    "bitcoin", "forex", "investment returns", "unlimited", "scheme",
    "jackpot", "doubl", "ponzi",
}


@tool
def check_merchant_risk(merchant_name: str) -> str:
    """Query the bank's case database for all disputes involving this merchant.
    Also checks the merchant name against known scam/blacklist patterns.
    Returns complaint count, fraud rate, top dispute categories, and risk level."""
    from database.database import SessionLocal
    from database.models import DisputeCase

    db = SessionLocal()
    try:
        cases = (
            db.query(DisputeCase)
            .filter(DisputeCase.merchant.ilike(f"%{merchant_name[:30]}%"))
            .all()
        )

        merchant_lower = merchant_name.lower()
        blacklisted    = any(p in merchant_lower for p in _RISKY_PATTERNS)

        if not cases:
            note = " — name matches known scam patterns, exercise caution" if blacklisted else ""
            return (
                f"Merchant Risk — '{merchant_name}'\n"
                f"  Prior Disputes in System : 0{note}\n"
                f"  Blacklist Pattern Match  : {'YES' if blacklisted else 'No'}\n"
                f"  Risk Level               : {'HIGH (blacklist match)' if blacklisted else 'UNKNOWN (no history)'}"
            )

        total       = len(cases)
        fraud_count = sum(1 for c in cases if c.fraud_suspicion)
        cats        = [c.dispute_category for c in cases if c.dispute_category]
        top_cats    = Counter(cats).most_common(3)
        fraud_rate  = fraud_count / total

        if blacklisted or fraud_rate > 0.6 or total > 20:
            risk = "CRITICAL"
        elif fraud_rate > 0.3 or total > 8:
            risk = "HIGH"
        elif fraud_rate > 0.1 or total > 3:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        return (
            f"Merchant Risk — '{merchant_name}'\n"
            f"  Total Complaints Filed   : {total}\n"
            f"  Fraud-Related Complaints : {fraud_count} ({fraud_rate:.0%})\n"
            f"  Top Dispute Categories   : {', '.join(f'{c}({n})' for c, n in top_cats)}\n"
            f"  Blacklist Pattern Match  : {'YES — extreme caution' if blacklisted else 'No'}\n"
            f"  Merchant Risk Level      : {risk}"
        )
    finally:
        db.close()


# ── Tool 3 — Duplicate detection ──────────────────────────────────────────────

@tool
def find_duplicate_transaction(
    transaction_id: str,
    customer_id: str,
    amount: float,
    merchant: str,
) -> str:
    """Search the case database for duplicate or near-duplicate disputes.
    Checks: (1) exact same transaction_id already disputed,
            (2) same customer + merchant + amount filed within 72 hours.
    If duplicates are found, classify the dispute as 'Duplicate Transaction'."""
    from database.database import SessionLocal
    from database.models import DisputeCase

    db = SessionLocal()
    try:
        found: List[str] = []

        if transaction_id:
            for c in db.query(DisputeCase).filter(
                DisputeCase.transaction_id == transaction_id
            ).all():
                found.append(
                    f"Case {c.case_id} — same transaction_id, status: {c.status}"
                )

        cutoff = datetime.now(timezone.utc) - timedelta(hours=72)
        for c in db.query(DisputeCase).filter(
            DisputeCase.customer_id == customer_id,
            DisputeCase.merchant.ilike(f"%{merchant[:20]}%"),
            DisputeCase.amount == amount,
            DisputeCase.created_at >= cutoff,
        ).all():
            entry = f"Case {c.case_id} — same customer+merchant+amount within 72h, status: {c.status}"
            if entry not in found:
                found.append(entry)

        if not found:
            return "Duplicate Check: No duplicate transactions found. This is a unique dispute."

        return (
            f"DUPLICATE ALERT — {len(found)} match(es) found:\n"
            + "\n".join(f"  • {f}" for f in found)
            + "\nAction: Classify as 'Duplicate Transaction' and reference the existing case(s)."
        )
    finally:
        db.close()


# ── Tool 4 — Fraud signal analyser ───────────────────────────────────────────

@tool
def analyze_fraud_signals(
    metadata_json: str,
    customer_comment: str,
    transaction_time: str,
    amount: float,
) -> str:
    """Run deterministic fraud signal analysis on transaction metadata and the customer statement.
    Returns a structured severity report listing every active fraud indicator.
    Always call this before forming your fraud_suspicion judgment."""
    try:
        meta = json.loads(metadata_json) if metadata_json else {}
    except Exception:
        meta = {}

    signals: List[str] = []
    severity = "NONE"

    def _flag(level: str, message: str) -> None:
        nonlocal severity
        signals.append(f"{level}: {message}")
        order = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        if order.get(level, 0) > order.get(severity, 0):
            severity = level

    # Critical
    if meta.get("otp_shared"):
        _flag("CRITICAL", "Customer shared OTP — classic social engineering / vishing")
    if meta.get("bank_impersonation"):
        _flag("CRITICAL", "Caller impersonated the bank — vishing attack confirmed")
    if meta.get("sim_swap_suspected"):
        _flag("CRITICAL", "SIM swap suspected — account takeover vector")

    # High
    if meta.get("remote_access"):
        _flag("HIGH", "Remote access app installed — device compromise risk")
    if meta.get("phishing_link"):
        _flag("HIGH", "Phishing link clicked — credential theft risk")
    if amount > 50_000:
        _flag("HIGH", f"High-value transaction ₹{amount:,.0f} exceeds ₹50,000 threshold")

    deny_kw = ["did not", "didn't", "not me", "not done", "i never", "unauthori", "without my"]
    if any(kw in (customer_comment or "").lower() for kw in deny_kw):
        _flag("HIGH", "Customer explicitly denies initiating the transaction")

    # Medium
    if meta.get("card_lost") or meta.get("device_lost"):
        _flag("MEDIUM", "Physical card or device reported lost/stolen")
    if meta.get("unknown_beneficiary"):
        _flag("MEDIUM", "Unknown beneficiary added to account before transaction")
    if meta.get("upi_collect_fraud"):
        _flag("MEDIUM", "UPI collect request fraud suspected")

    if transaction_time:
        try:
            hour = int(str(transaction_time).split(":")[0])
            if 0 <= hour < 5:
                _flag("MEDIUM", f"Transaction at {transaction_time} — unusual midnight-5AM window")
        except Exception:
            pass

    actions: List[str] = []
    if meta.get("card_blocked"):
        actions.append("card/account blocked immediately")
    if meta.get("bank_contacted"):
        actions.append("bank contacted prior to this dispute")

    if not signals:
        return (
            "Fraud Signal Analysis: No significant fraud indicators detected.\n"
            f"  Overall Severity         : NONE\n"
            f"  Protective Actions Taken : {', '.join(actions) or 'None'}\n"
            "  Assessment               : Low fraud risk — likely a merchant or service dispute."
        )

    return (
        f"Fraud Signal Analysis — Overall Severity: {severity}\n"
        f"  Active Signals ({len(signals)}):\n"
        + "\n".join(f"    • {s}" for s in signals)
        + f"\n  Protective Actions Taken : {', '.join(actions) or 'None — no protective steps taken despite fraud claim'}"
        + f"\n  Assessment               : "
        + (
            "Immediate escalation — strong fraud indicators present." if severity == "CRITICAL" else
            "High-priority investigation warranted." if severity == "HIGH" else
            "Standard fraud investigation protocol."
        )
    )


# ── Registry ──────────────────────────────────────────────────────────────────

TOOL_REGISTRY: dict = {
    "lookup_customer_history":    lookup_customer_history,
    "check_merchant_risk":        check_merchant_risk,
    "find_duplicate_transaction": find_duplicate_transaction,
    "analyze_fraud_signals":      analyze_fraud_signals,
}

TOOLS = list(TOOL_REGISTRY.values())
