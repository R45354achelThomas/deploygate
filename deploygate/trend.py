"""Trend analysis for checklist pass rates over time."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from deploygate.history import HistoryEntry


class TrendDirection(Enum):
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class TrendResult:
    direction: TrendDirection
    pass_rate_current: Optional[float]
    pass_rate_previous: Optional[float]
    delta: Optional[float]
    window_size: int

    def __str__(self) -> str:
        if self.direction == TrendDirection.INSUFFICIENT_DATA:
            return "Insufficient data for trend analysis."
        arrow = {
            TrendDirection.IMPROVING: "↑",
            TrendDirection.DECLINING: "↓",
            TrendDirection.STABLE: "→",
        }[self.direction]
        return (
            f"{arrow} {self.direction.value.capitalize()} "
            f"(current: {self.pass_rate_current:.0%}, "
            f"previous: {self.pass_rate_previous:.0%}, "
            f"delta: {self.delta:+.0%})"
        )


def _pass_rate(entries: List[HistoryEntry]) -> Optional[float]:
    if not entries:
        return None
    return sum(1 for e in entries if e.passed) / len(entries)


def analyze_trend(
    entries: List[HistoryEntry],
    window: int = 5,
    stable_threshold: float = 0.05,
) -> TrendResult:
    """Compare pass rate of the most recent *window* runs vs the previous window."""
    if len(entries) < 2:
        return TrendResult(
            direction=TrendDirection.INSUFFICIENT_DATA,
            pass_rate_current=None,
            pass_rate_previous=None,
            delta=None,
            window_size=window,
        )

    sorted_entries = sorted(entries, key=lambda e: e.timestamp)
    current_window = sorted_entries[-window:]
    previous_window = sorted_entries[-2 * window: -window]

    if not previous_window:
        return TrendResult(
            direction=TrendDirection.INSUFFICIENT_DATA,
            pass_rate_current=_pass_rate(current_window),
            pass_rate_previous=None,
            delta=None,
            window_size=window,
        )

    current_rate = _pass_rate(current_window)
    previous_rate = _pass_rate(previous_window)
    delta = current_rate - previous_rate  # type: ignore[operator]

    if abs(delta) <= stable_threshold:
        direction = TrendDirection.STABLE
    elif delta > 0:
        direction = TrendDirection.IMPROVING
    else:
        direction = TrendDirection.DECLINING

    return TrendResult(
        direction=direction,
        pass_rate_current=current_rate,
        pass_rate_previous=previous_rate,
        delta=delta,
        window_size=window,
    )


def format_trend_report(name: str, result: TrendResult) -> str:
    """Return a human-readable trend report string."""
    lines = [f"Trend report for '{name}':", f"  {result}"]
    return "\n".join(lines)
