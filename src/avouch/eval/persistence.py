"""Persistence for red-teaming run results.

Serializes RunResult objects to JSON so benchmark runs are recorded on disk
and can be reloaded for reporting. The raw provider response objects are not
serialized (they are large and provider-specific); only the normalized fields
needed for analysis are kept.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from avouch.agents.types import RunResult

RESULTS_DIR = Path("results")


def _verdict_to_dict(verdict) -> dict:
    """Convert a Verdict (with nested attempt and enums) to plain dict."""
    return {
        "outcome": verdict.outcome.value,
        "reasoning": verdict.reasoning,
        "attempt": {
            "technique": verdict.attempt.technique.value,
            "attack_prompt": verdict.attempt.attack_prompt,
            "target_response": verdict.attempt.target_response,
            "attempt_number": verdict.attempt.attempt_number,
        },
    }


def run_result_to_dict(result: RunResult) -> dict:
    """Convert a RunResult into a JSON-serializable dictionary."""
    return {
        "objective_description": result.objective.description,
        "target_name": result.target_name,
        "succeeded": result.succeeded,
        "num_attempts": len(result.attempts),
        "verdicts": [_verdict_to_dict(v) for v in result.verdicts],
    }


def save_run_result(result: RunResult, label: str) -> Path:
    """Save a RunResult to a timestamped JSON file under the results directory.

    Args:
        result: The run result to save.
        label: A short label included in the filename (e.g. target+objective).

    Returns:
        The path to the written file.
    """
    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_label = label.replace(":", "_").replace("/", "_").replace(" ", "_")
    path = RESULTS_DIR / f"{timestamp}_{safe_label}.json"

    path.write_text(json.dumps(run_result_to_dict(result), indent=2), encoding="utf-8")
    return path
