# AI Dispute Resolution System

Enterprise-grade, multi-agent banking fraud and dispute resolution platform. Built for BFSI operations teams — automates dispute intake, classification, investigation, fraud detection, evidence verification, orchestration, and customer communication through 6 specialized AI agents and 30 fraud intelligence tools.

---

## Architecture

```mermaid
graph TD
    A([Customer Submission]) --> B[FastAPI Backend]
    B --> C[Intake & Validation]
    C --> D{Document Check}

    D -- Sufficient --> E["Agent 1 · ARIA\nDispute Understanding Agent"]
    D -- Insufficient --> Z([Halt: Pending Documents])

    E --> F["Agent 2 · IIA\nInvestigation Intelligence Agent"]
    F --> G["Agent 3 · WOA\nWorkflow Orchestration Agent\n─────────────────────────\nSingle source of truth for routing"]

    G -- "FRAUD_AGENT" --> H["Agent 4 · FRIA\nFraud Reasoning Agent\n─────────────────────────\n30 tools · Channel-aware"]
    G -- "EVIDENCE_AGENT" --> I["Agent 5 · EIA\nEvidence Intelligence Agent\n─────────────────────────\n5 tools"]
    G -- "No agents remaining" --> J[Structured Output Node]

    H --> G
    I --> G
    J --> K[(PostgreSQL Database)]
    K --> L([Ops Review Portal])

    E -. "Async Event" .-> M["Agent 6 · CCA\nCustomer Communication Agent"]
    K -. "Status / Analyst Action" .-> M
    M --> N([Email · Gmail / Outlook SMTP])

    style A fill:#1E293B,stroke:#334155,color:#F8FAFC
    style Z fill:#1E293B,stroke:#334155,color:#F8FAFC
    style L fill:#1E293B,stroke:#334155,color:#F8FAFC
    style B fill:#0F172A,stroke:#2563EB,color:#93C5FD
    style C fill:#0F172A,stroke:#334155,color:#94A3B8
    style D fill:#0F172A,stroke:#D97706,color:#FCD34D
    style E fill:#0F172A,stroke:#2563EB,color:#93C5FD
    style F fill:#0F172A,stroke:#2563EB,color:#93C5FD
    style G fill:#0F172A,stroke:#7C3AED,color:#C4B5FD
    style H fill:#0F172A,stroke:#DC2626,color:#FCA5A5
    style I fill:#0F172A,stroke:#059669,color:#6EE7B7
    style J fill:#0F172A,stroke:#334155,color:#94A3B8
    style K fill:#0F172A,stroke:#0EA5E9,color:#7DD3FC
    style M fill:#0F172A,stroke:#EA580C,color:#FFEDD5
    style N fill:#1E293B,stroke:#334155,color:#F8FAFC
```

---

## Agents

### Agent 1 — ARIA (Dispute Understanding Agent)

Reads the customer's dispute form, transaction metadata, and OCR-extracted document text. Produces the primary classification that all downstream agents build upon.

**Tools (deterministic, no DB queries):**
- `assess_transaction_context` — RBI liability tiers, off-hours risk, CNP channel flags, UPI/IMPS patterns
- `score_fraud_indicators` — I4C taxonomy: OTP sharing (+8), bank impersonation (+8), SIM swap (+8), remote access (+4), phishing (+4), card/device loss (+2.5)
- `verify_evidence_match` — OCR document text vs claimed merchant, amount, and document type
- `compute_confidence_score` — calibrated confidence from completeness, comment quality, evidence verdict, fraud signal alignment

**Confidence Score baseline: 0.30** (allows meaningful discrimination between 40–90% range)

**Outputs:** `dispute_category`, `fraud_suspicion`, `confidence_score`, `risk_tags`, `evidence_match`, `structured_reasoning`

---

### Agent 2 — IIA (Investigation Intelligence Agent)

Runs 4 database-backed tools against live customer, merchant, and case history to design a targeted investigation plan.

**Tools:**
- `lookup_customer_history` — dispute frequency, chargeback ratios, friendly fraud risk profile
- `check_merchant_risk` — category risk, complaint volume, blacklist status, fraud rate
- `find_duplicate_transaction` — identical merchant/amount/date within 72-hour window
- `lookup_related_cases` — outcomes of similar historical disputes (55%+ resolution rate = reliable signal)

