"""Command-line interface for Avouch.

Provides the `avouch` command. For now it exposes a single subcommand,
`ask`, which sends a prompt to a chosen provider and prints the response.
"""

import typer

from avouch.adapters.base import AdapterError
from avouch.adapters.registry import available_providers, get_adapter

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


if __name__ == "__main__":
    app()