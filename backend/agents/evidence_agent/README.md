# EIA — Evidence Intelligence Agent (Agent 5)

**Role**: Evidence completeness audit, consistency validation, document gap analysis
**Model**: Groq `llama-3.1-8b-instant`
**Version**: 1.1.0

---

## How it works

EIA is activated by WOA when evidence gaps are detected. It reads from `dispute_cases` (which contains ARIA + IIA output) and evaluates whether available documentation is sufficient for the investigation.

**Pattern**: ReAct — LLM calls 5 tools, then finalizes.

**Data source**: `dispute_cases`, `document_requests`, `transactions` — 100% DB, no form data.

---

## Tools

| Tool | Tables Read | Purpose |
|---|---|---|
| `evaluate_evidence_completeness` | `dispute_cases`, `document_requests` | Score 0–100 of required docs present |
| `identify_missing_evidence` | `dispute_cases`, `document_requests` | List of unfulfilled required documents |
| `validate_evidence_consistency` | `dispute_cases`, `transactions` | Amount/merchant/date consistency check |
| `assess_evidence_strength` | `dispute_cases` | HIGH/MEDIUM/LOW strength from ARIA + IIA signals |
| `determine_next_document_request` | `dispute_cases`, `document_requests` | Next doc to request (avoids duplicates) |

---

## Output

Structured `EvidenceAssessment` including:
- `evidence_completeness` (0–100)
- `evidence_strength` (HIGH/MEDIUM/LOW)
- `evidence_consistent` (boolean) + `consistency_issues`
- `missing_documents` + `recommended_document_requests`
- `investigation_blocked` (boolean — true if missing evidence halts investigation)

---

## Files

```
evidence_agent/
├── agent.yaml       # Complete spec
├── config.py        # Reads agent.yaml
├── tools.py         # 5 tools (all read from dispute_cases)
├── state.py         # EvidenceAgentState
├── graph.py         # LangGraph StateGraph
├── __init__.py      # run_evidence_agent() entry point
└── nodes/
    └── pipeline.py  # agent, finalize nodes
```