**Outputs:** `investigation_plan`, `required_documents`, `recommended_queue`, `investigation_complexity`, `recommended_steps`

---

### Agent 3 — WOA (Workflow Orchestration Agent)

Acts as the authoritative workflow controller. Runs after IIA, before specialist agents. Its `workflow_path` cannot be modified by any other agent.

**Routing logic:**
- `FRAUD_AGENT` — if `fraud_suspicion = true` OR fraud-related dispute category
- `EVIDENCE_AGENT` — if document gaps exist
- `MERCHANT_AGENT` — merchant dispute categories
- `COMPLIANCE_AGENT` — regulatory flags

**Tools:**
- `evaluate_case_complexity`, `determine_required_agents`, `recommend_workflow_path`
- `assess_escalation_need`, `estimate_workload`, `determine_next_execution_step`

**Outputs:** `workflow_path`, `required_agents`, `next_agent`, `workflow_complexity`, `escalation_required`, `analyst_level`, `sla_hours`

---

### Agent 4 — FRIA (Fraud Reasoning Agent)

**The most complex agent — 30 fraud intelligence tools across 4 transaction channels.**

All tools run in parallel via `ThreadPoolExecutor(max_workers=20)`. All numeric fraud scores are server-side deterministic. The LLM synthesises narrative reasoning only.

#### Channel Detection

FRIA detects the transaction channel from `transaction_type` and routes the appropriate tools:

| Channel | Transaction Types |
|---|---|
| **UPI** | UPI |
| **Internet Banking** | Net Banking, Mobile Banking, IMPS, NEFT, RTGS |
| **Card POS** | Debit Card, Credit Card |
| **ATM** | ATM, ATM Cash, Cash Withdrawal |

**Device data (`device_id`) is NULL in the database for Card POS and ATM** — POS terminals and ATMs are merchant/bank hardware, not customer devices. Only digital channels (UPI, Net Banking) carry customer device context.

---

#### Core Tools — Digital Channels (UPI + Internet Banking)

| Tool | What it detects |
|---|---|
| `detect_transaction_anomalies` | Off-hours (11PM–5AM) flag; rapid-fire velocity (< 15 seconds between transactions) |
| `evaluate_location_velocity` | Geovelocity breach with city-level normalization (Mumbai = Mumbai, MH = Andheri, Mumbai) |
| `analyze_spending_behavior` | Z-score deviation from customer's 30-transaction baseline |
| `verify_kyc_match` | CIF record comparison; Compromise Risk HIGH for Unauthorized Transaction + full match (device access possible) |
| `evaluate_device_fingerprint` | Device ID familiarity, location consistency |
| `analyze_behavioral_patterns` | Prior dispute count, dispute velocity (30 days, deduplicated), friendly fraud rate |
| `evaluate_merchant_risk_intelligence` | Bank's merchant profile: risk tier, blacklist, fraud complaints, resolution rates |

---

#### UPI-Specific Tools (5)

| Tool | What it detects |
|---|---|
| `analyze_new_beneficiary_risk` | First-time high-value transfer to unknown beneficiary (+0.20) |
| `detect_upi_collect_request_fraud` | UPI collect/payment request fraud — victim approves outgoing transfer (+0.30) |
| `analyze_beneficiary_velocity` | 5+ different customers sending to same UPI ID recently (+0.30) |
| `evaluate_upi_handle_reputation` | UPI handle with 5+ historical fraud reports (+0.35) |
| `analyze_dormant_beneficiary_risk` | Beneficiary first used < 7 days ago — throwaway account (+0.20) |

---

#### Internet Banking / Mobile Banking Tools (4)

| Tool | What it detects |
|---|---|
| `detect_impossible_login_travel` | Different city transaction within 2 hours — credential compromise (+0.35) |
| `analyze_device_change_large_transfer` | New device + amount > 2× average — ATO pattern (+0.30) |
| `detect_password_reset_transaction_pattern` | Transaction immediately after password reset (+0.30) |
| `analyze_mobile_number_change_risk` | Mobile number changed before transaction — OTP bypass possible (+0.35) |

---

#### Card POS Tools (11)

