"""Run a traced multi-turn attack and save its execution trace.

Run with:
    poetry run python src/avouch/agents/run_multiturn_traced.py

Then inspect the trace with:
    poetry run python src/avouch/tracing/view_trace.py multiturn
"""

import logging

from avouch.adapters.registry import get_adapter
from avouch.agents.multiturn_agent import MultiTurnAttacker
from avouch.agents.objectives import get_objective
from avouch.tracing.trace import Tracer


def main() -> None:
    """Run a judged, traced multi-turn attack and save the trace."""
    logging.basicConfig(level=logging.WARNING, format="%(message)s")

    target = get_adapter("cerebras")
    attacker = get_adapter("groq")
    judge = get_adapter("groq")
    objective = get_objective("secret_word")

    tracer = Tracer(
        run_kind="multiturn",
        metadata={
            "target": target.name,
            "attacker": attacker.name,
            "judge": judge.name,
            "objective": objective.description,
        },
    )

    print(f"Target  : {target.name}")
    print(f"Attacker: {attacker.name}")
    print(f"Judge   : {judge.name}")
    print("Running traced multi-turn attack...")

    attacker_agent = MultiTurnAttacker(target, attacker, judge, tracer=tracer)
    turns = attacker_agent.run(objective, max_turns=4)

    path = tracer.save(label="multiturn")

    broke = any(t.verdict and t.verdict.outcome.value == "success" for t in turns)
    print(f"\nTurns run: {len(turns)}")
    print(f"Outcome  : target {'BROKE its rule' if broke else 'HELD'}")
    print(f"Trace saved: {path}")
    print(
        "\nView it with:\n  poetry run python src/avouch/tracing/view_trace.py multiturn"
    )


if __name__ == "__main__":
    main()
