"""Tests for deploygate.cli_approval."""
import json
from pathlib import Path

import pytest

from deploygate.cli_approval import _parse_args, main


# ---------------------------------------------------------------------------
# _parse_args
# ---------------------------------------------------------------------------

def test_parse_approve_defaults():
    ns = _parse_args(["approve", "prod", "--by", "alice"])
    assert ns.command == "approve"
    assert ns.checklist == "prod"
    assert ns.approved_by == "alice"
    assert ns.note == ""


def test_parse_approve_with_note():
    ns = _parse_args(["approve", "staging", "--by", "bob", "--note", "lgtm"])
    assert ns.note == "lgtm"


def test_parse_status():
    ns = _parse_args(["status", "prod"])
    assert ns.command == "status"
    assert ns.checklist == "prod"


def test_parse_list():
    ns = _parse_args(["list"])
    assert ns.command == "list"


def test_parse_custom_file():
    ns = _parse_args(["--file", "/tmp/a.json", "list"])
    assert ns.file == "/tmp/a.json"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

@pytest.fixture()
def store(tmp_path) -> Path:
    return tmp_path / "approvals.json"


def test_main_approve_creates_file(store, capsys):
    rc = main(["--file", str(store), "approve", "prod", "--by", "carol"])
    assert rc == 0
    assert store.exists()


def test_main_approve_output(store, capsys):
    main(["--file", str(store), "approve", "staging", "--by", "dave"])
    out = capsys.readouterr().out
    assert "staging" in out
    assert "dave" in out


def test_main_status_approved(store, capsys):
    main(["--file", str(store), "approve", "prod", "--by", "eve"])
    rc = main(["--file", str(store), "status", "prod"])
    assert rc == 0


def test_main_status_not_approved_returns_1(store):
    rc = main(["--file", str(store), "status", "prod"])
    assert rc == 1


def test_main_list_empty(store, capsys):
    rc = main(["--file", str(store), "list"])
    assert rc == 0
    assert "No approvals" in capsys.readouterr().out


def test_main_list_shows_entries(store, capsys):
    main(["--file", str(store), "approve", "prod", "--by", "frank", "--note", "ok"])
    main(["--file", str(store), "list"])
    out = capsys.readouterr().out
    assert "prod" in out
    assert "frank" in out
    assert "ok" in out
