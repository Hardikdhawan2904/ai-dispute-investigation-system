from agents.dispute_agent.graph import dispute_graph
from agents.dispute_agent.state import DisputeAgentState


def run_dispute_agent(dispute_input: dict) -> dict:
    """
    Entry point — run the full dispute understanding pipeline.
    Returns the structured case dict ready for DB storage.
    """
    initial: DisputeAgentState = {
        "dispute_input":       dispute_input,
        "case_id":             "",
        "supporting_evidence": "",
        "raw_llm_response":    "",
        "final_case":          {},
        "error":               None,
    }
    result = dispute_graph.invoke(initial)
    return result["final_case"]
