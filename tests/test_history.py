"""Tests for deploygate.history."""

from __future__ import annotations

import json
import pytest

from deploygate.checklist import CheckResult, CheckStatus, Checklist
from deploygate.history import (
    _checklist_to_entry,
    last_run,
    load_history,
    record,
    save_history,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def passing_checklist():
    cl = Checklist(name="smoke")
    cl.results = [
        CheckResult(name="ping", status=CheckStatus.PASSED, message="ok"),
        CheckResult(name="db", status=CheckStatus.PASSED, message="ok"),
    ]
    return cl


@pytest.fixture()
def failing_checklist():
    cl = Checklist(name="release")
    cl.results = [
        CheckResult(name="lint", status=CheckStatus.PASSED, message="ok"),
        CheckResult(name="tests", status=CheckStatus.FAILED, message="3 failures"),
        CheckResult(name="build", status=CheckStatus.ERROR, message="timeout"),
    ]
    return cl


# ---------------------------------------------------------------------------
# _checklist_to_entry
# ---------------------------------------------------------------------------


def test_entry_name(passing_checklist):
    entry = _checklist_to_entry(passing_checklist)
    assert entry["name"] == "smoke"


def test_entry_passed_flag(passing_checklist, failing_checklist):
    assert _checklist_to_entry(passing_checklist)["passed"] is True
    assert _checklist_to_entry(failing_checklist)["passed"] is False


def test_entry_counts(failing_checklist):
    entry = _checklist_to_entry(failing_checklist)
    assert entry["total"] == 3
    assert entry["failed"] == 1
    assert entry["errored"] == 1


def test_entry_has_timestamp(passing_checklist):
    entry = _checklist_to_entry(passing_checklist)
    assert "timestamp" in entry and entry["timestamp"]


def test_entry_checks_serialised(failing_checklist):
    entry = _checklist_to_entry(failing_checklist)
    names = [c["name"] for c in entry["checks"]]
    assert names == ["lint", "tests", "build"]


# ---------------------------------------------------------------------------
# load / save / record
# ---------------------------------------------------------------------------


def test_load_history_missing_file(tmp_path):
    result = load_history(str(tmp_path / "nope.json"))
    assert result == []


def test_save_and_load_roundtrip(tmp_path):
    path = str(tmp_path / "hist.json")
    entries = [{"name": "x", "passed": True}]
    save_history(entries, path)
    loaded = load_history(path)
    assert loaded == entries


def test_record_appends_entry(tmp_path, passing_checklist):
    path = str(tmp_path / "hist.json")
    record(passing_checklist, path)
    record(passing_checklist, path)
    entries = load_history(path)
    assert len(entries) == 2


def test_last_run_returns_none_when_empty(tmp_path):
    assert last_run(str(tmp_path / "empty.json")) is None


def test_last_run_returns_latest(tmp_path, passing_checklist, failing_checklist):
    path = str(tmp_path / "hist.json")
    record(passing_checklist, path)
    record(failing_checklist, path)
    latest = last_run(path)
    assert latest["name"] == "release"


def test_load_history_invalid_format(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"oops": True}))
    with pytest.raises(ValueError, match="JSON array"):
        load_history(str(path))
