"""Trend analysis for checklist run history.

Provides utilities to detect whether a checklist's pass rate is improving,
degrading, or stable over a rolling window of recent runs.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from deploygate.history import HistoryEntry


class TrendDirection(str, Enum):
    IMPROVING = "improving"
    DEGRADING = "degrading"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class TrendResult:
    """Result of a trend analysis over a window of history entries."""

    direction: TrendDirection
    window_size: int
    recent_pass_rate: float  # pass rate in the *later* half of the window
    earlier_pass_rate: float  # pass rate in the *earlier* half of the window
    delta: float  # recent_pass_rate - earlier_pass_rate

    def __str__(self) -> str:
        if self.direction == TrendDirection.INSUFFICIENT_DATA:
            return "Insufficient data for trend analysis"
        symbol = {
            TrendDirection.IMPROVING: "↑",
            TrendDirection.DEGRADING: "↓",
            TrendDirection.STABLE: "→",
        }[self.direction]
        return (
            f"{symbol} {self.direction.value.capitalize()} "
            f"(earlier {self.earlier_pass_rate:.0%} → recent {self.recent_pass_rate:.0%})"
        )


def _pass_rate(entries: List[HistoryEntry]) -> float:
    """Return the fraction of entries that passed."""
    if not entries:
        return 0.0
    return sum(1 for e in entries if e.passed) / len(entries)


def analyze_trend(
    entries: List[HistoryEntry],
    window: int = 10,
    threshold: float = 0.1,
) -> TrendResult:
    """Analyse the trend direction for a list of history entries.

    Args:
        entries:   History entries ordered oldest-first.  Only the most recent
                   *window* entries are considered.
        window:    Number of recent runs to include in the analysis.  Must be
                   at least 4 so that each half contains at least 2 data points.
        threshold: Minimum absolute change in pass-rate between the two halves
                   to be classified as improving or degrading (default 10 %).

    Returns:
        A :class:`TrendResult` describing the direction and magnitude.
    """
    if window < 4:
        raise ValueError("window must be at least 4")

    recent_entries = entries[-window:]

    if len(recent_entries) < 4:
        return TrendResult(
            direction=TrendDirection.INSUFFICIENT_DATA,
            window_size=len(recent_entries),
            recent_pass_rate=0.0,
            earlier_pass_rate=0.0,
            delta=0.0,
        )

    mid = len(recent_entries) // 2
    earlier_half = recent_entries[:mid]
    later_half = recent_entries[mid:]

    earlier_rate = _pass_rate(earlier_half)
    recent_rate = _pass_rate(later_half)
    delta = recent_rate - earlier_rate

    if delta >= threshold:
        direction = TrendDirection.IMPROVING
    elif delta <= -threshold:
        direction = TrendDirection.DEGRADING
    else:
        direction = TrendDirection.STABLE

    return TrendResult(
        direction=direction,
        window_size=len(recent_entries),
        recent_pass_rate=recent_rate,
        earlier_pass_rate=earlier_rate,
        delta=delta,
    )


def filter_by_checklist(
    entries: List[HistoryEntry], name: str
) -> List[HistoryEntry]:
    """Return only entries whose checklist name matches *name*."""
    return [e for e in entries if e.name == name]


def trend_for_checklist(
    entries: List[HistoryEntry],
    name: str,
    window: int = 10,
    threshold: float = 0.1,
) -> Optional[TrendResult]:
    """Convenience wrapper: filter entries by checklist name then analyse.

    Returns ``None`` if no matching entries exist.
    """
    filtered = filter_by_checklist(entries, name)
    if not filtered:
        return None
    return analyze_trend(filtered, window=window, threshold=threshold)
