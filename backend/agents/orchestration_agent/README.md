# Workflow Orchestration Agent (WOA) — Agent 3

**Role**: Workflow coordinator, queue director, and specialist agent execution planner  
**Model**: Groq `llama-3.1-8b-instant` (via ChatGroq)  
**Entry Point**: `agent` (ReAct loop) → `finalize`  
**Framework**: LangGraph (StateGraph)  

---

## 🎯 Purpose

WOA is the brain of the multi-agent system. It runs late in the intake workflow to analyze outputs from preceding agents (understanding, fraud reasoning, and investigation planning) to coordinate downstream specialist executions. The agent executes an autonomous ReAct loop calling **6 deterministic tools** to:
- Compute case **Orchestration Complexity** (LOW, MEDIUM, HIGH, CRITICAL).
- Select which **Specialist Agents** must run based on categories, evidence match, and compliance tags.
- Build an **Ordered Execution Sequence** respecting agent-level dependency constraints.
- Determine whether **Management Escalation** is required (CRITICAL, HIGH, MEDIUM, or null) and log the specific triggers.
- Estimate total **Workload Hours** and determine the **Analyst Seniority Level** (JUNIOR, STANDARD, SENIOR, LEAD) required to handle the dispute.
- Detect the immediate **Next Execution Step** (advancing the case sequentially and flagging dependency blocks).

---

## 📋 Workflow

```
┌──────────────────────────────────────┐
│  Receives Agent 1 & Agent 2 Outputs  │
│  from Database                       │
└────────────┬─────────────────────────┘
             │
       [agent Node] ◄────────────────┐
  (Groq ReAct loop - LLM reasoning)  │
             │                       │
      (Has tool call?)               │
       /          \                  │
     (Yes)        (No)               │
     /              \                │
[tools Node]   [finalize Node]       │
(Run database  (Synthesize output,   │
 lookup tool)   determine next step  │
     │          and documentation)   │
     └───────────────┴───────────────┘
```

WOA executes at the `orchestration` node of the main workflow (`dispute_workflow.py`). It reads persisted DB fields and outputs a structured workflow plan. Downstream routing checks this plan: if `next_agent=FRAUD_AGENT`, the workflow routes to the `fraud_reasoning` node; if `next_agent=EVIDENCE_AGENT`, it routes to the `evidence` node. Both nodes loop back to the `orchestration` node after execution to dynamically determine and run the next scheduled step until all steps have completed and execution finalized.

---

## ── Agent Persona ──

* **Role**: Senior AI Workflow Orchestrator.
* **Goal**: Coordinate execution across downstream specialists, evaluate complexity, assign SLAs/workloads, and flag escalation requirements.
* **Backstory**: Built to manage operational hand-offs as the platform grew beyond simple categorization. WOA decides which specialist agents are relevant, their ordered sequence, and when human analyst escalations are required.
* **Constraints**:
  - **Never reclassify** dispute categories (classification belongs to Agent 1).
  - **Never build** primary investigation plans (that belongs to Agent 2).
  - **Never make** final approval or transaction refund decisions.
  - Return **ONLY** a valid parseable JSON dictionary matching the specified output schema — no markdown, no conversational prose.

---

## ── LangGraph Pipeline Flow ──

WOA's StateGraph consists of:
1. **`agent`**: Invokes Groq `llama-3.1-8b-instant` to check inputs and dynamically call orchestration tools.
2. **`tools`**: Runs the requested database lookup and math assessment tools (`ToolNode`).
3. **`finalize`**: Formats the final JSON plan, applies final overrides (e.g. metadata timestamps), and saves the workflow plan.

---

## ── State Schema ──

