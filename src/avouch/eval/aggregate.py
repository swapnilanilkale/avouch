"""Aggregate saved statistical-benchmark runs into a summary with CIs.

Reads all 'statbench_' result files from the results directory, groups them by
(target, objective), and reports the break rate with a 95% Wilson confidence
interval per cell. Resumable: it summarizes whatever runs are on disk.

Run with:  poetry run python src/avouch/eval/aggregate.py
"""

import json
from collections import defaultdict
from pathlib import Path

from avouch.eval.statistics import wilson_interval

RESULTS_DIR = Path("results")


def main() -> None:
    """Aggregate saved statbench runs and print a summary table."""
    files = sorted(RESULTS_DIR.glob("*statbench_*.json"))
    if not files:
        print(
            "No statbench result files found in results/. Run stat_benchmark.py first."
        )
        return

    # Group runs by (target, objective); record break/hold for each.
    cells: dict[tuple[str, str], list[bool]] = defaultdict(list)

    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        target = data["target_name"]
        objective = data["objective_description"]
        cells[(target, objective)].append(bool(data["succeeded"]))

    print("=" * 90)
    print("STATISTICAL BENCHMARK SUMMARY")
    print("=" * 90)
    print(f"Total saved runs: {sum(len(v) for v in cells.values())}")
    print("-" * 90)
    print(f"{'Target':<30}{'Objective':<42}{'Break rate (95% CI)':<28}")
    print("-" * 90)

    for (target, objective), outcomes in sorted(cells.items()):
        breaks = sum(1 for o in outcomes if o)
        est = wilson_interval(breaks, len(outcomes))
        obj_short = objective[:40]
        print(f"{target:<30}{obj_short:<42}{est.as_pct():<28}")

    print("=" * 90)


if __name__ == "__main__":
    main()
