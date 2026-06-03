"""Assembly of the adaptive red-teaming graph.

Wires the attack, judge, and critique nodes into a LangGraph StateGraph with a
conditional edge that loops adaptively: after each judged attempt, the graph
either stops (success or max attempts reached) or critiques and retries.
"""

import logging

from langgraph.graph import END, START, StateGraph

from avouch.orchestrator.nodes import attack_node, critique_node, judge_node
from avouch.orchestrator.state import OrchestratorState

logger = logging.getLogger(__name__)


def route_after_judge(state: OrchestratorState) -> str:
    """Decide what to do after an attempt has been judged.

    Returns the name of the next node:
    - "stop" if the attack succeeded or max attempts have been reached.
    - "continue" otherwise (proceed to critique and retry).
    """
    if state["succeeded"]:
        logger.info("Routing: attack succeeded; stopping.")
        return "stop"

    if state["attempt_number"] >= state["max_attempts"]:
        logger.info("Routing: max attempts reached; stopping.")
        return "stop"

    logger.info("Routing: attempt failed; continuing to critique.")
    return "continue"


def build_graph():
    """Build and compile the adaptive red-teaming graph.

    Returns:
        A compiled LangGraph application ready to invoke with an initial state.
    """
    builder = StateGraph(OrchestratorState)

    builder.add_node("attack", attack_node)
    builder.add_node("judge", judge_node)
    builder.add_node("critique", critique_node)

    builder.add_edge(START, "attack")
    builder.add_edge("attack", "judge")

    builder.add_conditional_edges(
        "judge",
        route_after_judge,
        {
            "continue": "critique",
            "stop": END,
        },
    )

    builder.add_edge("critique", "attack")

    return builder.compile()
