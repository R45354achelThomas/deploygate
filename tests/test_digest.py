"""Tests for deploygate.digest module."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone

import pytest

from deploygate.digest import _period_bounds, build_digest


NOW = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)


def _write_history(path: str, entries: list) -> None:
    with open(path, "w") as f:
        json.dump(entries, f)


def _make_entry(name: str, passed: bool, ts: datetime) -> dict:
    return {
        "name": name,
        "timestamp": ts.isoformat(),
        "passed": passed,
        "total": 3,
        "passed_count": 3 if passed else 1,
        "failed_count": 0 if passed else 2,
    }


# --- _period_bounds ---

def test_period_bounds_daily():
    since, until = _period_bounds("daily", NOW)
    assert until == NOW
    assert (until - since).days == 1


def test_period_bounds_weekly():
    since, until = _period_bounds("weekly", NOW)
    assert (until - since).days == 7


def test_period_bounds_monthly():
    since, until = _period_bounds("monthly", NOW)
    assert (until - since).days == 30


def test_period_bounds_invalid():
    with pytest.raises(ValueError, match="Unknown period"):
        _period_bounds("yearly", NOW)


# --- build_digest ---

@pytest.fixture()
def tmp_history(tmp_path):
    path = str(tmp_path / "history.json")
    entries = [
        _make_entry("deploy", True, datetime(2024, 6, 14, 10, 0, tzinfo=timezone.utc)),
        _make_entry("deploy", False, datetime(2024, 6, 13, 8, 0, tzinfo=timezone.utc)),
        # Outside weekly window
        _make_entry("deploy", True, datetime(2024, 6, 1, 0, 0, tzinfo=timezone.utc)),
    ]
    _write_history(path, entries)
    return path


def test_digest_period_label(tmp_history):
    report = build_digest(tmp_history, period="weekly", now=NOW)
    assert report.period_label == "weekly"


def test_digest_body_contains_header(tmp_history):
    report = build_digest(tmp_history, period="weekly", now=NOW)
    assert "DeployGate Digest" in report.body
    assert "Weekly" in report.body


def test_digest_body_contains_period_dates(tmp_history):
    report = build_digest(tmp_history, period="weekly", now=NOW)
    assert "2024-06-08" in report.body  # since date
    assert "2024-06-15" in report.body  # until date


def test_digest_no_entries_message(tmp_path):
    path = str(tmp_path / "empty.json")
    _write_history(path, [])
    report = build_digest(path, period="daily", now=NOW)
    assert "No runs recorded" in report.body


def test_digest_checklist_filter(tmp_history):
    report = build_digest(tmp_history, period="weekly", checklist="other", now=NOW)
    assert "No runs recorded" in report.body


def test_digest_str_returns_body(tmp_history):
    report = build_digest(tmp_history, period="weekly", now=NOW)
    assert str(report) == report.body
