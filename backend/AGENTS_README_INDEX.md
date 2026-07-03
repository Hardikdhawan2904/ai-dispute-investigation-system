# BFSI Dispute Investigation Platform - Agent Documentation Index

**Last Updated**: 2026-07-03  
**System Version**: 1.0

---

## 📚 Quick Navigation

### Main Documentation Files

| Document | Purpose | Location |
|----------|---------|----------|
| **Comprehensive Guide** | Full system architecture, all agents, workflows, error handling | [AGENTS_COMPREHENSIVE_GUIDE.md](AGENTS_COMPREHENSIVE_GUIDE.md) |
| **Agent 1: ARIA** | Dispute Understanding Agent — intake & classification | [agents/dispute_agent/README.md](agents/dispute_agent/README.md) |
| **Agent 2: IIA** | Investigation Intelligence Agent — historical analysis | [agents/investigation_agent/README.md](agents/investigation_agent/README.md) |
| **Agent 3: WOA** | Workflow Orchestration Agent — case routing | [agents/orchestration_agent/README.md](agents/orchestration_agent/README.md) |
| **Agent 4: FRIA** | Fraud Reasoning Intelligence Agent — 48 fraud tools | [agents/fraud_reasoning_agent/README.md](agents/fraud_reasoning_agent/README.md) |
| **Agent 5: EIA** | Evidence Intelligence Agent — document verification | [agents/evidence_agent/README.md](agents/evidence_agent/README.md) |
| **Agent 6: CCA** | Customer Communication Agent — customer notification | [agents/communication_agent/README.md](agents/communication_agent/README.md) |

---

## 🎯 Agent Overview

### Agent 1: ARIA - Dispute Understanding Agent
**Role**: First contact point — dispute classification & DB-first fraud scoring  
**Input**: Dispute data (already saved to `dispute_cases` DB before ARIA runs)  
**Output**: `dispute_category`, `fraud_suspicion`, `confidence_score`, `risk_tags`, `key_findings`, `case_summary`  
**Tools** (all pre-computed server-side before LLM call):
- `assess_transaction_context()` — RBI liability tier, off-hours risk, CNP flags
- `score_fraud_indicators()` — DB-first fraud scoring (account_events → form fallback at 60% weight)
- `verify_evidence_match()` — OCR document text vs claimed merchant/amount
**Key Metrics**: 
- Amount tier (RBI Liability Tiers)
- Off-hours detection (11 PM–5 AM)
- Confidence score (0–1)

> **Note**: `priority` is **not** output by ARIA. It is computed post-workflow by `services/priority_engine.py`.

**Quick Start**: [Read ARIA README](agents/dispute_agent/README.md)

---

### Agent 2: IIA - Investigation Intelligence Agent
**Role**: Historical analysis & risk profiling  
**Input**: ARIA output (dispute_category, fraud_suspicion, confidence_score)  
**Output**: `investigation_plan`, `investigation_complexity`, `required_documents`, `recommended_queue`, `confidence_score`  
**Data**: 529+ historical disputes + 11,512 transactions  
**Tools** (all DB — no form data): 
- `lookup_customer_history()` — Customer risk profile from dispute_cases + dispute_history
- `check_merchant_risk()` — Merchant reputation from merchant_profiles
- `find_duplicate_transaction()` — Duplicate claims within 72-hour window
- `lookup_related_cases()` — Precedent cases & resolution history
**Key Metrics**: 
- Customer fraud rate (%)
- Merchant complaint count
- Duplicate check status
- Investigation complexity (LOW/MEDIUM/HIGH/CRITICAL)

**Quick Start**: [Read IIA README](agents/investigation_agent/README.md)

---

