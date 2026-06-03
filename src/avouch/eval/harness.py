"""The judge evaluation harness.

Runs the Judge Agent against the golden test cases and computes calibration
metrics: how often the judge's ruling matches the known-correct outcome, with
a breakdown of agreement and the specific cases where the judge diverged.
"""

import logging
from dataclasses import dataclass, field

from avouch.adapters.base import TargetAdapter
from avouch.agents.judge_agent import JudgeAgent
from avouch.agents.types import Outcome
from avouch.eval.golden_cases import GOLDEN_CASES, GoldenCase, _attempt

logger = logging.getLogger(__name__)


@dataclass
class CaseResult:
    """The judge's ruling on one golden case, with the expected answer.

    Attributes:
        case_id: Identifier of the golden case.
        expected: The known-correct outcome.
        actual: The outcome the judge produced.
        agreed: True if actual matches expected.
        reasoning: The judge's stated reasoning.
    """

    case_id: str
    expected: Outcome
    actual: Outcome
    agreed: bool
    reasoning: str


@dataclass
class EvalReport:
    """Aggregated results of running the judge against the golden set.

    Attributes:
        results: Per-case results.
        total: Total number of cases evaluated.
        agreements: Number of cases where the judge matched the expected label.
        missed_breaches: Cases where expected SUCCESS but judge said otherwise
            (the judge failed to catch a real rule break -- the dangerous error).
        false_alarms: Cases where expected FAILURE but judge said SUCCESS
            (the judge flagged a safe response as a breach).
    """

    results: list[CaseResult] = field(default_factory=list)
    total: int = 0
    agreements: int = 0
    missed_breaches: int = 0
    false_alarms: int = 0

    @property
    def accuracy(self) -> float:
        """Fraction of cases where the judge matched the expected label."""
        return self.agreements / self.total if self.total else 0.0


def evaluate_judge(
    judge: TargetAdapter,
    cases: list[GoldenCase] | None = None,
) -> EvalReport:
    """Run the judge against the golden cases and compute a calibration report.

    Args:
        judge: The adapter for the judge model to evaluate.
        cases: The golden cases to use; defaults to the full GOLDEN_CASES set.

    Returns:
        An EvalReport with per-case results and aggregate metrics.
    """
    if cases is None:
        cases = GOLDEN_CASES

    judge_agent = JudgeAgent(judge)
    report = EvalReport()

    for case in cases:
        attempt = _attempt(case.target_response)
        verdict = judge_agent.evaluate(case.objective, attempt)
        actual = verdict.outcome
        agreed = actual is case.expected

        logger.info(
            "Case '%s': expected=%s actual=%s %s",
            case.case_id,
            case.expected.value,
            actual.value,
            "OK" if agreed else "MISMATCH",
        )

        report.results.append(
            CaseResult(
                case_id=case.case_id,
                expected=case.expected,
                actual=actual,
                agreed=agreed,
                reasoning=verdict.reasoning,
            )
        )

        report.total += 1
        if agreed:
            report.agreements += 1
        else:
            if case.expected is Outcome.SUCCESS and actual is not Outcome.SUCCESS:
                report.missed_breaches += 1
            elif case.expected is Outcome.FAILURE and actual is Outcome.SUCCESS:
                report.false_alarms += 1

    logger.info(
        "Eval complete: accuracy=%.0f%% (%d/%d)",
        report.accuracy * 100,
        report.agreements,
        report.total,
    )
    return report
