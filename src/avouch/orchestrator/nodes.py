"""Graph nodes for the adaptive red-teaming orchestrator.

Each node is a function that takes the current OrchestratorState, performs one
unit of work, and returns a partial state update. LangGraph merges these
updates into the running state.
"""

import logging
from typing import Any

from avouch.agents.attack_templates import ATTACK_TEMPLATES, TECHNIQUE_ORDER
from avouch.agents.critic_agent import CriticAgent
from avouch.agents.judge_agent import JudgeAgent
from avouch.agents.types import AttackAttempt, Outcome
from avouch.orchestrator.state import OrchestratorState

logger = logging.getLogger(__name__)


def attack_node(state: OrchestratorState) -> dict:
    """Generate and send one adversarial prompt to the target.

    Uses the next framing technique in order, and incorporates the critic's
    advice (if any) into the prompt sent to the target.
    """
    attempt_index = state["attempt_number"] + 1
    technique = TECHNIQUE_ORDER[(attempt_index - 1) % len(TECHNIQUE_ORDER)]
    base_template = ATTACK_TEMPLATES[technique]

    advice = state.get("critic_advice", "")
    if advice:
        attack_prompt = f"{base_template}\n\n(Strategy hint: {advice})"
    else:
        attack_prompt = base_template

    full_prompt = f"{state['objective'].target_system_prompt}\n\nUser: {attack_prompt}"

    logger.info(
        "Attack node: attempt %d, technique '%s'", attempt_index, technique.value
    )

    try:
        response = state["target"].generate(full_prompt, temperature=0.7)
        target_text = response.text
    except Exception as exc:  # noqa: BLE001 - record any failure as response text
        logger.warning("Target call failed: %s", exc)
        target_text = f"[target call failed: {exc}]"

    attempt = AttackAttempt(
        technique=technique,
        attack_prompt=attack_prompt,
        target_response=target_text,
        attempt_number=attempt_index,
    )

    return {
        "attempts": [attempt],
        "attempt_number": attempt_index,
    }


def judge_node(state: OrchestratorState) -> dict:
    """Evaluate the most recent attempt and record a verdict."""
    judge_agent = JudgeAgent(state["judge"])
    last_attempt = state["attempts"][-1]
    verdict = judge_agent.evaluate(state["objective"], last_attempt)

    logger.info(
        "Judge node: attempt %d -> %s",
        last_attempt.attempt_number,
        verdict.outcome.value,
    )

    update: dict[str, Any] = {"verdicts": [verdict]}
    if verdict.outcome is Outcome.SUCCESS:
        update["succeeded"] = True
    return update


def critique_node(state: OrchestratorState) -> dict:
    """Produce strategic advice for the next attempt based on the last failure."""
    critic_agent = CriticAgent(state["judge"])
    last_attempt = state["attempts"][-1]
    advice = critic_agent.advise(state["objective"], last_attempt)

    logger.info("Critique node: advice = %s", advice[:80])

    return {"critic_advice": advice}
