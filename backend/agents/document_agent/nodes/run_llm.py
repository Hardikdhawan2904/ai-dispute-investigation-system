import os

from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from agents.document_agent.state import DocumentAgentState
from agents.document_agent.prompts import DOCUMENT_ANALYSIS_PROMPT
from utils.logger import agent_logger

_SYSTEM = "You are a BFSI fraud investigator. Analyze documents and return only valid JSON."


def run_llm(state: DocumentAgentState) -> dict:
    safe = state["safe_case_details"]

    prompt = DOCUMENT_ANALYSIS_PROMPT.format(
        customer_name=safe.get("customer_name", "Unknown"),
        merchant=safe.get("merchant", "Unknown"),
        currency=safe.get("currency", "INR"),
        amount=safe.get("amount", "Unknown"),
        transaction_date=safe.get("transaction_date", "Unknown"),
        dispute_reason=safe.get("dispute_reason", "Not specified"),
        fraud_selected=safe.get("fraud_selected", False),
        extracted_text=state["extracted_text"],
    )

    try:
        llm = ChatGroq(
            model_name=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
            groq_api_key=os.getenv("GROQ_API_KEY"),
            temperature=0,
            max_tokens=1024,
        )
        response = llm.invoke([SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)])
        return {"raw_response": response.content}
    except Exception as exc:
        agent_logger.error(f"Document LLM call failed: {exc}")
        return {"raw_response": "", "error": str(exc)}
