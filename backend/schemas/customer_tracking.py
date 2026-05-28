"""
Customer-safe tracking schemas for the public dispute tracking endpoint.

NEVER expose: AI reasoning, fraud signals, confidence scores, risk tags,
workflow states, LangGraph nodes, or any internal investigation details.
"""
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel

from database.models import DisputeCase, AuditLog


def _utc_iso(dt: datetime | None) -> str | None:
    """Return an ISO-8601 string with explicit UTC offset so browsers convert to local time."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


# ── Status mapping — internal → customer-visible ───────────────────────────────

CUSTOMER_STATUS_MAP: dict[str, str] = {
    "Dispute Raised":      "Dispute Submitted",
    "Under Investigation": "Under Review",
    "Pending Documents":   "Documents Requested",
    "Escalated":           "Investigation In Progress",
    "Resolved":            "Resolved",
    "Rejected":            "Resolved",
    "Closed":              "Resolved",
}

_ESTIMATED_RESOLUTION: dict[str, str] = {
    "Dispute Raised":      "Within 7 business days",
    "Under Investigation": "Within 5 business days",
    "Pending Documents":   "Within 5 business days of document receipt",
    "Escalated":           "Within 3 business days",
    "Resolved":            "Resolved",
    "Rejected":            "Resolved",
    "Closed":              "Closed",
}

# Audit log STATUS_CHANGED → customer-visible description
_STATUS_CHANGE_MESSAGES: dict[str, str] = {
    "Under Investigation": "Case assigned to our disputes team for review",
    "Pending Documents":   "Additional documentation has been requested",
    "Escalated":           "Case under priority investigation",
    "Resolved":            "Investigation complete — resolution has been determined",
    "Rejected":            "Case review complete",
    "Closed":              "Case closed",
}

# Audit log event_type values that surface customer-visible timeline entries
_SURFACE_EVENTS = {"CASE_CREATED", "STATUS_CHANGED"}


# ── Schemas ────────────────────────────────────────────────────────────────────

class TimelineEvent(BaseModel):
    description: str
    timestamp: Optional[str] = None


class CustomerTrackingResponse(BaseModel):
    case_id:              str
    status:               str           # customer-friendly label
    dispute_reason:       Optional[str] = None
    merchant:             str
    amount:               float
    currency:             str
    transaction_type:     str
    submission_date:      str
    last_updated:         Optional[str] = None
    estimated_resolution: str
    document_requested:   bool
    timeline:             List[TimelineEvent]


# ── Builder ────────────────────────────────────────────────────────────────────

def build_tracking_response(
    case: DisputeCase,
    audit_logs: List[AuditLog],
) -> dict:
    """
    Build a customer-safe tracking payload from a DisputeCase and its audit logs.
    Filters out all internal workflow events; only surfaces customer-visible milestones.
    """
    customer_status = CUSTOMER_STATUS_MAP.get(case.status, "Under Review")
    est_resolution  = _ESTIMATED_RESOLUTION.get(case.status, "Under review")
    doc_requested   = case.status == "Pending Documents"

    timeline: List[TimelineEvent] = []

    for log in audit_logs:
        event_type = (log.event_type or "").strip()

        if event_type not in _SURFACE_EVENTS:
            continue

        if event_type == "CASE_CREATED":
            timeline.append(TimelineEvent(
                description="Dispute received — case reference assigned",
                timestamp=_utc_iso(log.created_at),
            ))

        elif event_type == "STATUS_CHANGED":
            payload    = log.payload or {}
            new_status = payload.get("new_status", "")
            msg        = _STATUS_CHANGE_MESSAGES.get(new_status)
            if msg:
                timeline.append(TimelineEvent(
                    description=msg,
                    timestamp=_utc_iso(log.created_at),
                ))

    return CustomerTrackingResponse(
        case_id              = case.case_id,
        status               = customer_status,
        dispute_reason       = case.dispute_reason,
        merchant             = case.merchant or "",
        amount               = case.amount,
        currency             = case.currency or "INR",
        transaction_type     = case.transaction_type,
        submission_date      = _utc_iso(case.created_at) or "",
        last_updated         = _utc_iso(case.updated_at),
        estimated_resolution = est_resolution,
        document_requested   = doc_requested,
        timeline             = timeline,
    ).model_dump()
