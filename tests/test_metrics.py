import pytest

from gatedmind import metrics


def test_wilson_zero_of_200():
    p, lo, hi = metrics.wilson(0, 200)
    assert p == 0 and lo == 0
    assert hi == pytest.approx(0.0188, abs=1e-3)


def test_wilson_half():
    p, lo, hi = metrics.wilson(50, 100)
    assert (lo, hi) == pytest.approx((0.404, 0.596), abs=1e-3)


def test_rule_of_three():
    assert metrics.rule_of_three(200) == pytest.approx(0.015)


def test_percentile_and_bootstrap():
    xs = list(range(1, 101))
    assert metrics.percentile(xs, 50) == 50
    assert metrics.percentile(xs, 95) == 95
    lo, hi = metrics.bootstrap_ci(xs, 50)
    assert lo <= 50 <= hi
