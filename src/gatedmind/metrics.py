"""Rates with Wilson 95% intervals, the rule of three, and latency percentiles with a bootstrap."""

from __future__ import annotations

import math
import random

Z = 1.959964


def wilson(k: int, n: int) -> tuple[float, float, float]:
    """Point estimate and Wilson score 95% interval for k successes in n trials."""
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))


def rule_of_three(n: int) -> float:
    """Approximate 95% upper bound on a rate when 0 events were seen in n trials."""
    return 3 / n if n else 1.0


def percentile(xs: list[float], q: float) -> float:
    """Nearest-rank percentile, q in [0, 100]."""
    s = sorted(xs)
    if not s:
        return 0.0
    i = max(0, math.ceil(q / 100 * len(s)) - 1)
    return s[i]


def bootstrap_ci(xs: list[float], q: float, reps: int = 1000, seed: int = 0) -> tuple[float, float]:
    rng = random.Random(seed)  # noqa: S311 (bootstrap, not crypto)
    stats = sorted(percentile(rng.choices(xs, k=len(xs)), q) for _ in range(reps))
    return (stats[int(0.025 * reps)], stats[int(0.975 * reps) - 1])
