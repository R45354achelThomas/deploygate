"""Tests for deploygate.trend module."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from deploygate.history import HistoryEntry
from deploygate.trend import (
    TrendDirection,
    TrendResult,
    analyze_trend,
    format_trend_report,
)


def _entry(passed: bool, offset_seconds: int = 0) -> HistoryEntry:
    ts = datetime(2024, 1, 1, 12, 0, offset_seconds % 60, tzinfo=timezone.utc)
    return HistoryEntry(
        name="deploy",
        timestamp=ts.isoformat(),
        passed=passed,
        total=4,
        passed_count=4 if passed else 2,
        failed_count=0 if passed else 2,
    )


@pytest.fixture()
def all_passing() -> List[HistoryEntry]:
    return [_entry(True, i) for i in range(10)]


@pytest.fixture()
def all_failing() -> List[HistoryEntry]:
    return [_entry(False, i) for i in range(10)]


@pytest.fixture()
def improving() -> List[HistoryEntry]:
    # previous window: all fail, current window: all pass
    prev = [_entry(False, i) for i in range(5)]
    curr = [_entry(True, i + 5) for i in range(5)]
    return prev + curr


@pytest.fixture()
def declining() -> List[HistoryEntry]:
    prev = [_entry(True, i) for i in range(5)]
    curr = [_entry(False, i + 5) for i in range(5)]
    return prev + curr


def test_insufficient_data_single_entry():
    result = analyze_trend([_entry(True)])
    assert result.direction == TrendDirection.INSUFFICIENT_DATA


def test_insufficient_data_no_previous_window():
    entries = [_entry(True, i) for i in range(3)]
    result = analyze_trend(entries, window=5)
    assert result.direction == TrendDirection.INSUFFICIENT_DATA


def test_improving_trend(improving):
    result = analyze_trend(improving, window=5)
    assert result.direction == TrendDirection.IMPROVING
    assert result.delta == pytest.approx(1.0)


def test_declining_trend(declining):
    result = analyze_trend(declining, window=5)
    assert result.direction == TrendDirection.DECLINING
    assert result.delta == pytest.approx(-1.0)


def test_stable_trend(all_passing):
    result = analyze_trend(all_passing, window=5)
    assert result.direction == TrendDirection.STABLE
    assert result.delta == pytest.approx(0.0)


def test_pass_rates_populated(improving):
    result = analyze_trend(improving, window=5)
    assert result.pass_rate_current == pytest.approx(1.0)
    assert result.pass_rate_previous == pytest.approx(0.0)


def test_str_insufficient_data():
    result = TrendResult(
        direction=TrendDirection.INSUFFICIENT_DATA,
        pass_rate_current=None,
        pass_rate_previous=None,
        delta=None,
        window_size=5,
    )
    assert "Insufficient" in str(result)


def test_str_improving(improving):
    result = analyze_trend(improving, window=5)
    text = str(result)
    assert "↑" in text
    assert "Improving" in text


def test_format_trend_report(improving):
    result = analyze_trend(improving, window=5)
    report = format_trend_report("my-checklist", result)
    assert "my-checklist" in report
    assert "Trend report" in report
