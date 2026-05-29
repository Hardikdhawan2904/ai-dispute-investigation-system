from langgraph.graph import StateGraph, END

from agents.image_agent.state import ImageAgentState
from agents.image_agent.nodes.validate_image import validate_image
from agents.image_agent.nodes.load_image import load_image
from agents.image_agent.nodes.run_vision import run_vision
from agents.image_agent.nodes.parse_findings import parse_findings


def _route_after_validate(state: ImageAgentState) -> str:
    return "end" if state.get("error") else "load_image"


def build_image_graph():
    g = StateGraph(ImageAgentState)

    g.add_node("validate_image", validate_image)
    g.add_node("load_image",     load_image)
    g.add_node("run_vision",     run_vision)
    g.add_node("parse_findings", parse_findings)

    g.set_entry_point("validate_image")
    g.add_conditional_edges(
        "validate_image",
        _route_after_validate,
        {"load_image": "load_image", "end": END},
    )
    g.add_edge("load_image",     "run_vision")
    g.add_edge("run_vision",     "parse_findings")
    g.add_edge("parse_findings", END)

    return g.compile()


image_graph = build_image_graph()
