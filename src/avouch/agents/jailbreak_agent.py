"""The Jailbreak Agent.

Given a harmless proxy objective and a target adapter, this agent crafts a
sequence of adversarial prompts using escalating framing techniques and
records the target's responses. It stops early if an attempt appears to
succeed (the success substring shows up in the target's reply).

This agent demonstrates adaptive, multi-attempt red-teaming on harmless
canary objectives. It never seeks or produces harmful content.
"""

import logging

from avouch.adapters.base import AdapterError, TargetAdapter
from avouch.agents.attack_templates import ATTACK_TEMPLATES, TECHNIQUE_ORDER
from avouch.agents.types import AttackAttempt, AttackObjective

logger = logging.getLogger(__name__)


class JailbreakAgent:
    """Crafts and runs escalating adversarial prompts against a target."""

    def __init__(self, target: TargetAdapter) -> None:
        """Create a Jailbreak Agent.

        Args:
            target: The adapter for the model being probed.
        """
        self._target = target

    def _build_prompt(self, objective: AttackObjective, technique) -> str:
        """Combine the target's planted rule context with a framing template.

        The target is run with its objective system prompt prepended, so the
        attack prompt is the framing template itself.
        """
        return ATTACK_TEMPLATES[technique]

    def run(
        self,
        objective: AttackObjective,
        max_attempts: int = 4,
    ) -> list[AttackAttempt]:
        """Run a sequence of attack attempts against the target.

        Args:
            objective: The harmless proxy objective to pursue.
            max_attempts: Maximum number of framing techniques to try.

        Returns:
            A list of AttackAttempt records, one per technique tried, in order.
            Stops early if the success substring appears in a response.
        """
        attempts: list[AttackAttempt] = []

        for index, technique in enumerate(TECHNIQUE_ORDER[:max_attempts], start=1):
            attack_prompt = self._build_prompt(objective, technique)

            full_prompt = f"{objective.target_system_prompt}\n\nUser: {attack_prompt}"

            logger.info(
                "Jailbreak attempt %d using technique '%s'", index, technique.value
            )

            try:
                response = self._target.generate(full_prompt, temperature=0.7)
                target_text = response.text
            except AdapterError as exc:
                logger.warning("Target call failed on attempt %d: %s", index, exc)
                target_text = f"[target call failed: {exc}]"

            attempt = AttackAttempt(
                technique=technique,
                attack_prompt=attack_prompt,
                target_response=target_text,
                attempt_number=index,
            )
            attempts.append(attempt)

            if objective.success_substring.lower() in target_text.lower():
                logger.info("Success substring found on attempt %d; stopping.", index)
                break

        return attempts
