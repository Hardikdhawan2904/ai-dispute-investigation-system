"""
Investigation Confidence Service — deterministic (no LLM).

Computes a single investigation_confidence score that measures how
reliable the overall investigation plan is, separate from:
  - data_quality_score  (input data completeness)
  - queue_confidence    (routing certainty)
  - Agent 1 confidence  (dispute classification certainty)

Weighting:
  40%  queue_confidence            (how certain the routing decision is)
  40%  data_quality_score          (how complete the input data is)
  20%  related_case_similarity     (derived from historical precedent)

Clamped to [0.10, 1.00].
"""
from __future__ import annotations


# ── Public API ────────────────────────────────────────────────────────────────

def calculate_investigation_confidence(plan: dict) -> float:
    queue_confidence   = float(plan.get("queue_confidence")   or 0.50)
    data_quality_score = float(plan.get("data_quality_score") or 0.50)
    similarity         = _related_case_similarity(plan.get("related_cases") or {})

    score = (0.40 * queue_confidence) + (0.40 * data_quality_score) + (0.20 * similarity)
    return round(max(0.10, min(1.00, score)), 2)


def calculate_confidence_tier(score: float) -> str:
    if score >= 0.90:
        return "Very High Confidence"
    if score >= 0.75:
        return "High Confidence"
    if score >= 0.60:
        return "Moderate Confidence"
    return "Requires Review"


def generate_confidence_factors(plan: dict) -> list:
    factors: list[str] = []

    # Historical precedent
    related  = plan.get("related_cases") or {}
    similar  = int(related.get("similar_cases") or 0)
    res_rate = float(related.get("resolution_rate") or 0.0)
    if similar >= 3:
        factors.append(f"Strong historical precedent available ({similar} similar cases)")
    elif similar >= 1:
        factors.append("Historical precedent available")

    # Merchant profile
    merch = plan.get("merchant_risk_profile") or {}
    if merch.get("merchant_risk") and merch.get("merchant_risk") not in ("UNKNOWN", ""):
        factors.append("Merchant profile available")

    # Customer history
    cust = plan.get("customer_risk_profile") or {}
    if cust.get("previous_disputes") is not None:
        factors.append("Customer history complete")

    # Data quality
    dq = float(plan.get("data_quality_score") or 0)
    if dq >= 0.80:
        factors.append("Complete transaction data")
    elif dq < 0.60:
        factors.append("Limited data quality reduces confidence")

    # Queue confidence
    qc = float(plan.get("queue_confidence") or 0)
    if qc >= 0.85:
        factors.append("Strong queue assignment confidence")
    elif qc < 0.60:
        factors.append("Queue assignment has uncertainty")

    # Investigation coverage breadth
    coverage = plan.get("investigation_coverage") or {}
    covered  = sum(1 for v in coverage.values() if v)
    if covered >= 4:
        factors.append("Comprehensive investigation coverage")
    elif covered <= 2:
        factors.append("Partial investigation coverage")

    # Resolution rate signal
    if similar > 0 and res_rate >= 0.70:
        factors.append(f"High resolution rate in similar cases ({int(res_rate * 100)}%)")

    if not factors:
        factors.append("Standard investigation criteria met")

    return factors


# ── Private helpers ───────────────────────────────────────────────────────────

def _related_case_similarity(related: dict) -> float:
    similar      = int(related.get("similar_cases") or 0)
    res_rate     = float(related.get("resolution_rate") or 0.0)

    if similar >= 5:
        # Many precedents + high resolution rate = strong similarity signal
        return round(min(0.50 + (res_rate * 0.50), 1.00), 2)
    if similar >= 2:
        return round(0.50 + (res_rate * 0.30), 2)
    if similar == 1:
        return 0.35
    return 0.20
