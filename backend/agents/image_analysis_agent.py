"""
Image Analysis Agent — analyzes customer-uploaded evidence images.

Uses Groq's vision model to extract transaction details from bank SMS screenshots,
receipts, and statements, then cross-references with the dispute case.
"""
import os
import base64
import json
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from groq import Groq
from utils.logger import agent_logger
from utils.helpers import extract_json_from_text

_VISION_MODEL = "llama-3.2-11b-vision-preview"
_SUPPORTED_EXTS = {".jpg", ".jpeg", ".png"}

_ANALYSIS_PROMPT = """\
You are a banking fraud investigator analyzing a document uploaded as evidence for a dispute case.

CASE DETAILS:
- Customer: {customer_name}
- Claimed Merchant: {merchant}
- Claimed Amount: {currency} {amount}
- Transaction Date: {transaction_date}
- Dispute Reason: {dispute_reason}
- Fraud Claimed: {fraud_selected}

Carefully examine the uploaded image and extract all relevant information visible in it.

Return ONLY valid JSON (no markdown, no explanation):
{{
  "document_type": "bank_sms | bank_statement | receipt | upi_screenshot | card_statement | other",
  "extracted_amount": <number or null>,
  "extracted_merchant": "<string or null>",
  "extracted_date": "<YYYY-MM-DD or null>",
  "extracted_transaction_id": "<string or null>",
  "otp_visible": <true if an OTP is visible in the image, else false>,
  "fraud_indicators": ["list of any fraud signals visible in the image"],
  "matches_case": <true if image content is consistent with the case details>,
  "mismatches": ["list any contradictions between image and case details"],
  "confidence_adjustment": <float between -0.20 and +0.20 — positive if image supports the claim, negative if it contradicts it>,
  "summary": "<1-2 sentences describing what the image shows and its relevance to the dispute>"
}}"""


class ImageAnalysisAgent:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def is_supported(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in _SUPPORTED_EXTS

    def analyze(self, image_path: str, case_details: dict) -> Optional[dict]:
        """
        Analyze an image against a dispute case.
        Returns structured findings dict, or None if analysis fails.
        """
        path = Path(image_path)
        if not path.exists() or path.suffix.lower() not in _SUPPORTED_EXTS:
            return None

        try:
            with open(path, "rb") as f:
                image_b64 = base64.b64encode(f.read()).decode("utf-8")

            ext = path.suffix.lower()
            mime = "image/jpeg" if ext in {".jpg", ".jpeg"} else "image/png"

            prompt = _ANALYSIS_PROMPT.format(
                customer_name=case_details.get("customer_name", "Unknown"),
                merchant=case_details.get("merchant", "Unknown"),
                currency=case_details.get("currency", "INR"),
                amount=case_details.get("amount", "Unknown"),
                transaction_date=case_details.get("transaction_date", "Unknown"),
                dispute_reason=case_details.get("dispute_reason", "Not specified"),
                fraud_selected=case_details.get("fraud_selected", False),
            )

            response = self.client.chat.completions.create(
                model=_VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{mime};base64,{image_b64}"},
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
                max_tokens=1024,
                temperature=0,
            )

            raw = response.choices[0].message.content
            result = extract_json_from_text(raw)
            if not result:
                result = {"summary": raw[:500], "confidence_adjustment": 0.0, "matches_case": True}

            agent_logger.info(
                "Image analysis complete",
                extra={"file": path.name, "doc_type": result.get("document_type"), "adjustment": result.get("confidence_adjustment")},
            )
            return result

        except Exception as exc:
            agent_logger.error(f"Image analysis failed for {image_path}: {exc}")
            return None
