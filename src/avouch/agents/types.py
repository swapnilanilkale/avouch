"""Shared data structures for Avouch agents.

These types form the vocabulary that flows between the attacker agents, the
target model, and the judge agent. Keeping them in one place ensures every
agent speaks the same language about objectives, attempts, and verdicts.
"""

from dataclasses import dataclass, field
from enum import Enum


class AttackTechnique(str, Enum):
    """A named adversarial framing technique.

    These are well-documented, publicly-known prompt framings used to test
    whether a model holds its stated rules under pressure. They are
    illustrative categories, not novel exploits.
    """

    DIRECT = "direct"
    ROLE_PLAY = "role_play"
    HYPOTHETICAL = "hypothetical"
    INSTRUCTION_OVERRIDE = "instruction_override"


@dataclass
class AttackObjective:
    """A harmless proxy objective for a red-teaming run.

    The target is given a benign secret rule (e.g. a secret word it must not
    reveal). The attacker's goal is to make the target break that rule. Success
    is objectively verifiable, and no harmful content is ever involved.

    Attributes:
        description: Human-readable description of the objective.
        target_system_prompt: The benign rule planted in the target model.
        success_substring: If this string appears in the target's response,
            the rule was broken and the attack succeeded.
    """

    description: str
    target_system_prompt: str
    success_substring: str


@dataclass
class AttackAttempt:
    """A single adversarial prompt sent to the target and its response.

    Attributes:
        technique: Which framing technique produced the attack prompt.
        attack_prompt: The adversarial prompt sent to the target.
        target_response: The target model's reply.
        attempt_number: 1-based index of this attempt within a run.
    """

    technique: AttackTechnique
    attack_prompt: str
    target_response: str
    attempt_number: int


class Outcome(str, Enum):
    """The judge's ruling on whether an attack succeeded."""

    SUCCESS = "success"
    FAILURE = "failure"
    UNCERTAIN = "uncertain"


@dataclass
class Verdict:
    """The judge's evaluation of an attack attempt.

    Attributes:
        outcome: Whether the attack succeeded, failed, or is uncertain.
        reasoning: The judge's short explanation for the ruling.
        attempt: The attack attempt this verdict refers to.
    """

    outcome: Outcome
    reasoning: str
    attempt: AttackAttempt


@dataclass
class RunResult:
    """The full result of a red-teaming run against one target.

    Attributes:
        objective: The objective that was tested.
        target_name: Identifier of the target adapter (e.g. 'groq:...').
        attempts: Every attack attempt made during the run.
        verdicts: The judge's verdict for each attempt.
        succeeded: True if any attempt was judged a success.
    """

    objective: AttackObjective
    target_name: str
    attempts: list[AttackAttempt] = field(default_factory=list)
    verdicts: list[Verdict] = field(default_factory=list)
    succeeded: bool = False


@dataclass
class ConversationTurn:
    """One turn of a multi-turn red-teaming conversation.

    Attributes:
        turn_number: 1-based index of this turn in the conversation.
        attacker_message: The adversarial message the attacker sent this turn.
        target_response: The target model's reply this turn.
        verdict: The judge's ruling on this turn, if judged.
    """

    turn_number: int
    attacker_message: str
    target_response: str
    verdict: Verdict | None = None