### Agent 3: WOA - Workflow Orchestration Agent
**Role**: Single routing authority — decides which specialist agents run and in what order  
**Input**: ARIA + IIA output (read from `dispute_cases` DB)  
**Output**: `workflow_plan`, `required_agents`, `workflow_complexity`, `escalation_required`, `analyst_level`, `estimated_investigation_hours`  
**Tools** (all read from `dispute_cases` only — 100% DB):
- `evaluate_case_complexity()` — Complexity tier
- `determine_required_agents()` — Routes to FRAUD_AGENT / EVIDENCE_AGENT / MERCHANT_AGENT only
- `recommend_workflow_path()` — Execution sequence
- `assess_escalation_need()` — Escalation flag (high-risk tags → senior analyst, not compliance agent)
- `estimate_workload()` — Analyst capacity
- `determine_next_execution_step()` — Dependency tracking
**Routing logic**:
- `FRAUD_AGENT` — Unauthorized Transaction, Friendly Fraud, fraud_suspicion=true
- `EVIDENCE_AGENT` — Evidence gaps, ATM Cash Issue, Other
- `MERCHANT_AGENT` — Merchant Dispute, Refund Not Received, Product Not Received, Subscription Abuse, Duplicate Transaction

> Queue assignment, SLA deadline, and analyst assignment are **not** WOA outputs — they are computed by `queue_assignment_service.py` and `sla_service.py` post-workflow.

**Quick Start**: [Read WOA README](agents/orchestration_agent/README.md)

---

### Agent 4: FRIA - Fraud Reasoning Intelligence Agent
**Role**: Channel-aware fraud detection — 48 DB tools run in parallel, LLM generates narrative only  
**Input**: Case data from `dispute_cases` DB  
**Output**: `fraud_probability`, `fraud_risk_level`, `user_trust_score`, `behavioral_risk_score`, `fraud_reasoning`, `tool_signals`  
**Tools**: **48 tools across 4 channels** — all pre-executed server-side via `ThreadPoolExecutor`

| Channel | Tools |
|---------|-------|
| Core Digital (UPI + Internet Banking) | 7 tools |
| UPI-Specific | 5 tools |
| Internet Banking | 4 tools |
| Card POS | 15 tools |
| ATM | 6 tools |
| Universal (all channels, capped 0.60) | 11 tools |

**Key Metrics**: 
- Fraud probability (0–1, deterministic server-side — LLM never sets numbers)
- Risk level (LOW < 0.15 / MEDIUM < 0.40 / HIGH < 0.75 / CRITICAL ≥ 0.75)
- Channel-specific anomaly flags

**Quick Start**: [Read FRIA README](agents/fraud_reasoning_agent/README.md)

---

### Agent 5: EIA - Evidence Intelligence Agent
**Role**: Evidence completeness audit, consistency validation, document gap analysis  
**Input**: Case data from `dispute_cases` + `document_requests` + `transactions` DB  
**Output**: `evidence_completeness`, `evidence_strength`, `missing_documents`, `investigation_blocked`, `recommended_document_requests`  
**Tools**: 
- `evaluate_evidence_completeness()` — Required docs vs fulfilled requests
- `identify_missing_evidence()` — Gap analysis
- `validate_evidence_consistency()` — Amount/merchant/date vs transaction record
- `assess_evidence_strength()` — Weighted: ARIA verdict + completeness + IIA data quality
- `determine_next_document_request()` — Next formal request (deduplicates pending)
**Key Metrics**: 
- Completeness % (0–100)
- Evidence strength (HIGH/MEDIUM/LOW)

**Quick Start**: [Read EIA README](agents/evidence_agent/README.md)

---

### Agent 6: CCA - Customer Communication Agent
**Role**: Customer-facing notification delivery — fires asynchronously, never blocks workflow  
**Input**: Case event type + case data (case_id, notification_type, recipient, context)  
**Output**: HTML email delivered via Gmail SMTP; record saved to `communication_logs`  
**Pipeline**: `validate → generate (LLM) → deliver (SMTP)`  
**Notification types** (6 customer-facing, 2 internal-suppressed):
- CASE_RECEIVED, INVESTIGATION_STARTED, DOCUMENT_REQUESTED, CASE_RESOLVED, STATUS_CHANGED, DOCUMENTS_RECEIVED
- FRAUD_REVIEW_STARTED *(suppressed)*, EVIDENCE_REVIEW_COMPLETED *(suppressed)*
**Key Metrics**:
- Successful deliveries (SENT / FAILED)
- Deduplication: one-shot types fire at most once per case per 24-hour window

