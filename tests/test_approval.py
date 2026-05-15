"""Tests for deploygate.approval."""
import json
from pathlib import Path

import pytest

from deploygate.approval import (
    ApprovalEntry,
    approve,
    is_approved,
    latest_approval,
    load_approvals,
    save_approvals,
)


@pytest.fixture()
def tmp_file(tmp_path: Path) -> Path:
    return tmp_path / "approvals.json"


# ---------------------------------------------------------------------------
# ApprovalEntry
# ---------------------------------------------------------------------------

def test_entry_round_trip():
    e = ApprovalEntry(checklist="deploy", approved_by="alice", approved_at="2024-01-01T00:00:00+00:00", note="lgtm")
    assert ApprovalEntry.from_dict(e.to_dict()) == e


def test_entry_note_defaults_to_empty():
    e = ApprovalEntry.from_dict({"checklist": "x", "approved_by": "bob", "approved_at": "t"})
    assert e.note == ""


# ---------------------------------------------------------------------------
# load / save
# ---------------------------------------------------------------------------

def test_load_returns_empty_when_file_missing(tmp_file):
    assert load_approvals(tmp_file) == []


def test_save_creates_file(tmp_file):
    save_approvals(tmp_file, [])
    assert tmp_file.exists()


def test_save_and_load_round_trip(tmp_file):
    e = ApprovalEntry(checklist="prod", approved_by="carol", approved_at="2024-06-01T12:00:00+00:00")
    save_approvals(tmp_file, [e])
    loaded = load_approvals(tmp_file)
    assert len(loaded) == 1
    assert loaded[0].approved_by == "carol"


def test_save_creates_parent_dirs(tmp_path):
    deep = tmp_path / "a" / "b" / "approvals.json"
    save_approvals(deep, [])
    assert deep.exists()


# ---------------------------------------------------------------------------
# approve
# ---------------------------------------------------------------------------

def test_approve_returns_entry(tmp_file):
    entry = approve(tmp_file, checklist="staging", approved_by="dave")
    assert entry.checklist == "staging"
    assert entry.approved_by == "dave"


def test_approve_persists(tmp_file):
    approve(tmp_file, checklist="staging", approved_by="eve")
    assert is_approved(tmp_file, "staging")


def test_approve_appends(tmp_file):
    approve(tmp_file, checklist="staging", approved_by="frank")
    approve(tmp_file, checklist="staging", approved_by="grace")
    assert len(load_approvals(tmp_file)) == 2


def test_approve_records_note(tmp_file):
    entry = approve(tmp_file, checklist="prod", approved_by="henry", note="all green")
    assert entry.note == "all green"


# ---------------------------------------------------------------------------
# is_approved / latest_approval
# ---------------------------------------------------------------------------

def test_is_approved_false_when_no_entries(tmp_file):
    assert not is_approved(tmp_file, "prod")


def test_is_approved_false_for_different_checklist(tmp_file):
    approve(tmp_file, checklist="staging", approved_by="ida")
    assert not is_approved(tmp_file, "prod")


def test_latest_approval_returns_none_when_absent(tmp_file):
    assert latest_approval(tmp_file, "prod") is None


def test_latest_approval_returns_last(tmp_file):
    approve(tmp_file, checklist="prod", approved_by="jack")
    approve(tmp_file, checklist="prod", approved_by="kate")
    result = latest_approval(tmp_file, "prod")
    assert result is not None
    assert result.approved_by == "kate"
