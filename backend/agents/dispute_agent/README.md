# ARIA — Automated Resolution Intelligence Agent (Agent 1)

**Role**: Dispute intake, DB-first fraud scoring, classification, and initial triage
**Model**: Groq `llama-3.1-8b-instant`
**Version**: 2.0.0

---

## How it works

Form data is saved to `dispute_cases` DB **before** ARIA runs. ARIA reads from DB, not the raw form. Customer/transaction fields (email, phone, amount, merchant) are resolved from DB at submission time.

**Pipeline**: `validate → build_evidence → agent (LLM) → finalize`

All 3 tools run **server-side before the LLM call**:

| Tool | Data Source | Purpose |
|---|---|---|
| `assess_transaction_context` | Form timestamps/amounts | Amount tier, off-hours, CNP risk |
| `score_fraud_indicators` | `account_events` DB first, form fallback | Fraud signal scoring |
| `verify_evidence_match` | Uploaded document OCR text | Does evidence support the claim? |

---

## DB-First Fraud Scoring

`score_fraud_indicators` queries `account_events` table before trusting form answers.
DB-verified signals carry full weight. Form-only signals carry 60% weight.

**Verifiable from DB (`account_events`):**
- `SIM_SWAP_DETECTED`, `DEVICE_REGISTERED`, `MOBILE_NUMBER_CHANGED`
- `CARD_LOST_REPORTED`, `CARD_BLOCKED`
- `OTP_DELIVERED`, `CUSTOMER_CONTACT_LOGGED`, `UPI_COLLECT_REQUEST_RECEIVED`

**Form-only (60% weight — no DB equivalent):**
- `otp_shared`, `bank_impersonation`, `remote_access`, `screen_sharing`, `phishing_link`, `device_lost`

---

## Fraud Score Usage

The `Fraud Signal Level` output adjusts `confidence_score` in `finalize_node`:
- CRITICAL/HIGH + correct fraud category → **+0.15**
- MEDIUM + correct fraud category → **+0.08**
- CRITICAL/HIGH + wrong category → **-0.12**

This does NOT affect `fraud_probability` — that is computed by FRIA (Agent 4).

---

## Output

Structured `DisputeCase` JSON saved to `dispute_cases` table with:
- `dispute_category` (one of 9 categories)
- `fraud_suspicion` (boolean)
- `priority` (CRITICAL/HIGH/MEDIUM/LOW)
- `confidence_score` + `confidence_factors`
- `risk_tags` (server-stamped + LLM-generated, validated)
- `key_findings`, `case_summary`, `evidence_match`

---

## Files

```
dispute_agent/
├── agent.yaml       # Complete spec
├── config.py        # Reads agent.yaml
├── tools.py         # 3 tools with DB-first scoring
├── state.py         # DisputeAgentState
├── graph.py         # LangGraph StateGraph
├── __init__.py      # run_dispute_agent() entry point
└── nodes/
    └── pipeline.py  # validate, build_evidence, agent, finalize
```
