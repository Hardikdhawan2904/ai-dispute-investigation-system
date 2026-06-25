# CCA — Customer Communication Agent (Agent 6)

**Role**: Professional HTML email notifications for dispute lifecycle events
**Model**: Groq `llama-3.1-8b-instant` (temperature 0.3 for natural tone)
**Version**: 1.1.0

---

## How it works

CCA is triggered asynchronously when case status changes or document requests are created. The LLM generates professional, empathetic email content. Delivery is via Outlook SMTP.

**Pipeline**: `validate → generate (LLM) → deliver (SMTP + communication_logs)`

---

## Notification Types

| Type | Trigger |
|---|---|
| `CASE_RECEIVED` | Dispute submission confirmed |
| `INVESTIGATION_STARTED` | Status → Under Investigation |
| `DOCUMENT_REQUESTED` | Analyst creates document request |
| `CASE_RESOLVED` | Case resolved (any outcome) |
| `CASE_REJECTED` | Dispute not upheld |
| `CASE_REOPENED` | Case reopened for review |
| `STATUS_CHANGED` | Generic status update |
| `CASE_RESOLVED_APPROVED` | Resolution approved, credit/refund initiated |

---

## SMTP Configuration

| Setting | Value |
|---|---|
| Server | smtp.office365.com |
| Port | 587 (STARTTLS) |
| Credentials | `SMTP_USERNAME` + `SMTP_PASSWORD` env vars |
| Demo redirect | All mail → `NOTIFICATION_EMAIL` env var |

---

## Deduplication

Emails are deduplicated per `case_id + notification_type` within 24 hours.
Override with `_skip_dedup: true` in context (used for batch document requests).

---

## Constraints

- Never use: Agent, AI, LLM, Fraud Score, Risk Score, Trust Score, Workflow Path
- Never mention "fraud" in INVESTIGATION_STARTED emails
- Always include case reference number
- Returns JSON `{"subject": "...", "body": "<html>..."}`

---

## Files

```
communication_agent/
├── agent.yaml       # Complete spec
├── config.py        # Reads agent.yaml
├── tools.py         # Email template + send helpers
├── state.py         # CommunicationAgentState
├── graph.py         # LangGraph StateGraph
├── __init__.py      # run_communication_agent() entry point
└── nodes/
    └── pipeline.py  # validate, generate, deliver nodes
```
