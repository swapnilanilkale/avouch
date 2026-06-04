"""Inspect a saved benchmark run result by filename substring.

Run with:
    poetry run python src/avouch/eval/inspect_run.py forbidden_phrase llama
"""

import json
import sys
from pathlib import Path

RESULTS_DIR = Path("results")


def main() -> None:
    """Print the verdicts and target responses for a matching saved run."""
    substrings = sys.argv[1:]
    files = sorted(RESULTS_DIR.glob("*.json"))
    matches = [f for f in files if all(s.lower() in f.name.lower() for s in substrings)]

    if not matches:
        print(f"No result file matching: {substrings}")
        return

    target = matches[-1]  # most recent match
    data = json.loads(target.read_text(encoding="utf-8"))

    print("=" * 70)
    print("FILE:", target.name)
    print("Target:", data["target_name"])
    print("Objective:", data["objective_description"])
    print("Overall broke:", data["succeeded"])
    print("=" * 70)

    for v in data["verdicts"]:
        attempt = v["attempt"]
        print()
        print(
            f"Attempt {attempt['attempt_number']} [{attempt['technique']}] -> {v['outcome'].upper()}"
        )
        print(f"  judge reasoning: {v['reasoning']}")
        print(f"  target response: {attempt['target_response'][:500]}")


if __name__ == "__main__":
    main()
