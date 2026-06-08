# Avouch

**An agentic framework for adaptive LLM red-teaming with calibrated evaluation.**

Avouch automates red-teaming of large language models using a team of
specialized AI agents, and — unlike most red-teaming tooling — it *validates
its own judge* against hand-labeled cases before trusting its results.

> ✅ Actively developed. v1 (below) is complete and working; v2 extensions
> (expanded calibration set, multi-turn attacks, statistical benchmarking,
> tracing, MCP integration) are also completed in subsequent phases.

## What it does

Given any target model, Avouch runs an adaptive red-teaming cycle:

- An **attacker agent** probes the target with escalating, documented
  adversarial framings (direct, role-play, hypothetical, instruction-override).
- An independent **judge agent** — drawn from a *different model family* to
  reduce correlated blind spots — rules on whether each attempt broke the
  target's rule, with explained reasoning.
- A **critic agent** revises strategy between attempts, and a **LangGraph
  orchestrator** loops the cycle adaptively until success or exhaustion.

To enable safe, open development, Avouch operates only on **harmless proxy
objectives** — benign secret-extraction tasks (e.g. "never reveal this word")
that exercise the full attack machinery without ever eliciting harmful content.

## Why it's different

Most automated red-teaming relies on an evaluator that is never itself
validated. Avouch treats its judge as an object of measurement: a curated set
of hand-labeled cases measures how often the judge agrees with human labels,
separating dangerous *missed breaches* from benign *false alarms*.

## Architecture
Target Adapters (Groq · Cerebras · Gemini · OpenRouter)  ← one unified interface

│

Orchestrator (LangGraph state graph, critic loop)

┌────┴─────┐

Attacker → Judge → Critic   →   Scorecard + saved results

│

Eval Harness (golden cases → calibration metrics)

## Quick start

Requires Python 3.11+ and [Poetry](https://python-poetry.org/).

```bash
git clone git@github.com:swapnilanilkale/avouch.git
cd avouch
poetry install
cp .env.example .env   # then add your free-tier API keys
```

Free API keys (no card required): [Groq](https://console.groq.com),
[Cerebras](https://cloud.cerebras.ai). Gemini and OpenRouter adapters are also
included.

## Usage

```bash
# List providers and objectives
poetry run avouch providers
poetry run avouch objectives

# Run a red-teaming attack (adaptive mode uses the LangGraph orchestrator)
poetry run avouch attack --target cerebras --judge groq --objective secret_word --adaptive

# Validate the judge against golden test cases
poetry run avouch eval

# Launch the web UI
poetry run streamlit run streamlit_app.py
```

## Project status

| Capability | Status |
|---|---|
| Provider-agnostic adapter layer (4 providers) | ✅ |
| Attacker + judge agents | ✅ |
| LangGraph adaptive orchestrator with critic loop | ✅ |
| Judge calibration harness (golden cases) | ✅ |
| Streamlit UI | ✅ |
| Expanded calibration set + inter-judge agreement | ✅ v2 |
| Multi-turn conversational attacker | ✅ v2 |
| Statistical benchmarking (success rates, CIs) | ✅ v2 |
| Structured tracing + MCP server | ✅ v2 |

## Responsible use

Avouch is designed for safe, open AI-safety research. It operates exclusively
on harmless proxy objectives and does not seek or produce harmful content.

## License

See [LICENSE](LICENSE).
