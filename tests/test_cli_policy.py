"""Tests for deploygate.cli_policy."""
import json
import sys

import pytest

from deploygate.cli_policy import _parse_args


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def test_parse_args_checklist_positional():
    args = _parse_args(["my_checklist.py"])
    assert args.checklist == "my_checklist.py"


def test_parse_args_default_rule_name():
    args = _parse_args(["cl.py"])
    assert args.rule_name == "default"


def test_parse_args_custom_rule_name():
    args = _parse_args(["cl.py", "--rule-name", "production"])
    assert args.rule_name == "production"


def test_parse_args_default_min_pass_rate():
    args = _parse_args(["cl.py"])
    assert args.min_pass_rate == pytest.approx(1.0)


def test_parse_args_custom_min_pass_rate():
    args = _parse_args(["cl.py", "--min-pass-rate", "0.8"])
    assert args.min_pass_rate == pytest.approx(0.8)


def test_parse_args_required_checks():
    args = _parse_args(["cl.py", "--required-checks", "db", "cache"])
    assert args.required_checks == ["db", "cache"]


def test_parse_args_no_block_on_error_default_false():
    args = _parse_args(["cl.py"])
    assert args.no_block_on_error is False


def test_parse_args_no_block_on_error_flag():
    args = _parse_args(["cl.py", "--no-block-on-error"])
    assert args.no_block_on_error is True


def test_parse_args_json_flag():
    args = _parse_args(["cl.py", "--json"])
    assert args.json is True


def test_parse_args_json_default_false():
    args = _parse_args(["cl.py"])
    assert args.json is False
