"""
PII masking utility — scrubs sensitive data before sending to external LLMs.

Handles: card numbers, account numbers, CVV, OTP, PIN, UPI IDs,
         IFSC codes, IBAN, email addresses, phone numbers, Aadhaar, PAN.
"""
import re

# ── Regex patterns ─────────────────────────────────────────────────────────────

_PATTERNS = [
    # Card numbers — 13–19 digits, optionally spaced/dashed
    (re.compile(r"\b(\d[ -]?){13,19}\b"), "[CARD-XXXX]"),

    # CVV — "cvv 123", "CVV: 456", "cvv is 789"
    (re.compile(r"\b(cvv|cvc|security\s*code)\s*[:\-is]*\s*\d{3,4}\b", re.I), "[CVV-XXX]"),

    # PIN — "pin 1234", "my pin is 4321"
    (re.compile(r"\b(pin|m?pin)\s*[:\-is]*\s*\d{4,6}\b", re.I), "[PIN-XXXX]"),

    # OTP — "otp 847291", "OTP is 123456", "one time password 456123"
    (re.compile(r"\b(otp|one[\s-]time[\s-]password)\s*[:\-is]*\s*\d{4,8}\b", re.I), "[OTP-XXXX]"),

    # Aadhaar — 12 digits (spaced or plain)
    (re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"), "[AADHAAR-XXXX]"),

    # PAN card — ABCDE1234F pattern
    (re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"), "[PAN-XXXX]"),

    # IFSC code — SBIN0001234 pattern
    (re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"), "[IFSC-XXXX]"),

    # IBAN
    (re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{4,30}\b"), "[IBAN-XXXX]"),

    # UPI ID — username@bank
    (re.compile(r"\b[\w.\-]+@(okaxis|oksbi|okhdfcbank|okicici|paytm|ybl|ibl|axl|upi|[\w]+)\b", re.I), "[UPI-ID]"),

    # Bank account numbers — 9–18 digit standalone numbers
    (re.compile(r"\b(?<!\d)\d{9,18}(?!\d)\b"), "[ACCT-XXXX]"),

    # Email addresses in free text
    (re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b"), "[EMAIL-MASKED]"),

    # Indian mobile numbers in free text (10 digits starting with 6-9)
    (re.compile(r"\b[6-9]\d{9}\b"), "[PHONE-XXXX]"),
]


def mask_text(text: str) -> str:
    """Scrub PII from a free-text string. Returns masked version."""
    if not text:
        return text
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def mask_email(email: str) -> str:
    """Mask email keeping first char and domain."""
    if not email or "@" not in email:
        return "***@***.***"
    local, domain = email.split("@", 1)
    return f"{local[0]}***@{domain}"


def mask_phone(phone: str) -> str:
    """Mask phone keeping first 2 and last 2 digits."""
    digits = "".join(c for c in (phone or "") if c.isdigit())
    if len(digits) < 4:
        return "XXXXXX"
    return digits[:2] + "X" * (len(digits) - 4) + digits[-2:]


def mask_name(full_name: str) -> str:
    """Reduce full name to first name + initials."""
    parts = (full_name or "Unknown").split()
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]} {''.join(p[0]+'.' for p in parts[1:])}"


def mask_case_for_llm(dispute_input: dict) -> dict:
    """
    Return a copy of dispute_input with identifier fields masked.
    customer_comment is passed through unmasked — the LLM needs full context.
    """
    return {
        **dispute_input,
        "email":          mask_email(dispute_input.get("email", "")),
        "phone":          mask_phone(dispute_input.get("phone", "")),
        "transaction_id": _mask_partial(dispute_input.get("transaction_id", "")),
    }


def mask_case_details_for_llm(case_details: dict) -> dict:
    """
    Return a copy of case_details dict (from to_dict()) with identifier fields masked.
    Used by image analysis agent.
    """
    return {
        **case_details,
        "customer_name":  mask_name(case_details.get("customer_name", "")),
        "email":          mask_email(case_details.get("email", "")),
        "phone":          mask_phone(case_details.get("phone", "")),
        "transaction_id": _mask_partial(case_details.get("transaction_id", "")),
    }


def _mask_partial(value: str) -> str:
    """Show first 4 and last 4 chars, mask the middle."""
    if not value or len(value) <= 8:
        return value
    return value[:4] + "X" * (len(value) - 8) + value[-4:]
