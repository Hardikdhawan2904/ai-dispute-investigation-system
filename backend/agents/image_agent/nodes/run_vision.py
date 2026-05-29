import os

from dotenv import load_dotenv
load_dotenv()

from groq import Groq

from agents.image_agent.state import ImageAgentState
from agents.image_agent.prompts import VISION_PROMPT
from utils.logger import agent_logger

_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


def run_vision(state: ImageAgentState) -> dict:
    safe = state["safe_case_details"]

    prompt = VISION_PROMPT.format(
        customer_name=safe.get("customer_name", "Unknown"),
        merchant=safe.get("merchant", "Unknown"),
        currency=safe.get("currency", "INR"),
        amount=safe.get("amount", "Unknown"),
        transaction_date=safe.get("transaction_date", "Unknown"),
        dispute_reason=safe.get("dispute_reason", "Not specified"),
        fraud_selected=safe.get("fraud_selected", False),
    )

    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model=_VISION_MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{state['mime_type']};base64,{state['image_b64']}"},
                    },
                    {"type": "text", "text": prompt},
                ],
            }],
            max_tokens=1024,
            temperature=0,
        )
        return {"raw_response": response.choices[0].message.content}
    except Exception as exc:
        agent_logger.error(f"Vision LLM call failed: {exc}")
        return {"raw_response": "", "error": str(exc)}
