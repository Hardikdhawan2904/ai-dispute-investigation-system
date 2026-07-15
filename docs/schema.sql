-- ============================================================================
-- BFSI Dispute Investigation Platform — Database Schema
-- PostgreSQL DDL, derived from backend/database/models.py (SQLAlchemy ORM)
--
-- Usage:
--   psql "postgresql://user:password@host:5432/dbname" -f schema.sql
--
-- Note: the running application creates this same schema automatically on
-- startup via SQLAlchemy's Base.metadata.create_all() (see init_db() in
-- backend/database/database.py) — there is no Alembic migration history.
-- This file is a portable, framework-independent copy of that same schema
-- for anyone who wants to provision the database without running the app,
-- or hand it to a DBA for review.
-- ============================================================================

-- ── Reference Ledger ───────────────────────────────────────────────────────

CREATE TABLE bank_customers (
    customer_id  VARCHAR(64) PRIMARY KEY,
    full_name    VARCHAR(256) NOT NULL,
    email        VARCHAR(256) NOT NULL,
    phone        VARCHAR(32)  NOT NULL,
    joining_date DATE
);

CREATE TABLE merchant_profiles (
    merchant_id              VARCHAR(64) PRIMARY KEY,
    merchant_name            VARCHAR(256) NOT NULL,
    merchant_category        VARCHAR(128) NOT NULL,
    total_transactions       INTEGER DEFAULT 0,
    total_disputes           INTEGER DEFAULT 0,
    fraud_complaints         INTEGER DEFAULT 0,
    resolved_customer_favor  INTEGER DEFAULT 0,
    resolved_merchant_favor  INTEGER DEFAULT 0,
    risk_level               VARCHAR(32) DEFAULT 'LOW',   -- LOW | MEDIUM | HIGH | CRITICAL
    blacklisted              BOOLEAN DEFAULT FALSE,
    created_at               TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
);
CREATE INDEX ix_merchant_profiles_merchant_name ON merchant_profiles (merchant_name);

CREATE TABLE transactions (
    transaction_id    VARCHAR(64) PRIMARY KEY,
    customer_id       VARCHAR(64) NOT NULL,               -- references bank_customers.customer_id by convention (no FK)
    merchant_id       VARCHAR(64),                        -- references merchant_profiles.merchant_id by convention (no FK)
    merchant_name     VARCHAR(256) NOT NULL,
    amount            DOUBLE PRECISION NOT NULL,
    currency          VARCHAR(8) DEFAULT 'INR',
    transaction_type  VARCHAR(64) NOT NULL,                -- UPI | NEFT | IMPS | Debit Card | ...
    transaction_date  TIMESTAMP NOT NULL,
    status             VARCHAR(32) DEFAULT 'Success',       -- Success | Failed | Pending | Reversed
    location          VARCHAR(128),
    latitude          DOUBLE PRECISION,                    -- GPS, for geovelocity checks
    longitude         DOUBLE PRECISION,
    device_id         VARCHAR(64),
    card_entry_mode   VARCHAR(32),                         -- SWIPE | CHIP_INSERT | CONTACTLESS_TAP | MANUAL_ENTRY | UNKNOWN
    is_disputed       BOOLEAN DEFAULT FALSE,
    created_at        TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
);
CREATE INDEX ix_transactions_customer_id ON transactions (customer_id);

CREATE TABLE dispute_history (
    id                    SERIAL PRIMARY KEY,
    case_id               VARCHAR(64) NOT NULL UNIQUE,
    customer_id           VARCHAR(64) NOT NULL,
    merchant_id           VARCHAR(64),
    transaction_id        VARCHAR(64),
    dispute_category      VARCHAR(128) NOT NULL,
    fraud_claim           BOOLEAN DEFAULT FALSE,
    amount                DOUBLE PRECISION NOT NULL,
    resolution            TEXT,
    resolved_in_favor_of  VARCHAR(32),                     -- customer | merchant | partial
    resolution_days       INTEGER,
    status                VARCHAR(32) DEFAULT 'Resolved',  -- Resolved | Rejected | Closed
    created_at            TIMESTAMP NOT NULL,
    resolved_at           TIMESTAMP
);
CREATE INDEX ix_dispute_history_customer_id ON dispute_history (customer_id);

-- ── Core Case ────────────────────────────────────────────────────────────

