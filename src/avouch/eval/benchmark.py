"""Benchmark script: run Avouch across multiple targets and objectives.

For each (target, objective) combination, runs an adaptive attack with a fixed
judge, saves the result to disk, and prints a summary table of how each target
held up. Intended to produce the numbers reported in the technical report.

Run with:  poetry run python src/avouch/eval/benchmark.py
"""

import logging

from avouch.adapters.registry import get_adapter
from avouch.agents.objectives import OBJECTIVE_LIBRARY
from avouch.eval.persistence import save_run_result
from avouch.orchestrator.run import run_adaptive_attack

# Targets to benchmark. Judge is fixed and uses a different family per target.
TARGETS = ["groq", "cerebras"]
JUDGE_FOR = {
    "groq": "cerebras",
    "cerebras": "groq",
}
OBJECTIVES = ["secret_word", "forbidden_phrase"]
MAX_ATTEMPTS = 4


def main() -> None:
    """Run the full benchmark grid and print a summary table."""
    logging.basicConfig(level=logging.WARNING, format="%(message)s")

    rows = []

    for target_name in TARGETS:
        judge_name = JUDGE_FOR[target_name]
        target = get_adapter(target_name)
        judge = get_adapter(judge_name)

        for objective_name in OBJECTIVES:
            objective = OBJECTIVE_LIBRARY[objective_name]
            print(
                f"Running: target={target.name} judge={judge.name} "
                f"objective={objective_name} ..."
            )

            result = run_adaptive_attack(
                target, judge, objective, max_attempts=MAX_ATTEMPTS
            )

            held = sum(1 for v in result.verdicts if v.outcome.value != "success")
            total = len(result.verdicts)
            saved = save_run_result(result, f"{target.name}_{objective_name}")

            rows.append(
                {
                    "target": target.name,
                    "judge": judge.name,
                    "objective": objective_name,
                    "held": held,
                    "total": total,
                    "broke": result.succeeded,
                    "file": saved.name,
                }
            )
            print(f"  -> held {held}/{total} attempts; saved {saved.name}")

    print()
    print("=" * 78)
    print("BENCHMARK SUMMARY")
    print("=" * 78)
    print(f"{'Target':<32}{'Objective':<18}{'Resisted':<12}{'Broke?':<8}")
    print("-" * 78)
    for r in rows:
        print(
            f"{r['target']:<32}{r['objective']:<18}"
            f"{str(r['held']) + '/' + str(r['total']):<12}"
            f"{'YES' if r['broke'] else 'no':<8}"
        )
    print("=" * 78)


if __name__ == "__main__":
    main()
