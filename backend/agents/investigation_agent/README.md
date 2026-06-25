# IIA — Investigation Intelligence Agent (Agent 2)

**Role**: Operational intelligence gathering, risk profiling, investigation planning
**Model**: Groq `llama-3.1-8b-instant`
**Version**: 1.2.0

---

## How it works

IIA receives ARIA's structured output and runs 4 DB tools to build a complete investigation brief. It reads **100% from DB** — no form data, no account_events.

**Pattern**: ReAct — LLM calls tools autonomously, then finalizes.

---

## Tools (all 100% DB)

| Tool | Tables Read | Purpose |
|---|---|---|
| `lookup_customer_history` | `dispute_cases`, `dispute_history` | Prior disputes, fraud rate, risk level |
| `check_merchant_risk` | `merchant_profiles`, `dispute_cases`, `dispute_history` | Merchant risk tier, complaints, blacklist |
| `find_duplicate_transaction` | `transactions`, `dispute_cases` | Duplicate detection (ID or amount+merchant+72h) |
| `lookup_related_cases` | `dispute_history`, `dispute_cases` | Historical resolution stats for same category |

---

## Output

Structured `InvestigationReport` including:
- `recommended_queue` (CRITICAL/FRAUD/HIGH_VALUE/MERCHANT/ATM/STANDARD)
- `investigation_complexity` (LOW/MEDIUM/HIGH/CRITICAL)
- `required_documents` (list of documents to request)
- `duplicate_found` + `related_case_id`
- `manual_review_required` + `manual_review_reason`

---

## Files

```
investigation_agent/
├── agent.yaml       # Complete spec
├── config.py        # Reads agent.yaml
├── tools.py         # 4 tools (all DB)
├── state.py         # InvestigationAgentState
├── graph.py         # LangGraph StateGraph
├── __init__.py      # run_investigation_agent() entry point
└── nodes/
    └── pipeline.py  # agent, finalize nodes
```
