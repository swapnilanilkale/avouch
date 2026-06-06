"""MCP server exposing Avouch's capabilities as Model Context Protocol tools.

This is a thin, standalone wrapper: it imports Avouch's existing functions and
exposes a small set as MCP tools over stdio, so an MCP-compatible client (e.g.
Claude Desktop, or the MCP Inspector) can invoke them. It adds no new logic.

Run (development / inspector):
    poetry run mcp dev mcp_server.py

Or as a stdio server (e.g. configured in an MCP client):
    poetry run python mcp_server.py
"""

from mcp.server.fastmcp import FastMCP

from avouch.adapters.registry import available_providers, get_adapter
from avouch.agents.objectives import OBJECTIVE_LIBRARY
from avouch.eval.harness import evaluate_judge

mcp = FastMCP("avouch")


@mcp.tool()
def list_objectives() -> list[dict[str, str]]:
    """List the harmless proxy objectives available for red-teaming.

    Returns a list of objectives, each with its key and description.
    """
    return [
        {"key": key, "description": obj.description}
        for key, obj in sorted(OBJECTIVE_LIBRARY.items())
    ]


@mcp.tool()
def list_providers() -> list[str]:
    """List the LLM providers available as attack targets or judges."""
    return available_providers()


@mcp.tool()
def run_judge_eval(judge: str = "groq") -> dict:
    """Run the judge calibration against the golden cases and return a summary.

    Args:
        judge: The provider whose model will act as the judge (default "groq").

    Returns:
        A summary dict with accuracy, agreement counts, and error breakdown.
    """
    judge_adapter = get_adapter(judge)
    report = evaluate_judge(judge_adapter)
    return {
        "judge": judge_adapter.name,
        "accuracy_pct": round(report.accuracy * 100),
        "agreements": report.agreements,
        "total": report.total,
        "missed_breaches": report.missed_breaches,
        "false_alarms": report.false_alarms,
    }


if __name__ == "__main__":
    mcp.run()
