# Customer Communication Agent (CCA) — Agent 6

**Role**: Generates professional, customer-friendly HTML email notifications for dispute lifecycle events.  
**Model**: Groq `llama-3.1-8b-instant` (configured for LLM generation; template-driven builder utilized for secure delivery)  
**Entry Point**: `validate`  
**Framework**: LangGraph (StateGraph)  

---

## 🎯 Purpose

CCA bridges the gap between internal technical analysis and customer engagement. It translates case state changes, specialist reviews, and investigator findings into reassuring, clear, and professional notifications. 

To maintain banking compliance and account security, CCA operates under strict privacy constraints:
- Translates risk terms into user-friendly security verbiage (e.g., hiding "fraud score" or "suspicious" flags).
- Ensures no AI jargon, LLM metrics, internal notes, or route traces are ever leaked to the customer.
- Always inserts tracking links to direct users to the self-service dispute tracking page.

---

## 📋 Workflow

```
       ┌────────────────────────┐
       │   Workflow Event /     │
       │   Analyst Status Change│
       └───────────┬────────────┘
                   │
           [validate Node]
    (Check inputs, stamp start time,
     resolve recipient email address)
                   │
           [generate Node]
    (Construct subject & full HTML
     body via secure styling template)
                   │
            [deliver Node]
    (Deliver email SMTP & persist logs
     in communication_logs DB table)
                   │
                  END
```

CCA runs asynchronously (`trigger_communication_async`) and is wrapped in standard try/catch blocks. This ensures that any SMTP timeouts or network hiccups in delivery never block or degrade the primary dispute processing pipeline.

---

## ── Agent Persona & Constraints ──

* **Role**: Customer Communications Specialist at SecureBank.
* **Goal**: Deliver clear, timely, and empathetic transaction dispute updates.
* **Tone**: Professional, reassuring, and customer-centric.
* **Constraints**:
  - **NEVER** expose internal terms: *Agent, AI, LLM, Fraud Score, Risk Score, Trust Score, Workflow Path, Investigation Details*.
  - **FRAUD_REVIEW_STARTED Policy**: Never use the words "fraud" or "suspicious". Instead, communicate that the case is undergoing *"additional security verification"* or *"enhanced security review"*.
  - Every notification email must terminate with a valid tracking CTA button pointing to SecureBank's Dispute Tracker.
  - Return clean HTML structures formatted with inline styles (matching branding guidelines: deep navy headers `#0F2A4A`, slate text `#4A5568`, and card container shapes).

---

## ── LangGraph Pipeline Flow ──

CCA's execution pipeline is composed of the following sequential nodes:
1. **`validate`**: Sanitizes inputs (`case_id` and `notification_type`), sets default fallbacks if types mismatch, and locates the user's registered email destination.
2. **`generate`**: Generates matching email subject headings and inline-styled HTML blocks using `build_html_email` in [communication_prompts.py](file:///d:/Transaction_dispute_agent/ai-dispute-resolution-system/backend/prompts/communication_prompts.py).
3. **`deliver`**: Delivers the prepared message payload via SMTP TLS transport and records the outcome directly in the database logs.

---

## ── State Schema ──

The agent manages its execution context using `CommunicationAgentState` defined in [state.py](file:///d:/Transaction_dispute_agent/ai-dispute-resolution-system/backend/agents/communication_agent/state.py):
* `case_id`: The system-assigned unique Case ID.
* `notification_type`: The token keyword signifying the target lifecycle milestone.
* `case_data`: Safe key-value subset of customer attributes (name, transaction amount, merchant name).
* `context`: Additional dynamic arguments (e.g. lists of requested documents, resolution notes, status messages).
* `subject`: Finalized email subject line.
* `body`: Inline-styled HTML content.
* `recipient`: Destination email address.
* `status`: Current delivery state (`PENDING` | `SENT` | `FAILED`).
* `error`: Holds failure logs or traceback details if delivery fails.
* `agent_start_time`: Stamped at intake to measure latency.

---

## ── Notification Templates ──

The system defines 7 canonical templates within [communication_prompts.py](file:///d:/Transaction_dispute_agent/ai-dispute-resolution-system/backend/prompts/communication_prompts.py):

| Notification Type | Trigger Event | Customer Headline |
| :--- | :--- | :--- |
| `CASE_RECEIVED` | Initial claim ingestion | Your dispute has been received |
| `INVESTIGATION_STARTED` | Specialist starts active review | Your case is now under active investigation |
| `DOCUMENT_REQUESTED` | Missing documents required | Additional documents are required |
| `FRAUD_REVIEW_STARTED` | Fraud detection rules trigger | Additional security verification in progress |
| `EVIDENCE_REVIEW_COMPLETED`| Uploaded files successfully parsed | Your documents have been reviewed |
| `CASE_RESOLVED` | Dispute finalized (refunded/rejected)| Your dispute has been resolved |
| `STATUS_CHANGED` | General state fallback update | Your dispute status has been updated |

---

## ── Invocation & Calling Context ──

* **Function**: `run_communication_agent(case_id: str, notification_type: str, case_data: dict, context: Optional[dict] = None) -> dict`
* **Module**: [__init__.py](file:///d:/Transaction_dispute_agent/ai-dispute-resolution-system/backend/agents/communication_agent/__init__.py)
* **Callers**:
  * [communication_service.py](file:///d:/Transaction_dispute_agent/ai-dispute-resolution-system/backend/services/communication_service.py) -> handles database interaction and async thread execution.
  * [dispute_workflow.py](file:///d:/Transaction_dispute_agent/ai-dispute-resolution-system/backend/workflows/dispute_workflow.py) -> triggers intermediate verification, investigation, and review completions.
  * [dispute_service.py](file:///d:/Transaction_dispute_agent/ai-dispute-resolution-system/backend/services/dispute_service.py) -> notifies upon initial ingestion and analyst status transitions.
  * [communications.py (API Routes)](file:///d:/Transaction_dispute_agent/ai-dispute-resolution-system/backend/api/routes/communications.py) -> manual click-to-notify analyst triggers.
