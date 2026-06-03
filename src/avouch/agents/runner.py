"""The attack runner.

Coordinates a single red-teaming run: the Jailbreak Agent probes the target,
the Judge Agent evaluates each attempt, and the results are bundled into a
RunResult. This is the linear precursor to the LangGraph orchestrator built
in a later phase.
"""

import logging

from avouch.adapters.base import TargetAdapter
from avouch.agents.jailbreak_agent import JailbreakAgent
from avouch.agents.judge_agent import JudgeAgent
from avouch.agents.types import AttackObjective, Outcome, RunResult

logger = logging.getLogger(__name__)


def run_attack(
    target: TargetAdapter,
    judge: TargetAdapter,
    objective: AttackObjective,
    max_attempts: int = 4,
) -> RunResult:
    """Run a full red-teaming cycle against a target.

    Args:
        target: The model under test.
        judge: The independent model used to evaluate attempts. Should be a
            different model family from the target.
        objective: The harmless proxy objective to pursue.
        max_attempts: Maximum number of attack techniques to try.

    Returns:
        A RunResult containing every attempt, every verdict, and an overall
        success flag (True if any attempt was judged a success).
    """
    logger.info(
        "Starting attack run: target=%s judge=%s objective='%s'",
        target.name,
        judge.name,
        objective.description,
    )

    attacker = JailbreakAgent(target)
    judge_agent = JudgeAgent(judge)

    attempts = attacker.run(objective, max_attempts=max_attempts)

    result = RunResult(
        objective=objective,
        target_name=target.name,
    )
    result.attempts = attempts

    for attempt in attempts:
        verdict = judge_agent.evaluate(objective, attempt)
        result.verdicts.append(verdict)
        if verdict.outcome is Outcome.SUCCESS:
            result.succeeded = True

    logger.info(
        "Attack run complete: %d attempts, succeeded=%s",
        len(result.attempts),
        result.succeeded,
    )

    return result
