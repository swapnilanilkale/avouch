"""Run the framing-sensitivity probe against a target and print results.

Run with:
    poetry run python src/avouch/agents/run_framing.py [target] [judge]
"""

import sys

from avouch.adapters.registry import get_adapter
from avouch.agents.framing_probe import FramingProbe


def main() -> None:
    """Run the framing probe and print a per-case summary."""
    target_name = sys.argv[1] if len(sys.argv) > 1 else "groq"
    judge_name = sys.argv[2] if len(sys.argv) > 2 else "cerebras"

    target = get_adapter(target_name)
    judge = get_adapter(judge_name)

    print(f"Target: {target.name}")
    print(f"Judge : {judge.name}")
    print("Running framing-sensitivity probe...")
    print()

    results = FramingProbe(target, judge).run()

    flipped = sum(1 for r in results if r.outcome.value == "success")
    print("=" * 70)
    print(f"FRAMING PROBE: inconsistent on {flipped}/{len(results)} cases")
    print("=" * 70)
    for r in results:
        label = (
            "INCONSISTENT" if r.outcome.value == "success" else r.outcome.value.upper()
        )
        print(f"\n{r.case_id} -> {label}")
        print(f"  judge: {r.reasoning}")
        print(f"  A: {r.response_a[:160]}")
        print(f"  B: {r.response_b[:160]}")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
