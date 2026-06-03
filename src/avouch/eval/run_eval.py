"""Runnable script to evaluate the judge against the golden cases.

Run with:  poetry run python src/avouch/eval/run_eval.py
"""

import logging

from avouch.adapters.registry import get_adapter
from avouch.eval.harness import evaluate_judge


def main() -> None:
    """Evaluate the default judge and print a calibration report."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    judge = get_adapter("groq")
    report = evaluate_judge(judge)

    print("=" * 60)
    print("JUDGE CALIBRATION REPORT")
    print("=" * 60)
    print(f"Judge model : {judge.name}")
    print(
        f"Accuracy    : {report.accuracy * 100:.0f}% "
        f"({report.agreements}/{report.total})"
    )
    print(f"Missed breaches (dangerous): {report.missed_breaches}")
    print(f"False alarms               : {report.false_alarms}")
    print("-" * 60)
    for r in report.results:
        status = "OK" if r.agreed else "<-- MISMATCH"
        print(
            f"  {r.case_id:28s} expected={r.expected.value:8s} "
            f"actual={r.actual.value:8s} {status}"
        )
        if not r.agreed:
            print(f"      judge reasoning: {r.reasoning}")
    print("=" * 60)


if __name__ == "__main__":
    main()
