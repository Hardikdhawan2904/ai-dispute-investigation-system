CREATE DATABASE IF NOT EXISTS dispute_resolution;

USE dispute_resolution;

CREATE TABLE account_events (
	event_id VARCHAR(64) NOT NULL, 
	customer_id VARCHAR(64) NOT NULL, 
	event_type VARCHAR(64) NOT NULL, 
	event_timestamp DATETIME NOT NULL, 
	metadata_json JSON, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (event_id)
)ENGINE=InnoDB;

CREATE INDEX ix_account_events_event_timestamp ON account_events (event_timestamp);

CREATE INDEX ix_account_events_event_id ON account_events (event_id);

CREATE INDEX ix_account_events_customer_id ON account_events (customer_id);

CREATE INDEX ix_account_events_event_type ON account_events (event_type);

CREATE TABLE bank_customers (
	customer_id VARCHAR(64) NOT NULL, 
	full_name VARCHAR(256) NOT NULL, 
	email VARCHAR(256) NOT NULL, 
	phone VARCHAR(32) NOT NULL, 
	joining_date DATE, 
	PRIMARY KEY (customer_id)
)ENGINE=InnoDB;

CREATE INDEX ix_bank_customers_customer_id ON bank_customers (customer_id);

CREATE TABLE beneficiaries (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	customer_id VARCHAR(64) NOT NULL, 
	beneficiary_name VARCHAR(256) NOT NULL, 
	beneficiary_id VARCHAR(128), 
	created_at DATETIME NOT NULL, 
	last_used_at DATETIME, 
	transaction_count INTEGER, 
	trusted BOOL, 
	PRIMARY KEY (id)
)ENGINE=InnoDB;

CREATE INDEX ix_beneficiaries_customer_id ON beneficiaries (customer_id);

CREATE INDEX ix_beneficiaries_id ON beneficiaries (id);

CREATE TABLE customer_devices (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	device_id VARCHAR(64) NOT NULL, 
	customer_id VARCHAR(64) NOT NULL, 
	device_name VARCHAR(128), 
	first_seen DATETIME NOT NULL, 
	last_seen DATETIME, 
	trusted BOOL, 
	location VARCHAR(128), 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
)ENGINE=InnoDB;

CREATE INDEX ix_customer_devices_id ON customer_devices (id);

CREATE INDEX ix_customer_devices_device_id ON customer_devices (device_id);

CREATE INDEX ix_customer_devices_customer_id ON customer_devices (customer_id);

CREATE TABLE dispute_cases (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	case_id VARCHAR(64) NOT NULL, 
	customer_id VARCHAR(64) NOT NULL, 
	customer_name VARCHAR(256), 
	email VARCHAR(256), 
	phone VARCHAR(32), 
	transaction_id VARCHAR(128) NOT NULL, 
	transaction_type VARCHAR(64) NOT NULL, 
	merchant VARCHAR(256), 
	amount FLOAT NOT NULL, 
	currency VARCHAR(8), 
	transaction_date VARCHAR(32), 
	transaction_time VARCHAR(32), 
	customer_comment TEXT, 
	dispute_reason VARCHAR(256), 
	fraud_selected BOOL, 
	dispute_category VARCHAR(128), 
	fraud_suspicion BOOL, 
	customer_intent_summary TEXT, 
	priority VARCHAR(32), 
	confidence_score FLOAT, 
	risk_tags JSON, 
	structured_reasoning TEXT, 
	status VARCHAR(64), 
	workflow_ready BOOL, 
	current_stage VARCHAR(64), 
	assigned_queue VARCHAR(64), 
	assigned_analyst VARCHAR(128), 
	priority_score FLOAT, 
	sla_deadline DATETIME, 
	sla_breached BOOL, 
	sla_paused_at DATETIME, 
	duplicate_of VARCHAR(64), 
	requires_manual_review BOOL, 
	manual_review_reason TEXT, 
	locked_by VARCHAR(128), 
	locked_at DATETIME, 
	evidence_match BOOL, 
	evidence_match_note TEXT, 
	investigation_plan JSON, 
	confidence_factors JSON, 
	tools_used JSON, 
	agent_metadata JSON, 
	metrics JSON, 
	fallback_mode BOOL, 
	failure_reason VARCHAR(64), 
	workflow_plan JSON, 
	trust_intelligence JSON, 
	user_trust_score FLOAT, 
	behavioral_risk_score FLOAT, 
	identity_status VARCHAR(64), 
	fraud_reasoning_brief JSON, 
	fraud_probability FLOAT, 
	fraud_risk_level VARCHAR(32), 
	evidence_assessment JSON, 
	transaction_metadata JSON, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME, 
	PRIMARY KEY (id)
)ENGINE=InnoDB;

CREATE UNIQUE INDEX ix_dispute_cases_case_id ON dispute_cases (case_id);

CREATE INDEX ix_dispute_cases_dispute_category ON dispute_cases (dispute_category);

CREATE INDEX ix_dispute_cases_assigned_queue ON dispute_cases (assigned_queue);

CREATE INDEX ix_dispute_cases_created_at ON dispute_cases (created_at);

CREATE INDEX ix_dispute_cases_priority ON dispute_cases (priority);

CREATE INDEX ix_dispute_cases_transaction_id ON dispute_cases (transaction_id);

CREATE INDEX ix_dispute_cases_customer_id ON dispute_cases (customer_id);

CREATE INDEX ix_dispute_cases_fraud_suspicion ON dispute_cases (fraud_suspicion);