**Quick Start**: [Read CCA README](agents/communication_agent/README.md)

---

## 📊 Data Flow Architecture

```
CUSTOMER DISPUTE SUBMISSION
         │  (saved to dispute_cases DB before any agent runs)
         ▼
    ┌─────────────────────┐
    │  Agent 1: ARIA      │ Classification
    │  fraud_suspicion    │ DB-first fraud scoring
    │  confidence, tags   │ Evidence match
    └─────────┬───────────┘
              │  (async) ──────────────────────→ Agent 6: CCA (CASE_RECEIVED email)
              ▼
    ┌─────────────────────┐
    │  Agent 2: IIA       │ History Analysis
    │  investigation_plan │ Risk Profiling
    └─────────┬───────────┘
              │  (async) ──────────────────────→ Agent 6: CCA (INVESTIGATION_STARTED email)
              ▼
    ┌─────────────────────┐
    │  Agent 3: WOA       │ Case Orchestration
    │  workflow_plan      │ Routing Decisions
    └─────────┬───────────┘
              │
        ┌─────┴─────┐
        ▼           ▼
    ┌────────┐  ┌──────────┐
    │Agent 4 │  │ Agent 5  │
    │  FRIA  │  │   EIA    │
    │ Fraud  │  │Evidence  │
    └────┬───┘  └────┬─────┘
         │           │
         └─────┬─────┘
               ▼
      INVESTIGATION QUEUE
     (Fraud / Merchant / Evidence)
               │
               ▼
      Post-workflow services:
      priority_engine.py → priority
      queue_assignment_service.py → assigned_queue
      sla_service.py → sla_deadline
```

---

## 🔍 Key Concepts

### RBI Liability Tiers (Agent 1)
- **₹0–10K**: Standard processing
- **₹10K–50K**: Heightened scrutiny
- **₹50K–2L**: Senior officer escalation
- **₹2L–10L**: Mandatory investigation
- **>₹10L**: Executive-level review

### Fraud Scoring Architecture

**ARIA (Agent 1)** — `score_fraud_indicators`: DB-first scoring
- Bank-verified events from `account_events` → full weight
- Form-only unverifiable claims (otp_shared, bank_impersonation, remote_access) → 60% weight
- Output: fraud signal level (CRITICAL/HIGH/MEDIUM/LOW) used to adjust `confidence_score`

**FRIA (Agent 4)** — 48 tools, deterministic server-side scores:
- All numeric fraud scores computed from DB — LLM generates narrative only
- Channel-specific tools contribute on top of universal tools (capped at 0.60)
- Social engineering signals (otp_shared, bank_impersonation) appear in narrative only — never affect `fraud_probability`

### Investigation Complexity (Agent 2)
- **LOW**: Simple refund claims, first-time customers
- **MEDIUM**: Moderate fraud signals, some dispute history
- **HIGH**: High-value disputes, multiple risk signals
- **CRITICAL**: Very high value, identity theft patterns

### Evidence Completeness (Agent 5)
- **>80%**: HIGH (proceeding with confidence)
- **50–80%**: MEDIUM (may request additional docs)
- **<50%**: LOW (blocks investigation until complete)

### Case Complexity (Agent 3)
- **LOW**: Amount <₹10K, no fraud, single category
- **MEDIUM**: Amount ₹10K–₹2L, moderate signals
- **HIGH**: Amount >₹2L OR multiple risk tags
- **CRITICAL**: Amount >₹10L OR identity theft indicators

---

## ⚙️ Configuration Files

### Agent Configuration (agent.yaml)
Each agent has its own `agent.yaml` containing full spec: role, goal, LLM config, LangGraph pipeline, tools, output schema.

**Locations**:
- Agent 1: [agents/dispute_agent/agent.yaml](agents/dispute_agent/agent.yaml)
- Agent 2: [agents/investigation_agent/agent.yaml](agents/investigation_agent/agent.yaml)
- Agent 3: [agents/orchestration_agent/agent.yaml](agents/orchestration_agent/agent.yaml)
- Agent 4: [agents/fraud_reasoning_agent/agent.yaml](agents/fraud_reasoning_agent/agent.yaml)
- Agent 5: [agents/evidence_agent/agent.yaml](agents/evidence_agent/agent.yaml)
- Agent 6: [agents/communication_agent/agent.yaml](agents/communication_agent/agent.yaml)

