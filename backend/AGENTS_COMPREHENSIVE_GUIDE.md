# BFSI Dispute Resolution System - Agent Architecture & Operations Guide

**System Version**: 1.0  
**Last Updated**: 2026-06-14  
**Framework**: LangGraph (Multi-Agent ReAct Pattern)

---

## 📑 Table of Contents

1. [System Overview](#system-overview)
2. [Agent 1: Dispute Understanding Agent (ARIA)](#agent-1-aria)
3. [Agent 2: Investigation Intelligence Agent (IIA)](#agent-2-iia)
4. [Agent 3: Fraud Reasoning Agent (FRA)](#agent-3-fra)
5. [Agent 4: Evidence Intelligence Agent (EIA)](#agent-4-eia)
6. [Agent 5: Orchestration Workflow Agent (WOA)](#agent-5-woa)
7. [Data Flow & Dependencies](#data-flow--dependencies)
8. [Error Handling & Fallbacks](#error-handling--fallbacks)

---

# System Overview

## Architecture

```
CUSTOMER DISPUTE SUBMISSION
         │
         ▼
    ┌────────────────────────────┐
    │  Agent 1: ARIA             │ Dispute Classification
    │  (Intake & Fraud Scoring)  │ + Risk Baseline
    └────────────┬───────────────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │  Agent 2: IIA              │ Historical Analysis
    │  (History & Plan)          │ + Profile
    └────────────┬───────────────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │  Agent 5: WOA              │ Orchestration
    │  (Workflow Coordinator)    │ Case Routing
    └────────────┬───────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
   ┌──────────┐     ┌──────────┐
   │ Agent 4  │     │ Agent 3  │
   │ EIA      │     │ FRA      │
   │(Evidence)│     │(Fraud)   │
   └────┬─────┘     └────┬─────┘
        │                │
        └────────┬───────┘
                 ▼
          structured_output
                 │
                 ▼
                END
```

---

# Agent 1: ARIA
## Dispute Understanding Agent (ARIA)

**Role**: First intake point — dispute classification & fraud risk scoring  
**Model**: Groq (llama-3.1-8b-instant)  
**Execution**: ReAct loop (max 3 iterations)

### Input

```
customer_comment:     "I didn't authorize this transaction. My card was stolen."
fraud_selected:       true
transaction_id:       "TXN-00001947"
transaction_type:     "UPI"
merchant:            "Merchant_27"
amount:              34189.23
transaction_date:    "2025-08-01"
transaction_time:    "17:36"

OPTIONAL FLAGS:
otp_shared:          true         (HIGH-RISK: OTP shared with third party)
bank_impersonation:  false
sim_swap_suspected:  false
remote_access:       false
phishing_link:       false
```

### Workflow

```
INPUT
  │
  ▼
[VALIDATE NODE]
  • Assign case_id (e.g., CASE-000012)
  • Verify mandatory fields
  │
  ▼
[BUILD_EVIDENCE NODE]
  • Run: assess_transaction_context()
    → Amount tier, off-hours, CNP risk, international merchant
  • Run: score_fraud_indicators()
    → Keyword analysis, OTP patterns, fraud probability
  • Format evidence block for LLM
  │
  ▼
[AGENT NODE - LLM ReAct Loop]
  Round 1:
    "I'll analyze this transaction's context..."
    Action: Call assess_transaction_context()
    Result: "Composite Risk: MEDIUM (amount ₹34K + UPI)"
  
  Round 2:
    "Now let me score the fraud signals..."
    Action: Call score_fraud_indicators()
    Result: "Score: 9.5 (CRITICAL) — OTP shared + social engineering pattern"
  
  Round 3:
    Synthesize results → Output classification
  │
  ▼
[FINALIZE NODE]
  • Parse LLM classification JSON
  • Add metadata (timestamp, duration, tools_used)
  • Store in dispute_cases table
```

### Parameters Checked

| Parameter | Check | Output |
|-----------|-------|--------|
| **amount** | RBI liability tiers | Tier: LOW/STANDARD/ELEVATED/HIGH/CRITICAL |
| **transaction_time** | Off-hours (11PM-5AM) | Off-hours risk: Yes/No |
| **transaction_type** | Card-Not-Present risk | CNP risk: Yes/No (+2 points) |
| **merchant** | International flag | International: Yes/No (+2 points) |
| **customer_comment** | Fraud keyword scan | Keywords: [list], Score: +2 per match |
| **otp_shared** | Tier-1 fraud indicator | Fraud Score: +8.0 (alone = HIGH) |
| **otp_received + denial** | Combination signal | Score: +3.5 |
| **bank_impersonation** | Tier-1 indicator | Score: +8.0 (vishing attack) |
| **sim_swap_suspected** | Tier-1 indicator | Score: +8.0 (telecom account takeover) |
| **remote_access** | Tier-2 indicator | Score: +4.0 (device compromise) |
| **phishing_link** | Tier-2 indicator | Score: +4.0 (credential theft) |
| **card_lost / device_lost** | Tier-3 indicators | Score: +2.5 each |

### Output

```json
{
  "case_id": "CASE-000012",
  "dispute_category": "Unauthorized Transaction",
  "priority": "CRITICAL",
  "confidence_score": 0.92,
  "fraud_suspicion": true,
  "fraud_selected": true,
  "risk_tags": [
    "OTP_SHARED",
    "SOCIAL_ENGINEERING",
    "UNAUTHORIZED_UPI",
    "AMOUNT_ELEVATED"
  ],
  "structured_reasoning": {
    "transaction_risk": "MEDIUM (amount ₹34,189 + UPI channel)",
    "fraud_indicators": "CRITICAL (OTP shared + classic social engineering)",
    "confidence": "92% (high confidence in unauthorized transaction classification)"
  },
  "status": "Dispute Raised",
  "workflow_ready": false,
  "requires_manual_review": false,
  "evidence_match": true,
  "current_stage": "intake",
  "created_at": "2026-06-14T11:46:29Z"
}
```

### Fraud Probability Scoring

```
TIER-1 INDICATORS (each alone = HIGH signal):
  • OTP shared with third party:           +8.0
  • Bank impersonation (vishing):          +8.0
  • SIM swap suspected:                    +8.0

TIER-2 INDICATORS (medium certainty):
  • Remote access tool installed:          +4.0
  • Phishing link clicked:                 +4.0

TIER-3 INDICATORS (physical threat):
  • Card lost/stolen:                      +2.5
  • Device lost:                           +2.5

KEYWORD SCAN:
  • Each fraud keyword match:              +2.0 (capped at 6.0 total)
  Keywords: "didn't do", "unauthorized", "hacked", "stolen", "scam"

COMBINATION SIGNALS:
  • OTP received + customer denial:        +3.5

FINAL THRESHOLDS:
  Score >= 8.0   → CRITICAL fraud risk
  Score 5-8      → HIGH fraud risk
  Score 2-5      → MEDIUM fraud risk
  Score < 2      → LOW fraud risk
```

---

# Agent 2: IIA
## Investigation Intelligence Agent (IIA)

**Role**: Historical analysis & risk profiling  
**Model**: Groq (llama-3.1-8b-instant)  
**Data Sources**: 526+ historical disputes + 11,000+ transactions  
**Execution**: ReAct loop (5 tools available)

### Workflow

```
RECEIVES Agent 1 OUTPUT
        │
        ▼
[AGENT NODE - ReAct Loop]
  LLM decides which tools to call:
  
  Action 1: lookup_customer_history(customer_id)
    → Total disputes, fraud rate, last dispute, resolution history
  
  Action 2: check_merchant_risk(merchant_name)
    → Merchant complaints, fraud rate, blacklist status
  
  Action 3: detect_velocity_patterns(customer_id)
    → 24h transaction count, duplicate charges
  
  Action 4: analyze_transaction_anomalies(customer_id, time)
    → Off-hours flag, spending deviation
  
  Action 5: cross_reference_dispute_history(category, merchant)
    → Similar historical disputes, resolution outcomes
        │
        ▼
[FINALIZE NODE]
  • Synthesize tool results
  • Produce investigation_plan[]
  • Compute investigation_complexity
  • Generate investigation_confidence score
```

### Parameters Checked

| Tool | Checks | Output |
|------|--------|--------|
| **lookup_customer_history** | Total disputes, fraud claims, fraud rate, last dispute days, resolution history | Customer risk: LOW/MEDIUM/HIGH |
| **check_merchant_risk** | Prior complaints, fraud rate, blacklist patterns, resolution outcomes | Merchant risk: LOW/MEDIUM/HIGH |
| **detect_velocity_patterns** | 24h transaction count, duplicate charges, merchant velocity | Velocity breach: Yes/No |
| **analyze_transaction_anomalies** | Off-hours (11PM-5AM), spending Z-score, geovelocity | Anomalies: [list] |
| **cross_reference_dispute_history** | Similar cases, historical resolutions, investigation methods | Recommended path: [actions] |

### Output

```json
{
  "investigation_complexity": "HIGH",
  "investigation_confidence": 0.82,
  "customer_history": {
    "total_disputes": 12,
    "fraud_claims": 3,
    "fraud_rate": 0.25,
    "risk_level": "LOW",
    "assessment": "Normal dispute pattern"
  },
  "merchant_risk": {
    "name": "Merchant_27",
    "total_complaints": 2,
    "fraud_rate": 0.0,
    "risk_level": "LOW"
  },
  "transaction_patterns": {
    "velocity_breach": false,
    "off_hours_flag": false,
    "spending_anomaly": false
  },
  "investigation_plan": {
    "required_documents": [
      "UPI_AUTHORIZATION_LOG",
      "OTP_VERIFICATION_RECORDS",
      "DEVICE_LOGIN_HISTORY"
    ],
    "investigation_focus": [
      "Verify if OTP was actually sent",
      "Check device from which transaction initiated",
      "Cross-reference with login history"
    ],
    "estimated_resolution_days": 7
  },
  "similar_disputes": [
    {
      "case_id": "CASE-000005",
      "category": "Unauthorized Transaction",
      "resolved_in_favor_of": "customer"
    }
  ]
}
```

---

# Agent 3: WOA
## Workflow Orchestration Agent (WOA)

**Role**: Coordinator — routes cases to specialist agents & final disposition  
**Model**: Groq (llama-3.1-8b-instant)  
**Execution**: ReAct loop (6 deterministic tools pre-computed before LLM)

### Workflow

```
RECEIVES AGENT 1, 2 OUTPUTS
         │
         ▼
[PRE-EXECUTION NODE]
  Execute 6 routing tools:
  
  Tool 1: evaluate_case_complexity()
    → Compute complexity: LOW/MEDIUM/HIGH/CRITICAL
    → Based on amount, fraud signals, risk tags, Agent 2 complexity
  
  Tool 2: determine_required_agents()
    → Check fraud_suspicion, category, evidence gaps, risk tags
    → Routing rules determine specialists
  
  Tool 3: recommend_workflow_path()
    → Order specialist agents by dependency
    → FRAUD_AGENT first (fraud informs all others)
    → EVIDENCE_AGENT before MERCHANT_AGENT
  
  Tool 4: assess_escalation_need()
    → Determine manager escalation required
  
  Tool 5: estimate_workload()
    → Recommends analyst seniority + estimated effort hours
  
  Tool 6: determine_next_execution_step()
    → Track execution completion and remaining steps
         │
         ▼
[AGENT NODE - LLM]
  Receives pre-computed tool results
  Synthesizes final workflow plan
         │
         ▼
[FINALIZE NODE]
  • Output workflow_plan
  • Set assigned_queue, assigned_analyst
  • Set SLA deadline
  • Store in dispute_cases table
```

### Routing Rules

```
IF fraud_suspicion OR fraud_selected OR category IN ["Unauthorized", "Friendly Fraud"]:
  → REQUIRE FRAUD_AGENT
  
IF evidence_match != true OR required_documents present OR category IN ["ATM Cash", "Other"]:
  → REQUIRE EVIDENCE_AGENT
  
IF category IN ["Duplicate", "Merchant Dispute", "Refund", "Product", "Subscription"]:
  → REQUIRE MERCHANT_AGENT
  
IF risk_tags CONTAIN ["VELOCITY_BREACH", "SUSPICIOUS_BEHAVIOR", "MERCHANT_BLACKLISTED"]:
  → REQUIRE COMPLIANCE_AGENT

EXECUTION ORDER (dependency-aware):
  1. FRAUD_AGENT (fraud classification informs all)
  2. EVIDENCE_AGENT (evidence context for other specialists)
  3. MERCHANT_AGENT (merchant verification)
  4. COMPLIANCE_AGENT (regulatory checks last)
```

### Parameters Checked

| Parameter | Check | Output |
|-----------|-------|--------|
| **amount** | Exceeds tier thresholds? | Priority: LOW/MEDIUM/HIGH/CRITICAL |
| **fraud_signals** | High-risk tags present? | Complexity: LOW/MEDIUM/HIGH/CRITICAL |
| **risk_tags[]** | Compliance triggers? | Agent list: [FRAUD_AGENT, ...] |
| **investigation_complexity** | From Agent 2 | Affects analyst level (JUNIOR/STANDARD/SENIOR/LEAD) |
| **evidence_strength** | From Agent 5 | May block MERCHANT_AGENT until complete |
| **customer_risk** | From Agent 2 | Affects scrutiny level |

### Output

```json
{
  "workflow_plan": {
    "complexity": "HIGH",
    "priority": "CRITICAL",
    "required_agents": ["FRAUD_AGENT", "EVIDENCE_AGENT"],
    "execution_sequence": [
      {
        "agent": "FRAUD_AGENT",
        "reason": "Fraud suspicion + OTP shared pattern",
        "dependencies": []
      },
      {
        "agent": "EVIDENCE_AGENT",
        "reason": "Verify evidence before specialist agents",
        "dependencies": ["FRAUD_AGENT"]
      }
    ]
  },
  "assigned_queue": "FRAUD_INVESTIGATION_HIGH_PRIORITY",
  "assigned_analyst": "senior-analyst-001",
  "analyst_level": "SENIOR",
  "sla_deadline": "2026-06-21T11:46:29Z",
  "base_sla_hours": 8,
  "case_status": "READY_FOR_INVESTIGATION"
}
```

---

# Agent 4: FRIA
## Fraud Reasoning Agent (FRIA)

**Role**: Fraud pattern analysis, behavior profiling, & anomaly detection  
**Model**: Groq (llama-3.1-8b-instant)  
**Flow Type**: Linear (6 tools pre-executed in parallel in build_context node)

### Workflow

```
RECEIVES Agent 1, Agent 2 OUTPUT
          │
          ▼
[VALIDATE NODE]
  • Input sanity checks
          │
          ▼
[BUILD_CONTEXT NODE]
  PRE-EXECUTE 6 TOOLS IN PARALLEL:
  
  Tool 1: detect_transaction_anomalies()
    → Off-hours flag, 24h transaction velocity count
  
  Tool 2: evaluate_location_velocity()
    → Geographic geovelocity travel speed checks
  
  Tool 3: analyze_spending_behavior()
    → Z-score statistical spending deviation
  
  Tool 4: verify_kyc_match()
    → Comparison against bank's KYC CIF records
  
  Tool 5: evaluate_device_fingerprint()
    → Login logs recognition and location match
  
  Tool 6: analyze_behavioral_patterns()
    → Historical claims counts and friendly fraud risk
          │
          ▼
[AGENT NODE - LLM]
  • Receives pre-computed tool results
  • Synthesizes fraud risk probability and trust levels
  • Produces detailed Fraud & Trust Assessment brief
          │
          ▼
[FINALIZE NODE]
  • Parse final JSON matching output schema
  • Map to fraud_risk_level and user_trust_score
  • Persist brief back to dispute_cases table
```

### Parameters Checked

| Parameter/Tool | Check | Fraud/Trust Signal |
|-----------|-------|--------------|
| **detect_transaction_anomalies** | Off-hours (11PM-5AM) & rapid-fire interval | +15% probability if off-hours, +30% velocity breach if two transactions in last 24h are < 15 seconds apart |
| **evaluate_location_velocity** | Travel distance speed | +25% probability if impossible travel speed; uses city-level normalization to prevent text false positives, skips missing locations |
| **analyze_spending_behavior** | Spend Z-score deviation | +20% probability if Z >= 3.0 or > 3x average spend |
| **verify_kyc_match** | KYC name/email/phone match | Suspicious status if fields mismatch registered KYC, or if all fields match on an "Unauthorized Transaction" category (Compromise Risk: HIGH) |
| **evaluate_device_fingerprint** | Unrecognized device | High rating if unrecognized device ID + location mismatch |
| **analyze_behavioral_patterns** | Dispute velocity / favor profile | High friendly fraud risk if 30d claim count >= 2 or merchant-favor rate is high |

### Output

```json
{
  "fraud_probability": 0.58,
  "fraud_risk_level": "MEDIUM",
  "anomaly_detection": {
    "amount_anomaly": true,
    "time_anomaly": false,
    "velocity_anomaly": false
  },
  "user_trust_score": 0.45,
  "behavioral_risk_score": 0.60,
  "identity_verification": "SUSPICIOUS"
}
```

### Fraud Probability Calculation

```
Fraud Probability is the rounded sum of active risk indicators capped between [0.00, 1.00]:

ANOMALY SIGNALS:
  + Time Anomaly (11 PM - 5 AM off-hours)   : +0.15
  + Velocity Breach (< 15s between txns)     : +0.30
  + Geovelocity Breach (Impossible travel)   : +0.25
  + Amount Anomaly (Z >= 3.0 or > 3x average): +0.20
  + Unrecognized Device                      : +0.15
  + Location Mismatch                        : +0.20

CUSTOMER DISCLOSED VECTOR FLAGS (METADATA):
  + Bank Impersonation / Vishing             : +0.30
  + Remote Access Application installed      : +0.25
  + Screen Sharing active with attacker      : +0.20
  + OTP Shared with third party              : +0.20
  + SIM Swap suspected                       : +0.20
  + Phishing Link clicked                    : +0.15
  + Unknown Beneficiary / recipient          : +0.10
  + Physical Device / Card Lost              : +0.10 each
  + Explicit Fraud check box selected        : +0.10
```

---

# Agent 5: EIA
## Evidence Intelligence Agent (EIA)

**Role**: Evidence verification & document requirement tracking  
**Model**: Groq (llama-3.1-8b-instant)  
**Execution**: ReAct loop (5 deterministic tools pre-computed)

### Workflow

```
RECEIVES Agent 1, 2, 3, 4 OUTPUTS
       │
       ▼
[AGENT NODE - ReAct Loop]
  
  Tool 1: evaluate_evidence_completeness()
    → Check required_documents from investigation_plan
    → Compare against fulfilled document requests (customer-obtainable only)
    → Score: 0-100%
  
  Tool 2: identify_missing_evidence()
    → List missing customer-obtainable documents
    → Determine if gaps block investigation
  
  Tool 3: validate_evidence_consistency()
    → Cross-check transaction details (amount, merchant, date)
    → Flag discrepancies
  
  Tool 4: assess_evidence_strength()
    → Verdict base (Match: 0.65, Mismatch: 0.05, Unassessed/No docs: 0.30) + completeness adjustment (ranges from -0.25 to +0.25) + Agent 2 Data Quality adjustment (capped at ±0.075 max)
    → Returns HIGH (score >= 0.70), MEDIUM (0.45 - 0.69), or LOW (< 0.45) strength
  
  Tool 5: determine_next_document_request()
    → Recommend next required customer doc to formally request
       │
       ▼
[FINALIZE NODE]
  • Generate evidence_assessment summary
  • Update evidence_match_note
  • Determine if case ready for investigation
```

### Parameters Checked

| Parameter | Check | Output |
|-----------|-------|--------|
| **required_documents[]** | From investigation_plan | Customer docs vs bank docs |
| **fulfilled_requests** | Document request table | Count, types, dates |
| **uploaded_files** | Files on disk in uploads/ | Count, formats, sizes |
| **evidence_match** | From Agent 1 | true/false/null |
| **document_consistency** | Amount, merchant, date | Consistency score |
| **evidence_strength** | Combined formula score | Strength level (HIGH/MEDIUM/LOW) |

### Output

```json
{
  "evidence_assessment": {
    "completeness_score": 65,
    "completeness_status": "PARTIAL",
    "required_documents_count": 3,
    "fulfilled_documents_count": 2,
    "missing_documents": [
      "DEVICE_LOGIN_HISTORY"
    ],
    "bank_obtainable_documents": [
      "UPI_SERVER_LOGS",
      "OTP_DELIVERY_RECORDS"
    ]
  },
  "evidence_strength": "MEDIUM",
  "evidence_consistency": true,
  "gaps_block_investigation": false,
  "recommended_document_requests": [
    "DEVICE_LOGIN_HISTORY"
  ]
}
```

---

# Data Flow & Dependencies

## Complete Data Flow

```
CUSTOMER
   │
   ▼
┌──────────────────────────────┐
│ Agent 1: ARIA (INTAKE)       │
│ • Classify dispute           │
│ • Score fraud indicators     │
│ • Assign priority            │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ Agent 2: IIA (INVESTIGATION) │
│ • Customer risk profile      │
│ • Merchant risk profile      │
│ • Investigation plan         │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ Agent 3: WOA (ORCHESTRATION) │
│ • Evaluate case complexity   │
│ • Dynamically route case     │
│ • Schedule specialist agents │
└──────────┬───────────────────┘
           │
           ├────────────────────────────┐
           ▼                            ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ Agent 4: FRIA (FRAUD AGENT)  │  │ Agent 5: EIA (EVIDENCE AGENT)│
│ • Spend & geovelocity risk   │  │ • Document completeness check│
│ • Anomaly indicators check   │  │ • Evidence strength checklist│
└──────────┬───────────────────┘  └─────────────┬────────────────┘
           │                                    │
           └──────────────────┬─────────────────┘
                              ▼
                        dispute_cases
                    (Final structured case)
                              │
                              ▼
                     INVESTIGATION QUEUE
              (Fraud/Merchant/Compliance Teams)
```

---

# Error Handling & Fallbacks

## Agent Failure Scenarios

### Scenario 1: LLM Timeout
```
Agent attempts 3 ReAct loops
  Loop 1: Success → Continue
  Loop 2: Success → Continue
  Loop 3: Timeout → Set fallback_mode=true
  
Fallback: Return conservative assessment
  • Use highest risk signal detected
  • Set requires_manual_review=true
  • Escalate to SENIOR analyst
```

### Scenario 2: Database Query Failure
```
Tool queries database
  Result: Database connection error
  
Fallback:
  • Log error with case_id
  • Set confidence_score = 0.5 (medium)
  • Return: "Unable to verify, escalate to analyst"
  • Set requires_manual_review=true
```

### Scenario 3: Missing Document
```
Agent 5 requires document type X
  Upload not found
  
Action:
  • Create DocumentRequest for type X
  • Set fulfilled=false
  • Flag in required_documents[]
  • May block MERCHANT_AGENT until provided
```

---

## Metrics & Monitoring

```json
{
  "agent_metrics": {
    "agent_1_aria": {
      "avg_duration_ms": 2847,
      "tool_calls_avg": 2,
      "llm_calls_avg": 1,
      "fallback_rate_pct": 2.3
    },
    "agent_2_iia": {
      "avg_duration_ms": 4521,
      "tool_calls_avg": 3.2,
      "database_queries": 5,
      "cache_hit_rate_pct": 78
    },
    "system_totals": {
      "avg_total_duration_ms": 15243,
      "cases_processed": 1247,
      "avg_priority": "MEDIUM",
      "fraud_detection_rate_pct": 34
    }
  }
}
```

---

## Quick Reference

| Agent | Role | Entry | Tools | Output |
|-------|------|-------|-------|--------|
| **ARIA** | Dispute intake | validate | 4 | fraud_suspicion, priority, confidence |
| **IIA** | History analysis | agent | 4 | investigation_plan, complexity |
| **WOA** | Orchestration | agent | 6 | workflow_plan, assigned_analyst |
| **FRIA** | Fraud patterns | validate | 6 | fraud_probability, risk_level |
| **EIA** | Evidence check | agent | 5 | evidence_assessment, gaps |


