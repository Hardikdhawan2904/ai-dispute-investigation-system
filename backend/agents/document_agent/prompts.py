DOCUMENT_ANALYSIS_PROMPT = """\
You are a banking fraud investigator analyzing a document uploaded as evidence for a dispute case.

CASE DETAILS:
- Customer: {customer_name}
- Claimed Merchant: {merchant}
- Claimed Amount: {currency} {amount}
- Transaction Date: {transaction_date}
- Dispute Reason: {dispute_reason}
- Fraud Claimed: {fraud_selected}

EXTRACTED DOCUMENT CONTENT:
\"\"\"
{extracted_text}
\"\"\"

Carefully analyze the document content and cross-reference it with the case details above.

Return ONLY valid JSON (no markdown, no explanation):
{{
  "document_type": "bank_statement | transaction_receipt | merchant_communication | spreadsheet | other",
  "extracted_amount": <number or null>,
  "extracted_merchant": "<string or null>",
  "extracted_date": "<YYYY-MM-DD or null>",
  "extracted_transaction_id": "<string or null>",
  "fraud_indicators": ["list of any fraud signals found in the document"],
  "matches_case": <true if document content is consistent with the case details>,
  "mismatches": ["list any contradictions between document and case details"],
  "confidence_adjustment": <float between -0.20 and +0.20 — positive if document supports the claim, negative if it contradicts>,
  "summary": "<1-2 sentences describing what the document shows and its relevance to the dispute>"
}}"""
