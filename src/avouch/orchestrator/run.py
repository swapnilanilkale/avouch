"""Entry point for running the adaptive orchestrator.

Builds the initial state, invokes the compiled graph, and converts the final
graph state into a RunResult for reporting.
"""

import logging

from avouch.adapters.base import TargetAdapter
from avouch.agents.types import AttackObjective, RunResult
from avouch.orchestrator.graph import build_graph
from avouch.orchestrator.state import OrchestratorState

logger = logging.getLogger(__name__)


def run_adaptive_attack(
    target: TargetAdapter,
    judge: TargetAdapter,
    objective: AttackObjective,
    max_attempts: int = 4,
) -> RunResult:
    """Run an adaptive red-teaming attack via the LangGraph orchestrator.

    Args:
        target: The model under test.
        judge: The independent judge/critic model (different family advised).
        objective: The harmless proxy objective to pursue.
        max_attempts: Maximum number of attempts before stopping.

    Returns:
        A RunResult with all attempts, verdicts, and the overall success flag.
    """
    graph = build_graph()

    initial_state: OrchestratorState = {
        "objective": objective,
        "target": target,
        "judge": judge,
        "attempts": [],
        "verdicts": [],
        "critic_advice": "",
        "attempt_number": 0,
        "max_attempts": max_attempts,
        "succeeded": False,
    }

    logger.info("Invoking adaptive graph against %s", target.name)
    final_state = graph.invoke(initial_state)

    result = RunResult(
        objective=objective,
        target_name=target.name,
    )
    result.attempts = final_state["attempts"]
    result.verdicts = final_state["verdicts"]
    result.succeeded = final_state["succeeded"]
    return result
