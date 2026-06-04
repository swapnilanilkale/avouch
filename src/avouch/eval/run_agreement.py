"""Run inter-judge agreement (Cohen's kappa) over the golden cases.

Run with:  poetry run python src/avouch/eval/run_agreement.py
"""

import logging

from avouch.adapters.registry import get_adapter
from avouch.eval.agreement import compute_agreement


def main() -> None:
    """Compute and print inter-judge agreement between two judge families."""
    logging.basicConfig(level=logging.WARNING, format="%(message)s")

    judge_a = get_adapter("groq")
    judge_b = get_adapter("cerebras")

    print(f"Judge A: {judge_a.name}")
    print(f"Judge B: {judge_b.name}")
    print("Running both judges over the golden cases (this makes many calls)...")
    print()

    report = compute_agreement(judge_a, judge_b)

    print("=" * 70)
    print("INTER-JUDGE AGREEMENT REPORT")
    print("=" * 70)
    print(f"Judge A          : {report.judge_a_name}")
    print(f"Judge B          : {report.judge_b_name}")
    print(f"Cases            : {len(report.results)}")
    print(f"Observed agreement: {report.observed_agreement * 100:.0f}%")
    print(f"Expected (chance) : {report.expected_agreement * 100:.0f}%")
    print(f"Cohen's kappa    : {report.kappa:.2f} ({report.interpretation})")
    print("-" * 70)
    print("Disagreements:")
    any_disagreement = False
    for r in report.results:
        if not r.agreed:
            any_disagreement = True
            print(f"  {r.case_id:28s} A={r.judge_a.value:8s} B={r.judge_b.value:8s}")
    if not any_disagreement:
        print("  (none -- the judges agreed on every case)")
    print("=" * 70)


if __name__ == "__main__":
    main()
