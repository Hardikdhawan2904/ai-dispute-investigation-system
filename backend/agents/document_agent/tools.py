"""
Document Agent tools — extract text from PDF/XLSX for LLM analysis.
"""
from pathlib import Path
from langchain_core.tools import tool

from utils.pii_masker import mask_case_details_for_llm
from utils.helpers import extract_json_from_text

SUPPORTED_EXTS = {".pdf", ".xlsx", ".xls"}
_MAX_CHARS = 4000   # cap extracted text to keep tokens reasonable


@tool
def validate_document_file(file_path: str) -> dict:
    """Check whether a file exists and is a supported document format."""
    path = Path(file_path)
    valid = path.exists() and path.suffix.lower() in SUPPORTED_EXTS
    return {"valid": valid, "reason": "" if valid else f"Missing or unsupported file: {file_path}"}


@tool
def extract_document_text(file_path: str) -> str:
    """Extract readable text from a PDF or XLSX file (capped at 4000 chars)."""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        import pdfplumber
        lines = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines.append(text.strip())
        return "\n".join(lines)[:_MAX_CHARS]

    if ext in {".xlsx", ".xls"}:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        rows = []
        for sheet in wb.worksheets:
            rows.append(f"[Sheet: {sheet.title}]")
            for row in sheet.iter_rows(values_only=True):
                if any(cell is not None for cell in row):
                    rows.append("\t".join(str(c) if c is not None else "" for c in row))
        return "\n".join(rows)[:_MAX_CHARS]

    return ""


@tool
def mask_document_case_details(case_details: dict) -> dict:
    """Mask PII from case details before sending to the document analysis LLM."""
    return mask_case_details_for_llm(case_details)


@tool
def parse_document_json(raw_response: str) -> dict:
    """Parse structured JSON findings from a document LLM response."""
    result = extract_json_from_text(raw_response)
    if not result:
        result = {"summary": raw_response[:500], "confidence_adjustment": 0.0, "matches_case": True}
    return result