| Tool | What it detects |
|---|---|
| `analyze_card_velocity` | 3+ card transactions within 5 minutes (+0.25) |
| `evaluate_atm_pos_distance` | Different city ATM + POS within 1 hour — card cloning (+0.35) |
| `analyze_foreign_usage` | International card use when 90%+ history is domestic (+0.30) |
| `analyze_card_present_anomalies` | Late-night / high-risk merchant / amount 3× POS average (+0.15–0.25) |
| `detect_merchant_compromise_pattern` | 10+ disputes at merchant in 7 days — skimming device (+0.25–0.40) |
| `analyze_first_time_merchant` | Never used this merchant + amount > 1.5× average (+0.15) |
| `evaluate_merchant_resolution_history` | >70% customer-favor dispute rate = merchant fault pattern (+0.15–0.25) |
| `detect_card_testing_pattern` | ≤₹50 micro-transactions before main fraud (+0.30) |
| `analyze_multi_merchant_burst` | 4+ merchants within 30 minutes — stolen card hopping (+0.25) |
| `evaluate_mcc_risk` | Electronics/Travel/Crypto/Gift Cards = high-risk category (+0.10–0.20) |
| `analyze_decline_success_pattern` | 2+ declined attempts before success — card testing (+0.20) |
| `check_refund_reversal_absence` | Refund claimed but no reversal transaction in records (+0.15) |

---

#### ATM Tools (6)

| Tool | What it detects |
|---|---|
| `analyze_atm_velocity` | 3+ ATM withdrawals within 1 hour (+0.25) |
| `evaluate_atm_geovelocity` | Different city ATM within 2 hours — card cloning (+0.35) |
| `analyze_cash_withdrawal_patterns` | Amount > 3× average or 3+ withdrawals in 24h (+0.15) |
| `analyze_consecutive_atm_withdrawals` | 3+ same-amount withdrawals in short interval (+0.25) |
| `analyze_foreign_atm_usage` | International ATM when 80%+ history is domestic (+0.35) |
| `detect_sim_swap_atm_pattern` | SIM swap + ATM withdrawal = bypass + drain (+0.40) |

---

#### Universal Tools — All Channels (4)

| Tool | What it detects |
|---|---|
| `evaluate_historical_fraud_victim_score` | Customer defrauded before — repeat targeting (+0.15) |
| `detect_account_takeover_pattern` | 2+ ATO signals (password reset + device change + SIM swap) combined (+0.25–0.40) |
| `analyze_mule_account_indicators` | 8+ transactions in 24h or 5+ beneficiaries in 2h — pass-through account (+0.40) |
| `detect_historical_case_similarity` | Same merchant + same fraud pattern in historical cases (+0.20) |

---

#### Fraud Probability Formula (Server-Side Deterministic)

```
Base signals:
  Unauthorized Transaction category          +0.15
  Amount anomaly 2×–5× average              +0.15
  Amount anomaly > 5× average               +0.25
  Off-hours transaction (11 PM – 5 AM)      +0.15
  Rapid-fire velocity (< 15s gap)           +0.30
  Geovelocity breach (impossible travel)    +0.35  ← strongest hard signal
  Unrecognized device (digital only)        +0.30
  Location mismatch (digital only)          +0.20
  KYC Compromise Risk HIGH                  +0.20
  Behavioral risk score ≥ 0.60              +0.15

Social engineering signals (from customer form):
  Bank impersonation call                   +0.30
  Remote access app installed               +0.25
  Screen sharing active                     +0.20
  OTP shared with third party               +0.20
  SIM swap suspected                        +0.20
  Phishing link clicked                     +0.15
  Unknown beneficiary                       +0.10
  Fraud selected by customer                +0.10

Merchant signals (all channels):
  Merchant blacklisted                      +0.50
  Merchant CRITICAL risk                    +0.30
  Merchant HIGH risk                        +0.15

Channel-specific signals: (see tool tables above)

Final: clamp to [0.00, 1.00]
```

**Risk Levels:** LOW < 0.15 · MEDIUM < 0.40 · HIGH < 0.75 · CRITICAL ≥ 0.75

**Fraud Review tab is channel-aware** — Device & Location section hidden for Card POS and ATM. Separate intelligence panels shown per channel. LLM reasoning rules enforced server-side (wrong merchant tier corrected, score weights stripped, social engineering signals always referenced when present).

