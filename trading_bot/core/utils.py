from __future__ import annotations


def pct(value: float) -> float:
    """Interpret percentage-like numbers as ratios.

    If ``value`` is greater than 1.0, treat it as a percent (e.g., 1.5 -> 0.015).
    Otherwise, assume it is already a ratio.
    """
    return value / 100.0 if value > 1.0 else value
