"""Structured execution traces for Avouch runs.

A Trace is an ordered, inspectable record of the steps a run took: each agent
call, its inputs and outputs, timings, and decisions. Unlike ephemeral log
lines, a trace is structured data written to disk, so any run can be examined
after the fact -- which matters when the purpose of the system is to produce
auditable evidence about a model's behavior.

This is a lightweight, dependency-free tracer. The trace schema is kept clean
and general so that an exporter to an external observability backend (e.g.
OpenTelemetry / Arize Phoenix) could be added later without changing callers.
"""

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

TRACES_DIR = Path("traces")


@dataclass
class TraceEvent:
    """A single step within a traced run.

    Attributes:
        step: A short name for the step (e.g. "attack_compose", "target_call",
            "judge_verdict", "route").
        data: Structured details for the step (any JSON-serializable dict).
        timestamp: Unix time when the event was recorded.
        duration_ms: Optional wall-clock duration of the step, in milliseconds.
    """

    step: str
    data: dict
    timestamp: float = field(default_factory=time.time)
    duration_ms: float | None = None


@dataclass
class Trace:
    """An ordered record of all events in a single run.

    Attributes:
        trace_id: A unique identifier for this trace.
        run_kind: What kind of run this is (e.g. "multiturn", "adaptive").
        metadata: Free-form context (target name, judge name, objective, etc.).
        events: The ordered list of events recorded during the run.
        created_at: Unix time when the trace was started.
    """

    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    run_kind: str = ""
    metadata: dict = field(default_factory=dict)
    events: list[TraceEvent] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        """Convert the trace to a JSON-serializable dictionary."""
        return asdict(self)

    def save(self, label: str = "") -> Path:
        """Write the trace to disk as JSON and return the path.

        Args:
            label: An optional short label included in the filename.

        Returns:
            The path to the written trace file.
        """
        TRACES_DIR.mkdir(exist_ok=True)
        safe_label = (
            label.replace(":", "_").replace("/", "_").replace(" ", "_")
            if label
            else self.run_kind
        )
        path = TRACES_DIR / f"{self.trace_id}_{safe_label}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path


class Tracer:
    """Collects trace events during a run.

    A Tracer is passed into a run; the run calls record() (or the timed()
    context manager) at each step. When the run finishes, the accumulated
    Trace can be saved. If no Tracer is provided to a run, tracing is simply
    skipped -- existing behavior is unchanged.
    """

    def __init__(self, run_kind: str = "", metadata: dict | None = None) -> None:
        """Create a tracer.

        Args:
            run_kind: A label for the kind of run being traced.
            metadata: Free-form context to attach to the trace.
        """
        self.trace = Trace(run_kind=run_kind, metadata=metadata or {})

    def record(self, step: str, data: dict, duration_ms: float | None = None) -> None:
        """Record a single event into the trace.

        Args:
            step: A short name for the step.
            data: Structured details for the step.
            duration_ms: Optional duration of the step in milliseconds.
        """
        self.trace.events.append(
            TraceEvent(step=step, data=data, duration_ms=duration_ms)
        )

    def save(self, label: str = "") -> Path:
        """Save the underlying trace to disk."""
        return self.trace.save(label=label)
