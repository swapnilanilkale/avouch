"""View a saved Avouch trace in a readable form.

Run with:
    poetry run python src/avouch/tracing/view_trace.py [trace_file_or_substring]

With no argument, shows the most recent trace in the traces/ directory.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TRACES_DIR = Path("traces")


def _find_trace(arg: str | None) -> Path | None:
    """Locate a trace file by substring, or the most recent if no arg given."""
    files = sorted(TRACES_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not files:
        return None
    if not arg:
        return files[-1]
    matches = [f for f in files if arg.lower() in f.name.lower()]
    return matches[-1] if matches else None


def main() -> None:
    """Pretty-print a saved trace."""
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    path = _find_trace(arg)

    if path is None:
        print("No matching trace found in traces/.")
        return

    data = json.loads(path.read_text(encoding="utf-8"))

    print("=" * 72)
    print(f"TRACE  {data['trace_id']}   ({data['run_kind']})")
    print(f"File   {path.name}")
    created = datetime.fromtimestamp(data["created_at"], tz=timezone.utc)
    print(f"Time   {created.isoformat()}")
    if data.get("metadata"):
        print("Metadata:")
        for k, v in data["metadata"].items():
            print(f"  {k}: {v}")
    print("=" * 72)

    for i, event in enumerate(data["events"], start=1):
        dur = (
            f"  ({event['duration_ms']:.0f} ms)"
            if event.get("duration_ms") is not None
            else ""
        )
        print(f"\n[{i}] {event['step']}{dur}")
        for k, v in event["data"].items():
            text = str(v)
            if len(text) > 200:
                text = text[:200] + " ..."
            print(f"    {k}: {text}")

    print("\n" + "=" * 72)
    print(f"Total events: {len(data['events'])}")
    print("=" * 72)


if __name__ == "__main__":
    main()
