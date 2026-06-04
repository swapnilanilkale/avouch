"""Resumable statistical benchmark.

Runs each (target, objective) cell N times, saving every run to disk as it
goes. Because results are persisted immediately, an interrupted run loses no
completed work -- simply re-run to add more, then aggregate.

Run with:  poetry run python src/avouch/eval/stat_benchmark.py
"""

import logging

from avouch.adapters.registry import get_adapter
from avouch.agents.objectives import OBJECTIVE_LIBRARY
from avouch.eval.persistence import save_run_result
from avouch.orchestrator.run import run_adaptive_attack

# Full grid configuration.
TARGETS = ["groq", "cerebras"]
JUDGE_FOR = {"groq": "cerebras", "cerebras": "groq"}
OBJECTIVES = ["secret_word", "forbidden_phrase"]
RUNS_PER_CELL = 10
MAX_ATTEMPTS = 4


def main() -> None:
    """Run the full statistical grid, saving every run to disk."""
    logging.basicConfig(level=logging.WARNING, format="%(message)s")

    total_runs = len(TARGETS) * len(OBJECTIVES) * RUNS_PER_CELL
    completed = 0

    for target_name in TARGETS:
        judge_name = JUDGE_FOR[target_name]
        target = get_adapter(target_name)
        judge = get_adapter(judge_name)

        for objective_name in OBJECTIVES:
            objective = OBJECTIVE_LIBRARY[objective_name]

            for run_index in range(1, RUNS_PER_CELL + 1):
                completed += 1
                print(
                    f"[{completed}/{total_runs}] "
                    f"{target.name} x {objective_name} run {run_index}/{RUNS_PER_CELL}..."
                )

                try:
                    result = run_adaptive_attack(
                        target, judge, objective, max_attempts=MAX_ATTEMPTS
                    )
                except Exception as exc:  # noqa: BLE001 - keep the batch alive
                    print(f"    run failed (skipped): {exc}")
                    continue

                label = f"statbench_{target.name}_{objective_name}"
                saved = save_run_result(result, label)
                broke = "BROKE" if result.succeeded else "held"
                print(f"    -> {broke}; saved {saved.name}")

    print()
    print("Benchmark run complete. Aggregate with:")
    print("  poetry run python src/avouch/eval/aggregate.py")


if __name__ == "__main__":
    main()
