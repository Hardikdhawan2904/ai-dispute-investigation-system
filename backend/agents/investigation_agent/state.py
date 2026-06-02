from typing import Annotated, List, Optional, TypedDict

from langgraph.graph.message import add_messages


class InvestigationAgentState(TypedDict):
    messages:                Annotated[list, add_messages]  # full ReAct tool-call / response history
    agent1_output:           dict   # structured classification output from Agent 1 (read-only)
    tool_results:            dict   # accumulated tool call results keyed by tool name (audit)
    investigation_findings:  dict   # intermediate structured findings built during the loop
    final_output:            dict   # final investigation plan returned to the caller
    error:                   Optional[str]
