"""Tests for deploygate.cli_webhook."""
from __future__ import annotations

import pytest

from deploygate.cli_webhook import _parse_args


def test_parse_args_checklist_and_url():
    args = _parse_args(["checks.py", "https://hooks.example.com/deploy"])
    assert args.checklist == "checks.py"
    assert args.url == "https://hooks.example.com/deploy"


def test_parse_args_default_method():
    args = _parse_args(["checks.py", "https://hooks.example.com/deploy"])
    assert args.method == "POST"


def test_parse_args_custom_method():
    args = _parse_args(["checks.py", "https://hooks.example.com/deploy", "--method", "PUT"])
    assert args.method == "PUT"


def test_parse_args_default_timeout():
    args = _parse_args(["checks.py", "https://hooks.example.com/deploy"])
    assert args.timeout == 10


def test_parse_args_custom_timeout():
    args = _parse_args(["checks.py", "https://hooks.example.com/deploy", "--timeout", "30"])
    assert args.timeout == 30


def test_parse_args_include_results_by_default():
    args = _parse_args(["checks.py", "https://hooks.example.com/deploy"])
    assert args.no_results is False


def test_parse_args_no_results_flag():
    args = _parse_args(["checks.py", "https://hooks.example.com/deploy", "--no-results"])
    assert args.no_results is True


def test_parse_args_invalid_method_raises(capsys):
    with pytest.raises(SystemExit):
        _parse_args(["checks.py", "https://hooks.example.com/deploy", "--method", "DELETE"])


def test_parse_args_missing_url_raises(capsys):
    with pytest.raises(SystemExit):
        _parse_args(["checks.py"])
