"""Run a multi-turn red-teaming conversation with per-turn judging.

Run with:
    poetry run python src/avouch/agents/run_multiturn.py
"""

import logging

from avouch.adapters.registry import get_adapter
from avouch.agents.multiturn_agent import MultiTurnAttacker
from avouch.agents.objectives import get_objective


def main() -> None:
    """Run a judged multi-turn attack and print the per-turn transcript."""
    logging.basicConfig(level=logging.WARNING, format="%(message)s")

    target = get_adapter("cerebras")
    attacker = get_adapter("groq")
    judge = get_adapter("groq")
    objective = get_objective("secret_word")

    print(f"Target  : {target.name}")
    print(f"Attacker: {attacker.name}")
    print(f"Judge   : {judge.name}")
    print("Running multi-turn attack (this makes many calls)...")
    print()

    turns = MultiTurnAttacker(target, attacker, judge).run(objective, max_turns=5)

    print("=" * 70)
    print("MULTI-TURN TRANSCRIPT")
    print("=" * 70)
    for t in turns:
        verdict_str = t.verdict.outcome.value.upper() if t.verdict else "UNJUDGED"
        print(f"\n--- Turn {t.turn_number} -> {verdict_str} ---")
        print(f"Attacker: {t.attacker_message[:220]}")
        print(f"Target  : {t.target_response[:220]}")
        if t.verdict:
            print(f"Judge   : {t.verdict.reasoning}")
    print("\n" + "=" * 70)
    broke = any(t.verdict and t.verdict.outcome.value == "success" for t in turns)
    print(f"Overall: target {'BROKE its rule' if broke else 'HELD across all turns'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
