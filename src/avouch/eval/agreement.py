"""Inter-judge agreement metrics.

Runs two independent judges over the same set of golden cases and computes
their agreement, including Cohen's kappa, which corrects for the agreement
expected by chance. High inter-judge agreement indicates that verdicts are
robust rather than artifacts of a single model's idiosyncrasies.
"""

import logging
from dataclasses import dataclass, field

from avouch.adapters.base import TargetAdapter
from avouch.agents.judge_agent import JudgeAgent
from avouch.agents.types import Outcome
from avouch.eval.golden_cases import GOLDEN_CASES, GoldenCase, _attempt

logger = logging.getLogger(__name__)


@dataclass
class AgreementResult:
    """Per-case comparison of two judges' rulings."""

    case_id: str
    judge_a: Outcome
    judge_b: Outcome
    agreed: bool


@dataclass
class AgreementReport:
    """Aggregated inter-judge agreement, including Cohen's kappa.

    Attributes:
        results: Per-case agreement records.
        judge_a_name: Identifier of the first judge.
        judge_b_name: Identifier of the second judge.
        observed_agreement: Fraction of cases the judges agreed on.
        expected_agreement: Chance-expected agreement given each judge's
            marginal label frequencies.
        kappa: Cohen's kappa (chance-corrected agreement).
    """

    results: list[AgreementResult] = field(default_factory=list)
    judge_a_name: str = ""
    judge_b_name: str = ""
    observed_agreement: float = 0.0
    expected_agreement: float = 0.0
    kappa: float = 0.0

    @property
    def interpretation(self) -> str:
        """Landis & Koch qualitative label for the kappa value."""
        k = self.kappa
        if k < 0:
            return "poor (worse than chance)"
        if k <= 0.20:
            return "slight"
        if k <= 0.40:
            return "fair"
        if k <= 0.60:
            return "moderate"
        if k <= 0.80:
            return "substantial"
        return "almost perfect"


def _normalize(outcome: Outcome) -> Outcome:
    """Collapse UNCERTAIN into FAILURE for a binary agreement comparison.

    Agreement is computed on the broke/held distinction; an UNCERTAIN ruling is
    treated as 'did not confirm a break' (i.e. FAILURE) for this purpose.
    """
    return Outcome.SUCCESS if outcome is Outcome.SUCCESS else Outcome.FAILURE


def compute_agreement(
    judge_a: TargetAdapter,
    judge_b: TargetAdapter,
    cases: list[GoldenCase] | None = None,
) -> AgreementReport:
    """Run two judges over the cases and compute Cohen's kappa.

    Args:
        judge_a: First judge adapter.
        judge_b: Second judge adapter (ideally a different model family).
        cases: Golden cases to use; defaults to the full set.

    Returns:
        An AgreementReport with per-case results and kappa.
    """
    if cases is None:
        cases = GOLDEN_CASES

    agent_a = JudgeAgent(judge_a)
    agent_b = JudgeAgent(judge_b)

    report = AgreementReport(judge_a_name=judge_a.name, judge_b_name=judge_b.name)

    # Counts for kappa: how often each judge says SUCCESS, and agreements.
    n = 0
    agreements = 0
    a_success = 0
    b_success = 0

    for case in cases:
        attempt = _attempt(case.target_response)
        out_a = _normalize(agent_a.evaluate(case.objective, attempt).outcome)
        out_b = _normalize(agent_b.evaluate(case.objective, attempt).outcome)

        agreed = out_a is out_b
        report.results.append(
            AgreementResult(
                case_id=case.case_id, judge_a=out_a, judge_b=out_b, agreed=agreed
            )
        )

        n += 1
        if agreed:
            agreements += 1
        if out_a is Outcome.SUCCESS:
            a_success += 1
        if out_b is Outcome.SUCCESS:
            b_success += 1

        logger.info(
            "Case '%s': A=%s B=%s %s",
            case.case_id,
            out_a.value,
            out_b.value,
            "agree" if agreed else "DISAGREE",
        )

    # Observed agreement.
    p_o = agreements / n if n else 0.0

    # Expected (chance) agreement: probability both say SUCCESS plus both say FAILURE,
    # under independence given each judge's marginal success rate.
    pa_s = a_success / n if n else 0.0
    pb_s = b_success / n if n else 0.0
    p_e = (pa_s * pb_s) + ((1 - pa_s) * (1 - pb_s))

    kappa = (p_o - p_e) / (1 - p_e) if (1 - p_e) != 0 else 1.0

    report.observed_agreement = p_o
    report.expected_agreement = p_e
    report.kappa = kappa

    logger.info("Agreement: observed=%.2f expected=%.2f kappa=%.2f", p_o, p_e, kappa)
    return report
