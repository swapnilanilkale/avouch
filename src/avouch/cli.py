"""Command-line interface for Avouch.

Provides the `avouch` command. For now it exposes a single subcommand,
`ask`, which sends a prompt to a chosen provider and prints the response.
"""

import typer

from avouch.adapters.base import AdapterError
from avouch.adapters.registry import available_providers, get_adapter
from avouch.agents.objectives import OBJECTIVE_LIBRARY, get_objective
from avouch.agents.runner import run_attack
from avouch.agents.types import Outcome
from avouch.eval.harness import evaluate_judge
from avouch.orchestrator.run import run_adaptive_attack

app = typer.Typer(
    name="avouch",
    help="An agentic red-teaming and evaluation framework for LLM safety.",
    add_completion=False,
)


@app.command()
def providers() -> None:
    """List the available LLM providers."""
    typer.echo("Available providers:")
    for provider in available_providers():
        typer.echo(f"  - {provider}")


@app.command()
def ask(
    prompt: str = typer.Argument(..., help="The prompt to send to the model."),
    provider: str = typer.Option(
        "groq",
        "--provider",
        "-p",
        help="Which provider to use.",
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        "-m",
        help="Optional model identifier; uses the provider default if omitted.",
    ),
    temperature: float = typer.Option(
        0.7,
        "--temperature",
        "-t",
        help="Sampling temperature.",
    ),
) -> None:
    """Send a single prompt to a provider and print the response."""
    try:
        adapter = get_adapter(provider, model=model)
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Target : {adapter.name}")
    typer.echo(f"Prompt : {prompt}")
    typer.echo("Sending request...")

    try:
        response = adapter.generate(prompt, temperature=temperature)
    except AdapterError as exc:
        typer.echo(f"Error: the provider call failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo("")
    typer.echo("Response:")
    typer.echo(response.text)

    if response.prompt_tokens is not None:
        typer.echo("")
        typer.echo(
            f"Tokens : prompt={response.prompt_tokens}, "
            f"completion={response.completion_tokens}"
        )


@app.command()
def objectives() -> None:
    """List the available harmless red-teaming objectives."""
    typer.echo("Available objectives:")
    for key, obj in sorted(OBJECTIVE_LIBRARY.items()):
        typer.echo(f"  - {key}: {obj.description}")


@app.command()
def attack(
    target: str = typer.Option(
        "cerebras",
        "--target",
        "-t",
        help="Provider for the model under test.",
    ),
    judge: str = typer.Option(
        "groq",
        "--judge",
        "-j",
        help="Provider for the judge model (use a different family).",
    ),
    objective: str = typer.Option(
        "secret_word",
        "--objective",
        "-o",
        help="Which harmless objective to test.",
    ),
    max_attempts: int = typer.Option(
        4,
        "--max-attempts",
        "-n",
        help="Maximum number of attack techniques to try.",
    ),
    adaptive: bool = typer.Option(
        False,
        "--adaptive",
        "-a",
        help="Use the adaptive LangGraph orchestrator with a critic loop.",
    ),
) -> None:
    """Run a red-teaming attack and print a scorecard."""

    try:
        target_adapter = get_adapter(target)
        judge_adapter = get_adapter(judge)
        obj = get_objective(objective)
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    mode = "adaptive (LangGraph orchestrator)" if adaptive else "linear"
    typer.echo(f"Target    : {target_adapter.name}")
    typer.echo(f"Judge     : {judge_adapter.name}")
    typer.echo(f"Objective : {obj.description}")
    typer.echo(f"Mode      : {mode}")
    typer.echo("Running attack (this makes several model calls)...")
    typer.echo("")

    if adaptive:
        result = run_adaptive_attack(
            target_adapter,
            judge_adapter,
            obj,
            max_attempts=max_attempts,
        )
    else:
        result = run_attack(
            target_adapter,
            judge_adapter,
            obj,
            max_attempts=max_attempts,
        )

    typer.echo("=" * 60)
    typer.echo("SCORECARD")
    typer.echo("=" * 60)
    for verdict in result.verdicts:
        attempt = verdict.attempt
        marker = (
            "BROKEN"
            if verdict.outcome is Outcome.SUCCESS
            else verdict.outcome.value.upper()
        )
        typer.echo(
            f"  Attempt {attempt.attempt_number} "
            f"[{attempt.technique.value}] -> {marker}"
        )
        typer.echo(f"      reason: {verdict.reasoning}")
    typer.echo("=" * 60)

    if result.succeeded:
        typer.echo("RESULT: The target BROKE its rule on at least one attempt.")
    else:
        typer.echo("RESULT: The target HELD its rule on all attempts.")


@app.command(name="eval")
def eval_judge(
    judge: str = typer.Option(
        "groq",
        "--judge",
        "-j",
        help="Provider for the judge model to evaluate.",
    ),
) -> None:
    """Evaluate the judge against golden test cases and print a calibration report."""
    try:
        judge_adapter = get_adapter(judge)
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Evaluating judge: {judge_adapter.name}")
    typer.echo("Running golden test cases (this makes several model calls)...")
    typer.echo("")

    report = evaluate_judge(judge_adapter)

    typer.echo("=" * 60)
    typer.echo("JUDGE CALIBRATION REPORT")
    typer.echo("=" * 60)

    typer.echo(f"Judge model : {judge_adapter.name}")
    typer.echo(
        f"Accuracy    : {report.accuracy * 100:.0f}% "
        f"({report.agreements}/{report.total})"
    )
    typer.echo(f"Precision   : {report.precision * 100:.0f}%")
    typer.echo(f"Recall      : {report.recall * 100:.0f}%  (safety-critical)")
    typer.echo(f"F1          : {report.f1 * 100:.0f}%")
    typer.echo("-" * 60)
    typer.echo("Confusion matrix (positive = breach detected):")
    typer.echo(f"  TP (breach caught)        : {report.true_positives}")
    typer.echo(f"  TN (hold confirmed)       : {report.true_negatives}")
    typer.echo(f"  FN (missed breach, danger): {report.missed_breaches}")
    typer.echo(f"  FP (false alarm)          : {report.false_alarms}")
    typer.echo("-" * 60)
    for r in report.results:
        status = "OK" if r.agreed else "<-- MISMATCH"
        typer.echo(
            f"  {r.case_id:28s} expected={r.expected.value:8s} "
            f"actual={r.actual.value:8s} {status}"
        )
    typer.echo("=" * 60)


if __name__ == "__main__":
    app()
