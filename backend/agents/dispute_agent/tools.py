"""
Dispute Agent tools — atomic operations the agent graph can invoke.
"""
from typing import List
from langchain_core.tools import tool

from utils.helpers import determine_priority


@tool
def calculate_priority(amount: float, fraud_suspicion: bool, risk_tags: List[str]) -> str:
    """Determine case priority from amount and fraud indicators."""
    return determine_priority(amount, fraud_suspicion, risk_tags)


@tool
def clamp_score(score: float) -> float:
    """Clamp a confidence score to the valid [0.0, 1.0] range."""
    return max(0.0, min(1.0, score))
