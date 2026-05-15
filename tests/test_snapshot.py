"""Tests for deploygate.snapshot."""
from __future__ import annotations

import json
import os

import pytest

from deploygate.checklist import CheckResult, CheckStatus, Checklist
from deploygate.snapshot import (
    SnapshotDiff,
    diff_snapshot,
    load_snapshot,
    save_snapshot,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _pass(name: str) -> CheckResult:
    return CheckResult(name=name, status=CheckStatus.PASSED, message="ok")


def _fail(name: str) -> CheckResult:
    return CheckResult(name=name, status=CheckStatus.FAILED, message="nope")


@pytest.fixture()
def passing_checklist():
    cl = Checklist(name="deploy")
    cl.results = [_pass("lint"), _pass("tests")]
    return cl


@pytest.fixture()
def failing_checklist():
    cl = Checklist(name="deploy")
    cl.results = [_pass("lint"), _fail("tests")]
    return cl


# ---------------------------------------------------------------------------
# save / load round-trip
# ---------------------------------------------------------------------------


def test_save_creates_file(tmp_path, passing_checklist):
    dest = str(tmp_path / "snap.json")
    save_snapshot(passing_checklist, dest)
    assert os.path.exists(dest)


def test_save_load_roundtrip(tmp_path, passing_checklist):
    dest = str(tmp_path / "snap.json")
    save_snapshot(passing_checklist, dest)
    mapping = load_snapshot(dest)
    assert mapping["lint"] == CheckStatus.PASSED.value
    assert mapping["tests"] == CheckStatus.PASSED.value


def test_saved_file_is_valid_json(tmp_path, passing_checklist):
    dest = str(tmp_path / "snap.json")
    save_snapshot(passing_checklist, dest)
    data = json.loads(open(dest).read())
    assert isinstance(data, list)
    assert all("name" in item and "status" in item for item in data)


# ---------------------------------------------------------------------------
# diff_snapshot
# ---------------------------------------------------------------------------


def test_diff_no_previous_file(tmp_path, passing_checklist):
    dest = str(tmp_path / "missing.json")
    diffs = diff_snapshot(passing_checklist, dest)
    assert len(diffs) == 2
    assert all(d.previous is None for d in diffs)


def test_diff_unchanged(tmp_path, passing_checklist):
    dest = str(tmp_path / "snap.json")
    save_snapshot(passing_checklist, dest)
    diffs = diff_snapshot(passing_checklist, dest)
    assert all(not d.changed for d in diffs)


def test_diff_regression_detected(tmp_path, passing_checklist, failing_checklist):
    dest = str(tmp_path / "snap.json")
    save_snapshot(passing_checklist, dest)
    diffs = diff_snapshot(failing_checklist, dest)
    regressed = [d for d in diffs if d.regressed]
    assert len(regressed) == 1
    assert regressed[0].name == "tests"


def test_diff_recovery_detected(tmp_path, failing_checklist, passing_checklist):
    dest = str(tmp_path / "snap.json")
    save_snapshot(failing_checklist, dest)
    diffs = diff_snapshot(passing_checklist, dest)
    recovered = [d for d in diffs if d.recovered]
    assert len(recovered) == 1
    assert recovered[0].name == "tests"


def test_snapshot_diff_str_properties():
    d = SnapshotDiff(name="lint", previous="passed", current="failed")
    assert d.regressed
    assert not d.recovered
    assert d.changed