---

## 📈 Metrics & Observability

### Monitoring Dashboard Queries
```sql
SELECT COUNT(*) FROM dispute_cases;                          -- Total cases processed
SELECT AVG(updated_at - created_at) FROM dispute_cases;     -- Average processing time
SELECT COUNT(*) FROM dispute_cases WHERE fraud_suspicion=true; -- Fraud detection rate
SELECT COUNT(*) FROM dispute_cases WHERE priority='CRITICAL';  -- High-priority cases
SELECT AVG(confidence_score) FROM dispute_cases;            -- Average confidence score
```

---

## 🚨 Error Handling

### Common Scenarios

| Scenario | Handler | Fallback |
|----------|---------|----------|
| Database connection fails | Retry 3x with backoff | Set fallback_mode=true, requires_manual_review=true |
| LLM timeout | Return after 30s | Use deterministic heuristics from tool results |
| Missing required field | Validate input first | Return 400 error before agent execution |
| Document upload fails | Log error, continue | Flag in document_requests as pending |
| Tool execution error | Catch exception | Return conservative estimate, log warning |

---

## 📖 Usage Examples

### Example 1: Unauthorized UPI Transaction
```
Input:
  customer_comment: "I didn't authorize this transaction"
  otp_shared: true
  fraud_selected: true
  amount: ₹50,000
  time: 23:30 (off-hours)

Agent 1 (ARIA) Output:
  dispute_category: "Unauthorized Transaction"
  fraud_suspicion: true
  confidence_score: 0.92
  
Agent 2 (IIA) Output:
  investigation_complexity: HIGH
  required_documents: [UPI_LOG, OTP_RECORDS, DEVICE_HISTORY]
  
Agent 3 (WOA) Output:
  workflow_plan: [FRAUD_AGENT, EVIDENCE_AGENT]
  workflow_complexity: HIGH
  escalation_required: true
  analyst_level: SENIOR

Post-workflow (services):
  priority: CRITICAL                    ← priority_engine.py
  assigned_queue: FRAUD_QUEUE           ← queue_assignment_service.py
  sla_deadline: +8h                     ← sla_service.py

Agent 4 (FRIA) Output:
  fraud_probability: 0.85
  fraud_risk_level: CRITICAL
  
Agent 5 (EIA) Output:
  evidence_strength: HIGH
  evidence_completeness: 90
```

### Example 2: Refund Not Received
```
Input:
  customer_comment: "I paid but refund never arrived"
  fraud_selected: false
  amount: ₹5,000
  merchant: Raymond

Agent 1 (ARIA) Output:
  dispute_category: "Refund Not Received"
  fraud_suspicion: false
  confidence_score: 0.55
  
Agent 2 (IIA) Output:
  investigation_complexity: LOW
  required_documents: [PURCHASE_PROOF, PAYMENT_RECEIPT]
  
Agent 3 (WOA) Output:
  workflow_plan: [MERCHANT_AGENT]
  workflow_complexity: LOW
  analyst_level: JUNIOR

Post-workflow (services):
  priority: MEDIUM                      ← priority_engine.py
  assigned_queue: MERCHANT_QUEUE        ← queue_assignment_service.py
```

---

## 🔗 Related Documents

- [Root README](../README.md) — Primary system documentation (authoritative)
- [Deployment Guide](../README.md#setup)

---

## 📞 Support

For questions about specific agents or the system architecture:

1. **Agent-specific issues**: Check the agent's individual README
2. **System architecture**: See the root [README.md](../README.md) (authoritative) or [AGENTS_COMPREHENSIVE_GUIDE.md](AGENTS_COMPREHENSIVE_GUIDE.md)
3. **Data dependencies**: Review the Data Flow section above
4. **Configuration**: Check agent.yaml files
5. **Error investigation**: Search `logs/` directory for agent_name