CREATE TABLE dispute_cases (
    id                       SERIAL PRIMARY KEY,
    case_id                  VARCHAR(64) NOT NULL UNIQUE,
    customer_id              VARCHAR(64) NOT NULL,
    customer_name            VARCHAR(256),
    email                    VARCHAR(256),
    phone                    VARCHAR(32),

    -- Transaction snapshot
    transaction_id           VARCHAR(128) NOT NULL,
    transaction_type         VARCHAR(64) NOT NULL,
    merchant                 VARCHAR(256),
    amount                   DOUBLE PRECISION NOT NULL,
    currency                 VARCHAR(8) DEFAULT 'INR',
    transaction_date         VARCHAR(32),
    transaction_time         VARCHAR(32),

    -- Customer input
    customer_comment         TEXT,
    dispute_reason           VARCHAR(256),
    fraud_selected           BOOLEAN DEFAULT FALSE,

    -- AI analysis (Agent 1 — ARIA)
    dispute_category         VARCHAR(128),
    fraud_suspicion          BOOLEAN DEFAULT FALSE,
    customer_intent_summary  TEXT,
    priority                 VARCHAR(32) DEFAULT 'MEDIUM',  -- set post-workflow by priority_engine.py, never by the LLM
    confidence_score         DOUBLE PRECISION DEFAULT 0.0,
    risk_tags                JSON DEFAULT '[]',
    structured_reasoning     TEXT,

    -- Workflow state
    status                   VARCHAR(64) DEFAULT 'Dispute Raised',
    workflow_ready           BOOLEAN DEFAULT FALSE,
    current_stage            VARCHAR(64) DEFAULT 'intake',

    -- Queue, priority & SLA
    assigned_queue           VARCHAR(64),
    assigned_analyst         VARCHAR(128),
    priority_score           DOUBLE PRECISION DEFAULT 0.0,
    sla_deadline              TIMESTAMP,
    sla_breached             BOOLEAN DEFAULT FALSE,
    sla_paused_at            TIMESTAMP,                    -- non-null while SLA clock is paused

    -- Duplicate & manual review
    duplicate_of             VARCHAR(64),                  -- case_id of the original, if this is a duplicate
    requires_manual_review   BOOLEAN DEFAULT FALSE,
    manual_review_reason     TEXT,

    -- Case lock (pessimistic locking for concurrent analysts)
    locked_by                VARCHAR(128),
    locked_at                TIMESTAMP,

    -- Evidence verification
    evidence_match           BOOLEAN,                      -- NULL = no documents submitted
    evidence_match_note      TEXT,
    evidence_assessment      JSON,                          -- Agent 4 — EIA output

    -- Agent outputs
    investigation_plan       JSON,                          -- Agent 2 — IIA output
    confidence_factors       JSON DEFAULT '[]',              -- Agent 1 — ARIA audit trail
    tools_used               JSON DEFAULT '[]',
    agent_metadata           JSON,
    metrics                  JSON,
    fallback_mode            BOOLEAN DEFAULT FALSE,         -- set when the LLM was unavailable at submission time
    failure_reason           VARCHAR(64),
    workflow_plan            JSON,                          -- Agent 3 — WOA output
    trust_intelligence       JSON,                          -- Identity & Trust Intelligence Agent output
    user_trust_score         DOUBLE PRECISION DEFAULT 1.0,
    behavioral_risk_score    DOUBLE PRECISION DEFAULT 0.0,
    identity_status          VARCHAR(64) DEFAULT 'PENDING',
    fraud_reasoning_brief    JSON,                          -- Fraud Reasoning Agent (FRIA) output
    fraud_probability        DOUBLE PRECISION DEFAULT 0.0,
    fraud_risk_level         VARCHAR(32) DEFAULT 'LOW',
    transaction_metadata     JSON DEFAULT '{}',              -- raw form fields, kept for re-analysis

    created_at               TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
    updated_at               TIMESTAMP DEFAULT (now() AT TIME ZONE 'utc')
);
CREATE INDEX ix_dispute_cases_customer_id       ON dispute_cases (customer_id);
CREATE INDEX ix_dispute_cases_transaction_id    ON dispute_cases (transaction_id);
CREATE INDEX ix_dispute_cases_dispute_category  ON dispute_cases (dispute_category);
CREATE INDEX ix_dispute_cases_fraud_suspicion   ON dispute_cases (fraud_suspicion);
CREATE INDEX ix_dispute_cases_priority          ON dispute_cases (priority);
CREATE INDEX ix_dispute_cases_status            ON dispute_cases (status);
CREATE INDEX ix_dispute_cases_assigned_queue    ON dispute_cases (assigned_queue);
CREATE INDEX ix_dispute_cases_assigned_analyst  ON dispute_cases (assigned_analyst);
CREATE INDEX ix_dispute_cases_created_at        ON dispute_cases (created_at);

