"""The orchestrator state.

Defines the shared state object that flows through the LangGraph adaptive
red-teaming workflow. Every node reads from and writes to this state. List
fields use the `add` reducer so nodes append to them rather than overwriting.
"""

import operator
from typing import Annotated, TypedDict

from avouch.adapters.base import TargetAdapter
from avouch.agents.types import AttackAttempt, AttackObjective, Verdict


class OrchestratorState(TypedDict):
    """Shared state for the adaptive red-teaming graph.

    Attributes:
        objective: The harmless proxy objective being pursued (fixed).
        target: Adapter for the model under test (fixed).
        judge: Adapter for the independent judge model (fixed).
        attempts: All attack attempts made so far (appended to each loop).
        verdicts: All judge verdicts so far (appended to each loop).
        critic_advice: The critic's latest suggestion for the next attempt.
        attempt_number: 1-based counter of the current attempt.
        max_attempts: Maximum number of attempts before stopping.
        succeeded: True once any attempt is judged a success.
    """

    objective: AttackObjective
    target: TargetAdapter
    judge: TargetAdapter
    attempts: Annotated[list[AttackAttempt], operator.add]
    verdicts: Annotated[list[Verdict], operator.add]
    critic_advice: str
    attempt_number: int
    max_attempts: int
    succeeded: bool
