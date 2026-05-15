"""Tests for deploygate.cli_metrics."""
import json
import os
import tempfile

import pytest

from deploygate.cli_metrics import _parse_args, main


def _write_history(entries, tmp_path):
    path = os.path.join(tmp_path, "history.json")
    with open(path, "w") as fh:
        json.dump(entries, fh)
    return path


def _make_entry(name="deploy", passed=True, passed_count=3, failed_count=0):
    return {
        "name": name,
        "passed": passed,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "timestamp": "2024-06-01T12:00:00Z",
    }


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


def test_parse_args_history_file():
    args = _parse_args(["history.json"])
    assert args.history_file == "history.json"


def test_parse_args_checklist_filter():
    args = _parse_args(["history.json", "--checklist", "prod"])
    assert args.checklist == "prod"


def test_parse_args_checklist_default_none():
    args = _parse_args(["history.json"])
    assert args.checklist is None


def test_main_missing_file_returns_1(tmp_dir, capsys):
    result = main([os.path.join(tmp_dir, "nonexistent.json")])
    assert result == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_main_empty_history_returns_1(tmp_dir, capsys):
    path = _write_history([], tmp_dir)
    result = main([path])
    assert result == 1


def test_main_prints_metrics(tmp_dir, capsys):
    entries = [_make_entry(), _make_entry(passed=False, passed_count=1, failed_count=2)]
    path = _write_history(entries, tmp_dir)
    result = main([path])
    assert result == 0
    captured = capsys.readouterr()
    assert "deploy" in captured.out
    assert "%" in captured.out


def test_main_filter_by_checklist(tmp_dir, capsys):
    entries = [
        _make_entry(name="deploy"),
        _make_entry(name="smoke", passed=False, passed_count=0, failed_count=3),
    ]
    path = _write_history(entries, tmp_dir)
    result = main([path, "--checklist", "smoke"])
    assert result == 0
    captured = capsys.readouterr()
    assert "smoke" in captured.out


def test_main_filter_unknown_checklist_returns_1(tmp_dir, capsys):
    entries = [_make_entry(name="deploy")]
    path = _write_history(entries, tmp_dir)
    result = main([path, "--checklist", "ghost"])
    assert result == 1
    captured = capsys.readouterr()
    assert "ghost" in captured.err
