"""Statistics for benchmark results.

Computes success rates and Wilson score confidence intervals for binomial
proportions. The Wilson interval is used rather than the normal approximation
because it remains accurate for small samples and for proportions near 0 or 1,
which is the regime our benchmarks operate in.
"""

import math
from dataclasses import dataclass

# z-score for a 95% confidence interval (two-sided).
Z_95 = 1.959963984540054


@dataclass
class ProportionEstimate:
    """A success rate with a Wilson score confidence interval.

    Attributes:
        successes: Number of runs that resulted in a break.
        trials: Total number of runs.
        rate: Point estimate of the success rate (successes / trials).
        ci_low: Lower bound of the 95% Wilson confidence interval.
        ci_high: Upper bound of the 95% Wilson confidence interval.
    """

    successes: int
    trials: int
    rate: float
    ci_low: float
    ci_high: float

    def as_pct(self) -> str:
        """Format the estimate as a percentage with its CI."""
        return (
            f"{self.rate * 100:.0f}% "
            f"(95% CI: {self.ci_low * 100:.0f}-{self.ci_high * 100:.0f}%, "
            f"n={self.trials})"
        )


def wilson_interval(successes: int, trials: int, z: float = Z_95) -> ProportionEstimate:
    """Compute the Wilson score confidence interval for a proportion.

    Args:
        successes: Number of successes observed.
        trials: Number of trials.
        z: z-score for the desired confidence level (default 95%).

    Returns:
        A ProportionEstimate with the point rate and CI bounds.
    """
    if trials == 0:
        return ProportionEstimate(0, 0, 0.0, 0.0, 0.0)

    p = successes / trials
    n = trials
    denom = 1 + (z**2) / n
    center = (p + (z**2) / (2 * n)) / denom
    margin = (z * math.sqrt((p * (1 - p) / n) + (z**2) / (4 * n**2))) / denom

    return ProportionEstimate(
        successes=successes,
        trials=trials,
        rate=p,
        ci_low=max(0.0, center - margin),
        ci_high=min(1.0, center + margin),
    )