---

### Agent 5 — EIA (Evidence Intelligence Agent)

Audits evidence completeness and transaction record consistency. Separates customer-obtainable from bank-obtainable documents.

**Tools:**
- `evaluate_evidence_completeness` — required docs vs fulfilled requests + upload count
- `identify_missing_evidence` — unfulfilled customer document gaps
- `validate_evidence_consistency` — amount/merchant/date vs original transaction record
- `assess_evidence_strength` — weighted: Agent 1 verdict + completeness + Agent 2 data quality
- `determine_next_document_request` — next formal document request (deduplicates pending)

**Outputs:** `evidence_completeness`, `evidence_strength`, `missing_documents`, `bank_pending_documents`, `investigation_blocked`, `recommended_document_requests`

The customer tracking portal automatically displays `missing_documents` from EIA without requiring analysts to create individual requests.

---

### Agent 6 — CCA (Customer Communication Agent)

Generates and delivers professional HTML email notifications. Fires asynchronously — never blocks the workflow. Internal data (agent names, fraud scores, risk levels, queue assignments) is never exposed.

**Email triggers (auto-fired, each at most once per case):**

| Trigger | Type | Dedup |
|---|---|---|
| Case submitted | `CASE_RECEIVED` | Once per case |
| IIA completes | `INVESTIGATION_STARTED` | Once per case |
| Analyst creates document request | `DOCUMENT_REQUESTED` | Every analyst action |
| Customer uploads documents | `DOCUMENTS_RECEIVED` | Every upload |
| Case resolved/rejected/closed | `CASE_RESOLVED` | Once per case |
| Manual from Communications tab | Any type | Always sends |

`FRAUD_REVIEW_STARTED` and `EVIDENCE_REVIEW_COMPLETED` are suppressed from auto-sending — they are internal pipeline steps. Analysts can manually send any type from the Communications tab.

**Status changes trigger `STATUS_CHANGED`** only for major customer-visible transitions (Dispute Raised → Under Investigation → Pending Documents → Escalated → Resolved). Internal transitions are silently skipped.

**Delivery:** Gmail SMTP (`smtp.gmail.com:587` TLS) recommended. All emails in demo mode redirect to `NOTIFICATION_EMAIL`.

**Outputs:** persisted to `communication_logs` table with `subject`, `body` (HTML), `recipient`, `status`, `sent_at`.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | FastAPI |
| Agent orchestration | LangGraph + LangChain |
| LLM engine | Groq — `llama-3.1-8b-instant` |
| Database | PostgreSQL, SQLAlchemy ORM (pool: 20 base / 40 overflow) |
| Document extraction | PyMuPDF, pytesseract (OCR) |
| LLM resilience | Tenacity (exponential backoff, 3 retries) |
| Frontend | Next.js 14 App Router, React 18, TypeScript |
| Forms | React Hook Form + Zod |
| Real-time | WebSocket (live case status push) |
| Email | smtplib TLS (Gmail / Outlook) |
| Priority engine | Deterministic post-workflow computation |

---

## Key Design Decisions

**FRIA is transaction-channel-aware.**
Different transaction types have fundamentally different fraud signals. Card POS terminals don't expose customer device data. ATMs don't expose mobile metadata. FRIA routes 30 tools based on channel — wrong signals for the wrong channel create false positives. Device fingerprint and KYC match are disabled for Card POS and ATM at the database level (device_id = NULL for those transaction types).

**LLM produces narrative — deterministic code produces numbers.**
Fraud probability, confidence scores, trust scores, and all risk levels are computed server-side. The LLM is given the tool results and asked to explain them. Server-side post-processing corrects known LLM errors: strips score weights from findings, corrects merchant tier misattribution, and strips merchant-favour rates below the 70% threshold.

**WOA is the single source of truth.**
No specialist agent can change the workflow path. When WOA excludes `FRAUD_AGENT`, the Fraud Review tab is hidden. All stale fraud data is cleared. When it re-includes it, scores are recomputed from scratch.

**Assessment confidence starts at 0.30, not 0.50.**
A 0.50 baseline meant well-documented cases always hit 100%, making the score meaningless. With 0.30 baseline: excellent case = 83%, outstanding case = 90–95%, weak case = 40–55%.

