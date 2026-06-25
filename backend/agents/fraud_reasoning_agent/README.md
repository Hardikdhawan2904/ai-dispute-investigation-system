# FRIA — Fraud Reasoning Intelligence Agent (Agent 4)

**Role**: Channel-aware fraud detection — 48 parallel DB tools, LLM for narrative
**Model**: Groq `llama-3.1-8b-instant`
**Version**: 3.1.0

---

## How it works

FRIA runs **48 tools in parallel** before the LLM call. The LLM writes the fraud narrative. The server computes `fraud_probability` deterministically from tool results — the LLM never sets numbers.

**Pipeline**: `validate → build_context (48 parallel tools) → agent (LLM) → finalize`

**Form fields**: Narrative context only — zero impact on `fraud_probability`.
**All scoring**: From DB (transactions, dispute_cases, dispute_history, merchant_profiles, account_events, customer_devices, beneficiaries).

---

## Channel Routing

Transaction type determines which tool set runs:

| Channel | Transaction Types |
|---|---|
| UPI | UPI |
| INTERNET_BANKING | Net Banking, Mobile Banking, IMPS, NEFT, RTGS |
| CARD_POS | Debit Card, Credit Card |
| ATM | ATM, ATM Cash, Cash Withdrawal |

---

## Tool Groups (48 total)

| Group | Count | Channels | Key Signals |
|---|---|---|---|
| Core Digital | 7 | UPI + Internet Banking | Geovelocity (Haversine GPS), device fingerprint, KYC match |
| UPI | 5 | UPI only | Collect request, beneficiary velocity, UPI handle reputation |
| Internet Banking | 4 | IB only | Impossible login travel, device+large transfer, mobile change |
| Card POS | 15 | Card POS only | Card velocity, merchant compromise, card testing, MCC risk, **card_entry_mode** |
| ATM | 6 | ATM only | ATM velocity, geovelocity, SIM swap + ATM pattern |
| Universal | 6 | All (capped 0.60) | Prior fraud victim, mule account, linked fraud network |
| Bank-Verified | 5 | All | ATO sequence from account_events, device trust from customer_devices |

---

## New DB Columns / Tables (added in v3.x)

- `transactions.card_entry_mode` — SWIPE/CHIP_INSERT/CONTACTLESS_TAP/MANUAL_ENTRY (Card POS only)
- `transactions.latitude`, `transactions.longitude` — GPS for digital channels only
- `account_events` — 5,705 bank security events across 1,000 customers
- `customer_devices` — 7,494 registered devices
- `beneficiaries` — 9,347 known payees

---

## Scoring Rules

- `fraud_probability` range: 0.00–1.00 (server-computed, not LLM)
- Universal tool contribution: capped at **0.60**
- Risk levels: LOW <0.15, MEDIUM <0.40, HIGH <0.75, CRITICAL ≥0.75
- CARD_POS + ATM: `device_id = NULL` (POS terminals are merchant devices, not customer devices)

---

## Files

```
fraud_reasoning_agent/
├── agent.yaml       # Complete spec (v3.1.0, 48 tools documented)
├── config.py        # Reads agent.yaml
├── tools.py         # 48 tools + TOOL_REGISTRY
├── state.py         # FraudReasoningAgentState
├── graph.py         # LangGraph StateGraph
├── __init__.py      # run_fraud_reasoning_agent() entry point
└── nodes/
    └── pipeline.py  # validate, build_context, agent, finalize
```