-- ── Case Activity — child tables of dispute_cases ───────────────────────────
-- Note: cascade delete-orphan on these relationships is enforced by the
-- SQLAlchemy ORM (only applies when deleting through the app's ORM session),
-- not by an ON DELETE CASCADE at the database level.

CREATE TABLE audit_logs (                                  -- immutable, append-only
    id          SERIAL PRIMARY KEY,
    case_id     VARCHAR(64) NOT NULL REFERENCES dispute_cases(case_id),
    event_type  VARCHAR(128) NOT NULL,
    stage       VARCHAR(64),
    actor       VARCHAR(64) DEFAULT 'system',
    payload     JSON,
    message     TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
);
CREATE INDEX ix_audit_logs_case_id ON audit_logs (case_id);

CREATE TABLE workflow_states (                              -- LangGraph node execution snapshots
    id                 SERIAL PRIMARY KEY,
    case_id            VARCHAR(64) NOT NULL REFERENCES dispute_cases(case_id),
    node_name          VARCHAR(128) NOT NULL,
    input_state        JSON,
    output_state       JSON,
    execution_time_ms  DOUBLE PRECISION,
    success            BOOLEAN DEFAULT TRUE,
    error_message      TEXT,
    created_at         TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
);
CREATE INDEX ix_workflow_states_case_id ON workflow_states (case_id);

CREATE TABLE case_notes (                                   -- append-only
    id          SERIAL PRIMARY KEY,
    case_id     VARCHAR(64) NOT NULL REFERENCES dispute_cases(case_id),
    analyst     VARCHAR(128) NOT NULL,
    note        TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT TRUE,                       -- FALSE = visible to customer
    created_at  TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
);
CREATE INDEX ix_case_notes_case_id ON case_notes (case_id);

CREATE TABLE document_requests (
    id            SERIAL PRIMARY KEY,
    case_id       VARCHAR(64) NOT NULL REFERENCES dispute_cases(case_id),
    requested_by  VARCHAR(128) NOT NULL,
    document_type VARCHAR(256) NOT NULL,                    -- e.g. "Bank Statement", "Police FIR"
    description   TEXT,
    due_date      TIMESTAMP,
    fulfilled     BOOLEAN DEFAULT FALSE,
    fulfilled_at  TIMESTAMP,
    created_at    TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
);
CREATE INDEX ix_document_requests_case_id ON document_requests (case_id);

CREATE TABLE communication_logs (
    id                 SERIAL PRIMARY KEY,
    case_id            VARCHAR(64) NOT NULL REFERENCES dispute_cases(case_id),
    notification_type  VARCHAR(64) NOT NULL,                -- CASE_RECEIVED | INVESTIGATION_STARTED | ...
    recipient          VARCHAR(256) NOT NULL,
    subject            VARCHAR(512) NOT NULL,
    body               TEXT NOT NULL,
    status             VARCHAR(32) DEFAULT 'SENT',          -- SENT | FAILED | PENDING
    sent_at            TIMESTAMP,
    created_at         TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
);
CREATE INDEX ix_communication_logs_case_id ON communication_logs (case_id);

-- ── Risk & Behavioral Signals ────────────────────────────────────────────

CREATE TABLE account_events (                               -- bank security events: password resets, device registrations
    event_id         VARCHAR(64) PRIMARY KEY,
    customer_id      VARCHAR(64) NOT NULL,
    event_type       VARCHAR(64) NOT NULL,
    event_timestamp  TIMESTAMP NOT NULL,
    metadata_json    JSON DEFAULT '{}',
    created_at       TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
);
CREATE INDEX ix_account_events_customer_id     ON account_events (customer_id);
CREATE INDEX ix_account_events_event_type      ON account_events (event_type);
CREATE INDEX ix_account_events_event_timestamp ON account_events (event_timestamp);

CREATE TABLE customer_devices (                             -- registered devices, feeds device trust scoring
    id           SERIAL PRIMARY KEY,
    device_id    VARCHAR(64) NOT NULL,
    customer_id  VARCHAR(64) NOT NULL,
    device_name  VARCHAR(128),
    first_seen   TIMESTAMP NOT NULL,
    last_seen    TIMESTAMP,
    trusted      BOOLEAN DEFAULT FALSE,
    location     VARCHAR(128),
    created_at   TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
);
CREATE INDEX ix_customer_devices_device_id   ON customer_devices (device_id);
CREATE INDEX ix_customer_devices_customer_id ON customer_devices (customer_id);

CREATE TABLE beneficiaries (                                -- known payees per customer
    id                 SERIAL PRIMARY KEY,
    customer_id        VARCHAR(64) NOT NULL,
    beneficiary_name   VARCHAR(256) NOT NULL,
    beneficiary_id     VARCHAR(128),
    created_at         TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
    last_used_at       TIMESTAMP,
    transaction_count  INTEGER DEFAULT 0,
    trusted            BOOLEAN DEFAULT FALSE
);
CREATE INDEX ix_beneficiaries_customer_id ON beneficiaries (customer_id);