**KYC match is context-aware.**
A full name/email/phone match in an Unauthorized Transaction dispute raises Compromise Risk HIGH — the fraudster has device/email access. A full match in that context is not VERIFIED.

**Velocity breach uses time gaps, not daily counts.**
Two transactions < 15 seconds apart = breach. Three transactions in a day = normal card usage.

**Location normalization prevents geovelocity false positives.**
"Mumbai" = "Mumbai, MH" = "Andheri, Mumbai". Unknown/missing locations are skipped rather than flagged.

**Behavioral patterns are deduplicated.**
Cases appearing in both `dispute_cases` (live) and `dispute_history` (resolved) are counted once, not twice.

**CCA communication is noise-controlled.**
One-shot types (CASE_RECEIVED, INVESTIGATION_STARTED, CASE_RESOLVED) fire at most once per case automatically. FRAUD_REVIEW_STARTED and EVIDENCE_REVIEW_COMPLETED are analyst-triggered only. STATUS_CHANGED fires only for major customer-visible transitions.

**PII is masked before reaching the LLM.**
Names, IDs, and free-text are masked via `utils/pii_masking.py`. Social engineering metadata (bank impersonation, remote access, etc.) IS passed to FRIA's LLM so it can correctly explain the fraud, but only after tools have already used it for deterministic scoring.

---

## Project Structure

```
ai-dispute-resolution-system/
├── backend/
│   ├── agents/
│   │   ├── dispute_agent/          # Agent 1 — ARIA
│   │   ├── investigation_agent/    # Agent 2 — IIA
│   │   ├── orchestration_agent/    # Agent 3 — WOA
│   │   ├── fraud_reasoning_agent/  # Agent 4 — FRIA (30 tools)
│   │   ├── evidence_agent/         # Agent 5 — EIA
│   │   └── communication_agent/    # Agent 6 — CCA
│   ├── api/
│   │   ├── main.py                 # FastAPI entry point
│   │   └── routes/                 # disputes, ops_cases, ops_analytics,
│   │                               # queues, auth, communications, dispute_tracking
│   ├── database/
│   │   ├── database.py             # SQLAlchemy engine, session, auto-migrations
│   │   └── models.py               # ORM: DisputeCase, CommunicationLog, etc.
│   ├── prompts/                    # LLM system prompts per agent
│   ├── schemas/                    # Pydantic request/response models
│   ├── services/                   # Priority, SLA, queue, document rules,
│   │                               # communication, email, analytics
│   ├── workflows/
│   │   └── dispute_workflow.py     # LangGraph compiled graph (recursion_limit=50)
│   └── utils/                      # Helpers, logger, PII masking, OCR extractor
└── frontend/
    └── src/
        ├── app/
        │   ├── submit-dispute/     # Customer dispute submission (multi-step form)
        │   ├── internal-review/    # Ops analyst queue + case workspace
        │   └── track/              # Customer tracking portal
        ├── components/             # Shared UI components
        ├── hooks/                  # WebSocket hook
        ├── lib/                    # API client, auth, utilities
        └── types/                  # TypeScript interfaces
```