CREATE INDEX ix_dispute_cases_assigned_analyst ON dispute_cases (assigned_analyst);

CREATE INDEX ix_dispute_cases_id ON dispute_cases (id);

CREATE INDEX ix_dispute_cases_status ON dispute_cases (status);

CREATE TABLE dispute_history (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	case_id VARCHAR(64) NOT NULL, 
	customer_id VARCHAR(64) NOT NULL, 
	merchant_id VARCHAR(64), 
	transaction_id VARCHAR(64), 
	dispute_category VARCHAR(128) NOT NULL, 
	fraud_claim BOOL, 
	amount FLOAT NOT NULL, 
	resolution TEXT, 
	resolved_in_favor_of VARCHAR(32), 
	resolution_days INTEGER, 
	status VARCHAR(32), 
	created_at DATETIME NOT NULL, 
	resolved_at DATETIME, 
	PRIMARY KEY (id)
)ENGINE=InnoDB;

CREATE UNIQUE INDEX ix_dispute_history_case_id ON dispute_history (case_id);

CREATE INDEX ix_dispute_history_id ON dispute_history (id);

CREATE INDEX ix_dispute_history_customer_id ON dispute_history (customer_id);

CREATE TABLE merchant_profiles (
	merchant_id VARCHAR(64) NOT NULL, 
	merchant_name VARCHAR(256) NOT NULL, 
	merchant_category VARCHAR(128) NOT NULL, 
	total_transactions INTEGER, 
	total_disputes INTEGER, 
	fraud_complaints INTEGER, 
	resolved_customer_favor INTEGER, 
	resolved_merchant_favor INTEGER, 
	risk_level VARCHAR(32), 
	blacklisted BOOL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (merchant_id)
)ENGINE=InnoDB;

CREATE INDEX ix_merchant_profiles_merchant_name ON merchant_profiles (merchant_name);

CREATE INDEX ix_merchant_profiles_merchant_id ON merchant_profiles (merchant_id);

CREATE TABLE transactions (
	transaction_id VARCHAR(64) NOT NULL, 
	customer_id VARCHAR(64) NOT NULL, 
	merchant_id VARCHAR(64), 
	merchant_name VARCHAR(256) NOT NULL, 
	amount FLOAT NOT NULL, 
	currency VARCHAR(8), 
	transaction_type VARCHAR(64) NOT NULL, 
	transaction_date DATETIME NOT NULL, 
	status VARCHAR(32), 
	location VARCHAR(128), 
	latitude FLOAT, 
	longitude FLOAT, 
	device_id VARCHAR(64), 
	card_entry_mode VARCHAR(32), 
	is_disputed BOOL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (transaction_id)
)ENGINE=InnoDB;

CREATE INDEX ix_transactions_transaction_id ON transactions (transaction_id);

CREATE INDEX ix_transactions_customer_id ON transactions (customer_id);

CREATE TABLE audit_logs (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	case_id VARCHAR(64) NOT NULL, 
	event_type VARCHAR(128) NOT NULL, 
	stage VARCHAR(64), 
	actor VARCHAR(64), 
	payload JSON, 
	message TEXT, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(case_id) REFERENCES dispute_cases (case_id)
)ENGINE=InnoDB;

CREATE INDEX ix_audit_logs_case_id ON audit_logs (case_id);

CREATE INDEX ix_audit_logs_id ON audit_logs (id);

CREATE TABLE case_notes (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	case_id VARCHAR(64) NOT NULL, 
	analyst VARCHAR(128) NOT NULL, 
	note TEXT NOT NULL, 
	is_internal BOOL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(case_id) REFERENCES dispute_cases (case_id)
)ENGINE=InnoDB;

CREATE INDEX ix_case_notes_case_id ON case_notes (case_id);

CREATE INDEX ix_case_notes_id ON case_notes (id);

CREATE TABLE communication_logs (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	case_id VARCHAR(64) NOT NULL, 
	notification_type VARCHAR(64) NOT NULL, 
	recipient VARCHAR(256) NOT NULL, 
	subject VARCHAR(512) NOT NULL, 
	body TEXT NOT NULL, 
	status VARCHAR(32), 
	sent_at DATETIME, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(case_id) REFERENCES dispute_cases (case_id)
)ENGINE=InnoDB;

CREATE INDEX ix_communication_logs_id ON communication_logs (id);

CREATE INDEX ix_communication_logs_case_id ON communication_logs (case_id);

CREATE TABLE document_requests (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	case_id VARCHAR(64) NOT NULL, 
	requested_by VARCHAR(128) NOT NULL, 
	document_type VARCHAR(256) NOT NULL, 
	description TEXT, 
	due_date DATETIME, 
	fulfilled BOOL, 
	fulfilled_at DATETIME, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(case_id) REFERENCES dispute_cases (case_id)
)ENGINE=InnoDB;

CREATE INDEX ix_document_requests_id ON document_requests (id);

CREATE INDEX ix_document_requests_case_id ON document_requests (case_id);

CREATE TABLE workflow_states (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	case_id VARCHAR(64) NOT NULL, 
	node_name VARCHAR(128) NOT NULL, 
	input_state JSON, 
	output_state JSON, 
	execution_time_ms FLOAT, 
	success BOOL, 
	error_message TEXT, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(case_id) REFERENCES dispute_cases (case_id)
)ENGINE=InnoDB;

CREATE INDEX ix_workflow_states_id ON workflow_states (id);

CREATE INDEX ix_workflow_states_case_id ON workflow_states (case_id);
