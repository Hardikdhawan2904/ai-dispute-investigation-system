# WOA — Workflow Orchestration Agent (Agent 3)

**Role**: Workflow coordinator, specialist agent routing, escalation planning
**Model**: Groq `llama-3.1-8b-instant`
**Version**: 1.1.0

---

## How it works

WOA reads ARIA + IIA output from `dispute_cases` and decides which specialist agents run, in what order, and whether escalation is needed. It coordinates — it does not investigate.

**Pattern**: ReAct — LLM calls 6 tools, then generates workflow plan.

**Data source**: `dispute_cases` only — 100% DB, no form data.

---

## Tools

| Tool | Purpose |
|---|---|
| `evaluate_case_complexity` | LOW/MEDIUM/HIGH/CRITICAL from amount, fraud flags, IIA complexity |
| `determine_required_agents` | Which specialist agents must run |
| `recommend_workflow_path` | Ordered execution sequence |
| `assess_escalation_need` | Escalation level and reason |
| `estimate_workload` | Hours + analyst seniority |
| `determine_next_execution_step` | Next unexecuted agent (for re-analysis continuity) |

---

## Routing Rules

| Condition | Agent |
|---|---|
| Unauthorized Transaction, fraud_suspicion=true, Friendly Fraud | FRAUD_AGENT |
| Merchant Dispute, Refund Not Received, Product Not Received, Subscription Abuse, Duplicate Transaction | MERCHANT_AGENT |
| evidence_match ≠ true, required_documents present, ATM Cash Issue, Other | EVIDENCE_AGENT |

> **COMPLIANCE_AGENT removed.** High-risk tags (VELOCITY_BREACH, OTP_COMPROMISED, DEVICE_MISMATCH, MERCHANT_BLACKLISTED) now trigger **escalation** — not a separate agent.

---

## Output

Structured `WorkflowPlan` including:
- `required_agents`, `workflow_path`, `next_agent`
- `escalation_required`, `escalation_level`
- `workflow_reasoning` (factual past-tense rationale)
- `analyst_level`, `estimated_investigation_hours`

---

## Files

```
orchestration_agent/
├── agent.yaml       # Complete spec
├── config.py        # Reads agent.yaml
├── tools.py         # 6 tools (all read from dispute_cases)
├── state.py         # OrchestrationAgentState
├── graph.py         # LangGraph StateGraph
├── __init__.py      # run_orchestration_agent() entry point
└── nodes/
    └── pipeline.py  # agent, finalize nodes
```
