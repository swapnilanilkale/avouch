# Taxonomy Alignment

This document situates Avouch within two established frameworks for AI risk and
evaluation: the **NIST AI Risk Management Framework (AI RMF 1.0)** and the
**UK AI Security Institute's** evaluation approach and its **Inspect** framework.
Its purpose is to express what Avouch contributes in the shared vocabulary the
field uses — and, just as importantly, to state plainly what Avouch does *not*
cover. Alignment claims here are deliberately conservative: Avouch is a focused
methodology demonstrator, not a comprehensive risk-evaluation suite.

## 1. Scope statement (what Avouch is, and is not)

Avouch is an **evaluation-methodology** tool. It exercises whether a model holds
a stated constraint under adversarial pressure, using *harmless proxy
objectives* (a benign secret to withhold, a benign phrase to avoid), plus two
auxiliary probes (sycophancy, framing-sensitivity). It validates its own judge
and reports findings with quantified uncertainty.

Avouch does **not** evaluate dangerous capabilities — it does not test
biosecurity, cybersecurity, autonomy, or persuasion risks, which are the
substantive focus of frontier-model safety institutes. Its proxies are chosen
precisely to avoid eliciting harmful content. Consequently, the alignment below
is with the **methodology and measurement** layers of these frameworks, not with
their threat taxonomies. A model that performs well against Avouch's proxies is
not thereby certified safe in any capability domain.

## 2. NIST AI RMF: the Measure function

The NIST AI RMF organizes AI risk management into four functions — **Govern,
Map, Measure, Manage**. Avouch operates within **Measure**, the function
concerned with analyzing, assessing, benchmarking, and monitoring AI risk using
quantitative, qualitative, or mixed-method tools. Avouch does not address Govern
(organizational risk culture and accountability), Map (context and risk
identification), or Manage (risk treatment and response); these are
organizational and lifecycle functions outside a measurement tool's remit.

Within Measure, Avouch's components map to specific categories:

| NIST Measure category | What it calls for | Avouch's contribution |
|---|---|---|
| **Measure 1** — appropriate metrics | Selecting methods and metrics for assessment | Break rate as a binomial proportion with 95% Wilson score confidence intervals; success criteria defined objectively (substring presence, or judgment against a known fact) |
| **Measure 2** — trustworthiness evaluation | Evaluating the system for trustworthy characteristics | Constraint-adherence under adversarial pressure (the core objectives); sycophancy (a *valid-and-reliable* / truthfulness concern); framing-sensitivity (a reasoning-robustness concern) |
| **Measure 3** — risk tracking | Mechanisms to track identified risks over time | Persisted run results and structured execution traces, enabling runs to be re-examined and compared rather than surviving only as logs |
| **Measure 4** — measurement effectiveness | Assessing whether the measurement itself is effective | Judge calibration against hand-labeled cases (agreement with human labels) and inter-judge agreement (Cohen's κ) — i.e. measuring the reliability of the evaluator itself |

The mapping to **Measure 4** is the one worth emphasizing. NIST's Measure
function explicitly calls for assessing whether measurement methods are
themselves effective; most automated red-teaming omits this step. Avouch's
judge-calibration work is, in NIST's terms, a Measure-4 activity — and it is the
framework's central methodological contribution.

A note on **Measure 2.11** (fairness and bias evaluation): Avouch does **not**
satisfy this. The framing-sensitivity probe tests answer-consistency under
reframing, not demographic fairness. Genuine bias evaluation in the NIST sense
remains out of scope (see the report's Future Work).

NIST also notes that Measure processes should include "associated measures of
uncertainty" and "comparisons to performance benchmarks." Avouch's use of
confidence intervals over repeated trials, rather than single-run verdicts, is a
direct instance of this guidance.

## 3. UK AISI and the Inspect framework

The UK AI Security Institute conducts pre-deployment evaluations of frontier
models, focused on dangerous capabilities (biosecurity, cybersecurity, autonomy,
persuasion), and has released **Inspect**, an open-source evaluation framework,
under an MIT licence. AISI defines red-teaming as attempting to elicit dangerous
capabilities from a model in a controlled environment.

Avouch's alignment with AISI is **methodological and architectural, not domain
coverage**. Avouch does not test AISI's dangerous-capability domains; it
substitutes harmless proxies for them. What aligns is *how* evaluation is
structured:

| Inspect concept | Avouch counterpart |
|---|---|
| Datasets (labeled examples) | Golden calibration cases; probe case sets |
| Scorers (decide pass/fail) | The judge agent, with judgment-based and substring-based scoring |
| Solvers / agents | The attacker, critic, and multi-turn conversational attacker |
| Multi-agent primitives | The LangGraph orchestrator coordinating attack–judge–critique |
| Evaluation logging / view tooling | The structured execution-trace layer |

Avouch's controlled-proxy red-teaming is the same *method* AISI describes —
adversarial elicitation in a controlled setting — applied to harmless objectives
rather than dangerous capabilities. The honest summary is: Avouch demonstrates,
on safe proxies, the evaluation methodology that institutes like AISI apply to
genuine capability risks.

A natural extension (noted as future work) is that Avouch's objectives and
scoring could be ported to run as Inspect tasks, which would let them execute
within a widely-used, institutionally-maintained harness.

## 4. Summary

Avouch aligns with the **Measure** function of the NIST AI RMF — most
distinctively at Measure 4, evaluating the evaluator — and with the
**methodology and architecture** of AISI's Inspect framework. It does not
address the governance, mapping, or management functions of the NIST framework,
nor the dangerous-capability domains that are the substance of frontier-model
safety evaluation. Stated plainly: Avouch is a rigorous demonstration of
evaluation *method* on harmless proxies, positioned within — but not claiming to
span — the frameworks the field uses.