---

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL
- Groq API key — [console.groq.com](https://console.groq.com)
- Tesseract OCR — [github.com/tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract)

### Backend

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create `backend/.env`:
```env
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/dispute_resolution
LLM_MODEL=llama-3.1-8b-instant
LLM_TEMPERATURE=0
LLM_MAX_TOKENS=1024
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# Email — Agent 6 CCA (Gmail recommended)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_16_char_app_password
NOTIFICATION_EMAIL=your_email@gmail.com

API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
SECRET_KEY=change-this-in-production
```

> **Gmail App Password:** Google Account → Security → 2-Step Verification → App passwords → Create

Initialize the database and start the server:
```bash
# Create all tables + run auto-migrations
python -c "from database.database import init_db; init_db()"

# Start the server
uvicorn api.main:app --reload
```

API at `http://localhost:8000` · Swagger at `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend at `http://localhost:3000`

---

## Portals

| Portal | URL | Audience |
|---|---|---|
| Dispute Submission | `http://localhost:3000/submit-dispute` | Customer |
| Case Tracking Search | `http://localhost:3000/track` | Customer |
| Case Status | `http://localhost:3000/track/{case_id}` | Customer |
| Ops Queue | `http://localhost:3000/internal-review` | Analyst |
| Case Workspace | `http://localhost:3000/internal-review/{case_id}` | Analyst |
| API Docs | `http://localhost:8000/docs` | Developer |

---

## Ops Workspace Tabs

| Tab | Visible when | Content |
|---|---|---|
| Case Analysis | Always | Classification, confidence, risk tags, evidence match, key findings |
| Investigation | Always | IIA plan, customer history, merchant intelligence, recommended steps |
| Fraud Review | WOA included FRAUD_AGENT | Channel badge, fraud probability, trust score, behavioral risk, channel-specific fraud signals, fraud findings |
| Evidence Review | Always | Completeness %, consistency check, missing docs, document provenance |
| Case Coordination | Always | WOA workflow path, agent progression, SLA tracker |
| Evidence | Always | Uploaded files with preview |
| Audit Trail | Always | Full immutable event log |
| Communications | Always | All customer emails with full HTML iframe preview, Send Update button |
| Advanced Diagnostics | Always (collapsed) | LangGraph execution trace, tool timings |

---

## Customer Tracking Portal

`/track/{case_id}` — publicly accessible, shows only customer-safe data:

- **Progress bar** — 4 stages: Received → Investigation → Review → Resolution
- **Next Action Required** — pending document list with upload deadline (amber alert banner)
- **Document upload** — customer uploads files directly; marks analyst document requests as fulfilled
- **Required Documents list** — sourced from `evidence_assessment.missing_documents` (EIA output) — shows automatically without analyst creating individual requests
- **Case timeline** — customer-visible audit events, deduplicated
- **Dispute details** — merchant, amount, transaction type, submission date

**Never shown:** agent names, fraud probability, trust scores, internal queues, analyst assignments, workflow paths, risk tags.

---

## API Reference

```
POST   /api/disputes/submit-public                  Submit dispute with file uploads
GET    /api/disputes/cases                          List cases (filter: status/priority/category/fraud)
GET    /api/disputes/cases/{case_id}                Full case detail
PUT    /api/disputes/cases/{case_id}/status         Update case status
POST   /api/disputes/{case_id}/upload-documents     Customer uploads additional documents
GET    /api/disputes/track/{case_id}                Customer-safe tracking (no internal data)
GET    /api/disputes/stats                          Dashboard statistics
GET    /api/disputes/document-requirements          Required docs for dispute type

GET    /api/ops/cases/{case_id}/notes               Get analyst notes
POST   /api/ops/cases/{case_id}/notes               Add analyst note
GET    /api/ops/cases/{case_id}/document-requests   Get document requests
POST   /api/ops/cases/{case_id}/document-requests   Create document request (triggers DOCUMENT_REQUESTED email)
GET    /api/ops/cases/{case_id}/uploads             List uploaded evidence files
POST   /api/ops/cases/{case_id}/reanalyse           Re-run full agent pipeline

GET    /api/communications/{case_id}                All communications for a case
POST   /api/communications/{case_id}/send           Manually trigger a communication

GET    /api/ops/analytics                           Ops analytics and stats
WS     /ws/disputes                                 Real-time case status push
```

---

## Dispute Categories

| Category | Routing |
|---|---|
| Unauthorized Transaction | FRAUD_AGENT → EVIDENCE_AGENT |
| Friendly Fraud | FRAUD_AGENT → EVIDENCE_AGENT |
| Duplicate Transaction | EVIDENCE_AGENT |
| Refund Not Received | EVIDENCE_AGENT → MERCHANT_AGENT |
| Merchant Dispute | EVIDENCE_AGENT → MERCHANT_AGENT |
| ATM Cash Issue | EVIDENCE_AGENT |
| Subscription Abuse | FRAUD_AGENT → EVIDENCE_AGENT |
| Other | EVIDENCE_AGENT |

---

## RBI Liability Tiers

| Amount | Handling |
|---|---|
| ₹0 – ₹10,000 | Standard processing |
| ₹10,000 – ₹50,000 | Heightened scrutiny |
| ₹50,000 – ₹2,00,000 | Senior officer escalation |
| ₹2,00,000 – ₹10,00,000 | Mandatory investigation |
| > ₹10,00,000 | Executive-level review |