The agent manages state via `OrchestrationAgentState` defined in [state.py](file:///d:/Transaction_dispute_agent/ai-dispute-resolution-system/backend/agents/orchestration_agent/state.py):
* `messages`: Message list accumulating ReAct tool call/response history.
* `case_id`: Current Case ID.
* `case_input`: Aggregated case input fields loaded from the database.
* `tool_results`: Caches raw tool reports.
* `final_output`: Synthesized orchestration plan JSON payload.
* `error`: Tracks execution errors.
* `tools_used`: Tracks executed tools.
* `agent_metadata`: Includes name, version, model, and duration.
* `metrics`: Tracks LLM calls, tool calls, and duration.

---

## ── Orchestration Tools ──

WOA has access to **6 database-backed tools** defined in [tools.py](file:///d:/Transaction_dispute_agent/ai-dispute-resolution-system/backend/agents/orchestration_agent/tools.py) that compute metrics and read case details:

### 1. `evaluate_case_complexity`
- **Purpose**: Computes orchestration complexity (`LOW` | `MEDIUM` | `HIGH` | `CRITICAL`) based on transaction amount, fraud flags, risk tags, and Agent 2's complexity score.
- **Inputs**: `case_id`
- **Output**: Complexity level and list of contributing factors.

### 2. `determine_required_agents`
- **Purpose**: Identifies which specialist agents must execute based on routing rules:
  - `FRAUD_AGENT`: Unauthorized Transaction, Friendly Fraud, or fraud suspicion.
  - `EVIDENCE_AGENT`: Document gaps, `evidence_match=false`, ATM Cash Issues, or Friendly Fraud.
  - `MERCHANT_AGENT`: Merchant Disputes, Refund Not Received, Product Not Received, Subscription Abuse, or Duplicate Transaction.
  - `COMPLIANCE_AGENT`: High-risk compliance tags (e.g. velocity breaches, blacklist matches).
- **Inputs**: `case_id`
- **Output**: List of required agent identifiers and routing reasons.

### 3. `recommend_workflow_path`
- **Purpose**: Determines the optimal execution order for required specialists.
- **Dependency Rules**:
  - `FRAUD_AGENT` always runs first (informs other agents).
  - `EVIDENCE_AGENT` runs before `MERCHANT_AGENT` and `COMPLIANCE_AGENT` (provides evidence verification).
  - Canonical order: `FRAUD_AGENT` → `EVIDENCE_AGENT` → `MERCHANT_AGENT` → `COMPLIANCE_AGENT`.
- **Inputs**: `case_id`
- **Output**: Ordered sequence of agent paths and active dependencies.

### 4. `assess_escalation_need`
- **Purpose**: Determines if the case must be escalated to management.
- **Rules**:
  - `CRITICAL`: Fraud + amount > ₹50,000, OR Agent 2 complexity is CRITICAL.
  - `HIGH`: Fraud alone, OR amount > ₹5,00,000, OR blacklist/velocity risk tags.
  - `MEDIUM`: Amount > ₹50,000, OR Agent 2 complexity is HIGH.
- **Inputs**: `case_id`
- **Output**: Escalation required boolean, level, and triggers list.

### 5. `estimate_workload`
- **Purpose**: Estimates operational analyst hours and recommends analyst seniority.
- **Rules**:
  - Base hours by complexity: `LOW` = 1h, `MEDIUM` = 2h, `HIGH` = 4h, `CRITICAL` = 8h.
  - Adds 1 hour for each required specialist agent.
  - Analyst level: `LOW` → JUNIOR; `MEDIUM` → STANDARD; `HIGH` → SENIOR; `CRITICAL` → LEAD.
- **Inputs**: `case_id`
- **Output**: Estimated hours, analyst level, and breakdown.

### 6. `determine_next_execution_step`
- **Purpose**: Checks the planned workflow path against completed agents in the database to identify the immediate next step. Checks for unmet dependency locks (e.g. EVIDENCE_AGENT blocked waiting for FRAUD_AGENT).
- **Inputs**: `case_id`
- **Output**: Next agent string (or `null` if complete), list of remaining agents, list of blocking dependencies, and explanation.

---

## ── Downstream Specialist Registry ──

WOA orchestrates routing across the following specialist nodes:
* **`FRAUD_AGENT`**: Evaluates unauthorized transactions, identity theft risk, and friendly fraud.
* **`MERCHANT_AGENT`**: Handles refunds, duplicate charges, undelivered products, and subscription issues.
* **`EVIDENCE_AGENT`**: Requests, checks, and validates outstanding customer documents.
* **`COMPLIANCE_AGENT`**: Evaluates regulatory guidelines, RBI timelines, and blacklisted merchants.

---

## ── Invocation ──

* **Function**: `run_orchestration_agent(case_id: str) -> dict`
* **Module**: [__init__.py](file:///d:/Transaction_dispute_agent/ai-dispute-resolution-system/backend/agents/orchestration_agent/__init__.py)
* **Behavior**:
  - Reads the combined classification results from Agent 1 (ARIA) and investigation plan from Agent 2 (IIA) fresh from the `dispute_cases` database table by `case_id` (save-first architecture).
  - Pre-runs all 6 orchestration tools in parallel and formats their results into the LLM context for optimal synthesis.
* **Callers**:
  - `workflows/dispute_workflow.py` → `orchestration_node`
  - `api/routes/ops_cases.py` → manual analyst re-orchestration trigger
  - `api/routes/disputes.py` → re-analysis trigger after customer document upload

