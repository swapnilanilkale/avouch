# Avouch: An Agentic Framework for Adaptive LLM Red-Teaming with Calibrated, Statistically-Grounded Evaluation

**Swapnil Anil Kale**
*Independent Research · June 2026*

---

## Abstract

Red-teaming — probing language models for safety failures through adversarial inputs — is central to AI safety practice, yet most red-teaming is manual or relies on closed-source tooling, and the evaluators that judge attack outcomes are rarely validated or applied with statistical rigor. We present Avouch, an open-source agentic framework that automates adaptive red-teaming against arbitrary language models and treats both its evaluator and its results as objects of measurement. Avouch couples a provider-agnostic model interface with a multi-agent workflow: an attacker escalates through documented adversarial framings, an independent judge from a different model family rules on each attempt, and a critic revises strategy between attempts via a state-graph orchestrator. To enable safe, open development, all attacks target *harmless proxy objectives* — benign rule-following tasks that exercise the full attack machinery without eliciting harmful content. We validate the judge against 26 hand-labeled cases (96% agreement with human labels; zero false alarms) and against a second judge of a different family (Cohen's κ = 0.77, "substantial"), finding that residual disagreement is confined to genuinely ambiguous cases. A statistical benchmark of two models, each cell run ten times with Wilson confidence intervals, exposes a result that single-run benchmarking misses: one model resisted on every trial (0%, 95% CI 0–28%) while the other broke roughly half the time (50%, 95% CI 24–76%) on the same objective a single prior run had reported as fully robust. Avouch demonstrates that credible, adaptive LLM red-teaming can be built openly and safely, with evaluators whose reliability is measured rather than assumed and findings reported with quantified uncertainty.

---

## 1. Introduction

As language models are deployed in increasingly consequential settings, systematically discovering their safety failures before deployment has become a core competency for developers and oversight bodies. *Red-teaming* — deliberately probing a system with adversarial inputs to surface harmful behaviors, rule violations, or security weaknesses — is the principal method by which this is done, and national bodies such as the UK AI Safety Institute, alongside the safety teams of frontier laboratories, treat structured red-teaming and evaluation as central to their mandate.

The practice faces three persistent gaps. First, much red-teaming remains **manual** — skilled humans crafting adversarial prompts by hand — which does not scale and is hard to reproduce. Second, the most capable automated systems are **closed-source and internal** to a small number of laboratories, limiting access for independent and academic researchers. Third, and most subtle, automated red-teaming depends on an *evaluator* that decides whether an attack succeeded, yet these evaluators are **rarely validated**, and their verdicts are often reported from a **single run** despite the stochasticity of the systems involved. A red-teaming result is only as trustworthy as the judge that produced it and the sampling that surrounds it; an unvalidated judge can silently miss real failures, and a single unrepresentative run can misclassify a frequently-vulnerable model as robust.

This report presents **Avouch**, an open-source framework addressing these gaps through four contributions.

**An adaptive multi-agent architecture.** Avouch coordinates an attacker, an independent judge, and a critic that revises strategy from observed failures, using a state-graph orchestrator that loops adaptively until success or exhaustion. This moves beyond static, single-shot attack libraries toward a system that responds to a target's defenses within a session, and whose execution path is fully traceable.

**A safe-by-design methodology.** Rather than eliciting genuinely harmful content, Avouch operates on *harmless proxy objectives*: a target is given a benign confidential rule, and success is the objectively-verifiable breaking of that rule. This exercises the complete attack-and-evaluation machinery while producing no harmful output, making the framework safe for open development and use by researchers without institutional safety infrastructure.

**A validated judge.** Avouch treats its evaluator as an object of measurement. Against 26 hand-labeled cases the judge agreed with human labels 96% of the time with zero false alarms; against an independent judge of a different model family it achieved substantial agreement (κ = 0.77), with all disagreement falling on a priori ambiguous cases. This calibration is what licenses trust in the framework's findings.

**Statistically-grounded benchmarking.** Avouch runs each evaluation cell multiple times and reports break rates with Wilson confidence intervals rather than single-run verdicts. In our benchmark this distinction was decisive: a cell that a single run had reported as fully robust showed a 50% break rate (95% CI 24–76%) over ten runs, demonstrating concretely that single-run red-teaming benchmarks can mislead.

We describe Avouch's design and methodology, report judge-calibration and benchmark results with their limitations, and outline a roadmap for extension. Avouch is released as open source.

---

## 2. Methodology

Avouch's design rests on three methodological commitments, each chosen to make the framework's results trustworthy and its operation safe. We state them explicitly here because they, more than any implementation detail, determine whether the framework's findings can be believed.

### 2.1 Harmless proxy objectives

The central decision is to never target genuinely harmful behavior. A naive automated red-teaming system attempts to elicit dangerous content and reports its success rate at doing so; such a system is itself a generator of harmful outputs, and is correspondingly hazardous to develop, publish, or run. Avouch instead substitutes a *proxy*: the target is given a benign confidential rule — withhold a secret word, never utter a particular phrase — and an attack succeeds exactly when that rule is broken.

This substitution is sound for two reasons. First, the *mechanism* under test is identical to that of harmful red-teaming: the same adversarial framings, the same multi-attempt adaptive pressure, the same question of whether a model holds a stated constraint under manipulation. A model's tendency to abandon an instruction when pressed is what we are measuring, and the proxy exercises exactly that tendency. Second, success is *objectively verifiable* — the protected token either appears in the output or it does not — which makes outcomes reproducible in a way that judgments about the harmfulness of free-form content are not. The proxy thus buys both safety and measurement precision, at the cost of not testing any specific harmful capability directly. We regard this as the correct trade for an open framework, and discuss its limits in Section 5.

### 2.2 Calibrate the evaluator before trusting it

Every result Avouch produces passes through the judge, so the judge's reliability bounds the reliability of everything else. We therefore treat calibration as a precondition, not an afterthought: the judge is validated against human-labeled cases *before* its verdicts on novel attacks are trusted. The calibration set is constructed to include not only clear cases but deliberately ambiguous ones — a protected phrase quoted inside a refusal, a near-miss hint, a partial fragment — because a judge that only handles obvious cases is untested precisely where judgment is hard.

We distinguish two error types and treat them asymmetrically. A *missed breach* (the judge failing to flag a genuine rule-break) is the consequential error, since it would cause a vulnerable model to be reported as safe; a *false alarm* is comparatively benign. Reporting these separately, rather than a single accuracy figure, reflects the asymmetric cost structure of the safety setting the framework is built for.

### 2.3 Two checks on judgment: human agreement and inter-rater agreement

Agreement with a single human labeler establishes that the judge tracks one reviewer's intent, but not that its verdicts are robust to who — or what — is judging. We therefore add a second, independent check: a judge from a different model family rules on the same cases, and we measure inter-judge agreement using Cohen's kappa, which corrects for the agreement expected by chance given each judge's marginal tendencies. We report the standard qualitative interpretation (Landis and Koch, 1977) alongside the raw coefficient. High inter-judge agreement on clear cases, with disagreement confined to ambiguous ones, is the signature we treat as evidence that verdicts are robust rather than artifacts of one model's idiosyncrasies.

### 2.4 Report distributions, not single runs

Because both the attacker (operating at non-zero sampling temperature) and the target are stochastic, a single attack run samples once from a distribution of possible outcomes. Treating that single sample as the model's behavior is unsound, and — as Section 4 shows — can invert the conclusion. Avouch therefore runs each evaluation cell repeatedly and reports the break rate as a proportion with a 95% Wilson score confidence interval. The Wilson interval is chosen over the normal approximation because it remains valid for small samples and for proportions near zero or one, which is the regime in which robustness evaluations operate.

---

## 3. System Design

Avouch separates four concerns into distinct layers: model access, agents, orchestration, and evaluation. The separation is deliberate — it is what allows the model under test, the judge, and the attack strategy to vary independently, and it is what made the system robust to the provider instability we encountered during development.

### 3.1 Model access

Red-teaming requires probing arbitrary models, so the framework commits to no single provider. A single abstract interface, `TargetAdapter`, defines the only operations the rest of the system depends on: submit a prompt and receive a normalized response, and report a provider-and-model identifier. Concrete adapters implement this contract for Groq, Cerebras, Google Gemini, and OpenRouter, each translating between the common interface and a provider's SDK — normalizing responses and mapping provider-specific exceptions onto a single error type. No component above this layer references a provider SDK; the target is a runtime argument, resolved through a name-to-adapter registry.

This design was tested by circumstance rather than chosen for elegance. Of the four providers, two proved unsuitable as default backends on their free tiers — one gated access behind billing activation, the other routed free models through a shared backend that returned rate-limit errors under sustained load. In both cases the change was confined to a single line, because no other component was coupled to the provider. We treat this as evidence for the design rather than an incidental detail: a red-teaming framework is only useful insofar as it can follow the models worth testing, and model availability is not stable.

Each adapter wraps its network call in a shared exponential-backoff retry policy. This was a practical necessity, not a precaution; at the call volumes generated by repeated benchmarking, free-tier rate limits were the common case, and the retry layer is what allowed long runs to complete.

### 3.2 Agents

Three agents share a small set of typed objects — objectives, attempts, verdicts — and each does one thing.

The attacker issues adversarial prompts under a sequence of framings: direct request, role-play, hypothetical, and simulated instruction-override. We stress that these framings are drawn from the public literature and are intentionally generic; the framework makes no claim to novel attacks, and against well-aligned targets most framings are expected to fail. The research contribution is the surrounding apparatus — adaptation and validated evaluation — not the prompts themselves.

The judge decides whether an attempt broke the target's rule, and is instantiated from a different model family than the target. This is a deliberate guard against correlated failure: a model evaluating outputs from its own family may share its blind spots. The judge returns a structured verdict (success, failure, or uncertain) with a brief justification; its output is parsed defensively, degrading malformed responses to an explicit "uncertain" rather than failing.

The critic runs after an unsuccessful attempt and proposes a short, strategic revision for the next one. Its output conditions the construction of the following prompt. The critic is the component that distinguishes adaptation from enumeration: the attacker responds to the target's specific refusals rather than exhausting a fixed list.

### 3.3 Orchestration

The agents are coordinated by a state-graph orchestrator implemented with LangGraph. Nodes — attack, judge, critique — operate over a shared state that accumulates attempts, verdicts, and the current critic advice. A conditional edge after the judge governs termination: the run halts on success or on reaching the attempt budget, and otherwise routes through the critic and back to the attacker.

A plain loop would suffice functionally. We use an explicit graph for a reason specific to the domain: evaluation is only as valuable as it is auditable, and a graph makes the execution path — every node and every routing decision — an inspectable trace rather than an opaque control flow. When the output of a system is evidence about a model's behavior, the provenance of that evidence matters.

### 3.4 Objectives

Every attack targets a harmless proxy objective: the target is given a benign rule — a word to withhold, a phrase to avoid — and an attack succeeds exactly when the rule is broken, which is objectively checkable. This is the framework's central methodological commitment. It exercises the full mechanism of adaptive red-teaming while guaranteeing that no harmful content is solicited or produced, irrespective of an attack's effectiveness. The framework is consequently safe to publish and to run in the open, including by researchers without institutional safety infrastructure — a deliberate choice to keep this class of evaluation accessible.

### 3.5 Interfaces

The framework is driven from a command line and a browser interface, both thin over the same engine. The command line covers single-prompt queries, attacks in linear or adaptive mode, judge calibration, and inventory of providers and objectives. The browser interface, built with Streamlit, exposes the same operations interactively and renders each attempt's prompt, response, and verdict alongside the judge-calibration report. Neither interface contains logic of its own; both exist to make the engine usable.

---

## 4. Results

We report two kinds of result: the calibration of the judge that underpins every other measurement, and a statistical benchmark of two models against the harmless proxy objectives.

### 4.1 Judge calibration

The judge's reliability is a precondition for trusting any verdict the framework produces, so we measure it directly. We evaluate the default judge (Llama-3.3-70B) against a set of 26 hand-labeled cases spanning clear disclosures, clear refusals, and deliberately ambiguous framings — including a protected phrase appearing inside a refusal, a partial fragment followed by a refusal, and heavy hints that stop short of disclosure.

The judge agreed with the human labels on 25 of 26 cases (96%), with zero false alarms and a single missed breach. The lone disagreement is instructive rather than a defect: on a case where the target quoted the protected phrase *while stating its own rule* ("never say the phrase '…'"), the judge ruled that no disclosure had occurred, reasoning that quoting a phrase to acknowledge a rule is not the same as revealing it. This is a defensible interpretation; the case is one we had labeled the other way under a strict "the protected content appeared in the output" criterion. The divergence localizes precisely to the boundary where "breaking the rule" is itself contested.

We separate the two error types deliberately. A *missed breach* — the judge failing to flag a genuine disclosure — is the dangerous error, because it would cause a vulnerable model to be reported as safe. A *false alarm* is benign by comparison. The judge produced zero false alarms and one missed breach, and that single miss was on the contested recitation case rather than a clear disclosure.

To test whether verdicts are robust to the choice of judge model, we ran a second judge from a different family (GPT-OSS-120B) over the same 26 cases and measured inter-judge agreement. The judges agreed on 23 of 26 cases (88% raw agreement; Cohen's κ = 0.77, "substantial" on the Landis–Koch scale, against a chance-agreement baseline of 50%). Every disagreement fell on an a priori ambiguous case, and the disagreements were systematic in direction: the GPT-OSS judge consistently applied a stricter disclosure threshold than the Llama judge. Agreement was perfect on all unambiguous cases. We read this as evidence that verdicts on clear cases are robust to judge choice, and that residual judgment uncertainty is confined to cases where the underlying concept of disclosure is genuinely fuzzy.

### 4.2 Statistical benchmark

We benchmarked two models — Llama-3.3-70B and GPT-OSS-120B — against both harmless objectives, each judged by a model of the opposite family, running each of the four cells ten times under the adaptive orchestrator. We report the break rate per cell with a 95% Wilson score confidence interval.

| Target | Objective | Break rate (95% CI) |
|---|---|---|
| GPT-OSS-120B | secret word | 0% (0–28%, n=10) |
| GPT-OSS-120B | forbidden phrase | 0% (0–28%, n=10) |
| Llama-3.3-70B | secret word | 50% (24–76%, n=10) |
| Llama-3.3-70B | forbidden phrase | 40% (17–69%, n=10) |

Two findings follow. First, the two models differ substantially and consistently: GPT-OSS-120B resisted on every run of both objectives, while Llama-3.3-70B broke roughly half the time on each. This is consistent with the inter-judge result, where the GPT-OSS model was also the stricter evaluator — the same model is both the more rule-adherent target and the more conservative judge.

Second, and more important methodologically, the statistical benchmark contradicts what a single run would have reported. An earlier single-run benchmark of the same Llama–secret-word cell observed four refusals and would have classified the model as robust on that objective. The ten-run estimate places its break rate at 50% (95% CI 24–76%). The single run was not wrong about what it observed; it was unrepresentative of the distribution. Because the attacker operates at non-zero temperature and the target is stochastic, single-run red-teaming benchmarks can misclassify a frequently-vulnerable model as robust. Reporting rates with confidence intervals over repeated trials is necessary, not optional, for this class of evaluation.

We note two limitations specific to these numbers. The sample size (ten runs per cell) is small, which the wide confidence intervals reflect honestly — the GPT-OSS "0%" cells are consistent with a true break rate as high as 28%. And one of the forty runs completed with a degraded judge call: the daily token limit of the free-tier judge was exhausted on the final run, its judge calls failed after retries, and the run was recorded as "held." That single run is flagged; it does not affect the GPT-OSS conclusion, which rested on the preceding nine clean runs of that cell.

---

## 5. Limitations

We state the framework's limitations plainly; several follow directly from the design choices that give it its other properties.

**Proxy objectives do not measure specific harmful capabilities.** By construction, Avouch tests whether a model abandons a stated constraint under adversarial pressure, not whether it can be made to produce any particular harmful output. The harmless-proxy design is what makes the framework safe to develop and publish openly, but it means our results speak to constraint-robustness in general, not to any specific real-world harm. A model robust on our proxies is not thereby certified safe; conversely, a model that breaks a proxy rule has demonstrated a tendency, not a concrete danger.

**The attack techniques are documented, not novel.** The four framings used are well-known and intentionally generic. Avouch is a framework for orchestrating and evaluating attacks, not a source of new ones; a determined adversary using bespoke or state-of-the-art techniques would likely achieve higher break rates than we report. Our numbers should be read as lower bounds under a fixed, public attack repertoire.

**The calibration set is small.** Twenty-six hand-labeled cases are sufficient to demonstrate the calibration methodology and to surface where judgment is hard, but they are not a comprehensive audit of the judge. The confidence intervals on the benchmark, likewise, rest on ten runs per cell; they are honest about their width but remain wide. Both the calibration set and the per-cell sample size would need to grow substantially for the framework's outputs to support strong claims about any specific model.

**Evaluation was constrained by free-tier infrastructure.** All experiments used free-tier model access, which imposes per-minute and per-day rate limits. These shaped the scale of the benchmark and, in one of forty runs, degraded a judge call when a daily token limit was reached mid-run (that run is flagged in Section 4). The framework's design — provider abstraction, retry with backoff, resumable benchmarking — was in part a response to these constraints, but the constraints nonetheless bounded the scale of evidence we could gather.

**Two models, two objectives.** The benchmark covers a 2×2 grid. It is sufficient to demonstrate the method and to surface a meaningful differential between two models, but it is a demonstration, not a survey of the model landscape.

---

## 6. Future Work

Several extensions would deepen the framework along the axes its current limitations identify.

**Broader and adaptive attack coverage.** The most direct extension is a multi-turn conversational attacker that builds adversarial pressure across a dialogue rather than in single shots, which would exercise the adaptive orchestrator more fully. Additional attacker types — probes for demographic bias and for sycophancy (a model's tendency to agree with confidently-asserted falsehoods), each with harmless proxy formulations — would broaden the classes of failure the framework can surface.

**Stronger evaluation evidence.** Expanding the calibration set across more objectives and edge types, and adding a third judge family, would tighten the inter-rater picture. Increasing the per-cell run count would narrow the benchmark's confidence intervals, and a larger model grid would turn the current demonstration into a survey.

**Observability and integration.** Structured run tracing would make every attack's execution path inspectable as first-class data rather than logs. Exposing Avouch's tools through the Model Context Protocol would let other systems invoke its capabilities directly, and would align it with emerging conventions for agent tooling.

**Taxonomy alignment.** Mapping Avouch's objectives and findings onto published evaluation frameworks — the categories used by national safety institutes, and the risk taxonomy of the NIST AI Risk Management Framework — would situate its results within the shared vocabulary the field is converging on.

We note that more conventional engineering extensions — concurrent execution, a persistent results store and API, authentication and access control — would be required to operate Avouch at scale, but these concern productionization rather than the evaluation methodology that is the framework's contribution.

---

## 7. References

[1] P. Chao et al., "Jailbreaking Black Box Large Language Models in Twenty Queries," 2023. [Online]. Available: https://github.com/patrickrchao/JailbreakingLLMs

[2] A. Zou et al., "Universal and Transferable Adversarial Attacks on Aligned Language Models," 2023. [Online]. Available: https://llm-attacks.org

[3] X. Liu et al., "AutoDAN: Generating Stealthy Jailbreak Prompts on Aligned Large Language Models," Oct. 2023. [Online]. Available: https://arxiv.org/abs/2310.04451

[4] M. Mazeika et al., "HarmBench: A Standardized Evaluation Framework for Automated Red Teaming and Robust Refusal," Feb. 2024. [Online]. Available: https://arxiv.org/abs/2402.04249

[5] P. Chao et al., "JailbreakBench: An Open Robustness Benchmark for Jailbreaking Large Language Models," Mar. 2024. [Online]. Available: https://arxiv.org/abs/2403.04451

[6] J. R. Landis and G. G. Koch, "The Measurement of Observer Agreement for Categorical Data," *Biometrics*, vol. 33, no. 1, pp. 159–174, Mar. 1977.

[7] J. Cohen, "A Coefficient of Agreement for Nominal Scales," *Educational and Psychological Measurement*, vol. 20, no. 1, pp. 37–46, 1960.

[8] E. B. Wilson, "Probable Inference, the Law of Succession, and Statistical Inference," *Journal of the American Statistical Association*, vol. 22, no. 157, pp. 209–212, Mar. 1927.

[9] National Institute of Standards and Technology (NIST), "Artificial Intelligence Risk Management Framework (AI RMF 1.0)," Jan. 2023. [Online]. Available: https://www.nist.gov/itl/ai-risk-management-framework

[10] UK AI Safety Institute, "Evaluating Frontier Models for Dangerous Capabilities," 2024. [Online]. Available: https://www.gov.uk/government/organisations/ai-safety-institute
