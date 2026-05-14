"""Tests for deploygate.slack notification module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from deploygate.checklist import CheckItem, CheckResult, CheckStatus, Checklist
from deploygate.slack import _build_payload, notify


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def passing_checklist():
    items = [CheckItem("Migrations", lambda: None), CheckItem("Tests", lambda: None)]
    cl = Checklist("release", items)
    cl.run()
    return cl


@pytest.fixture()
def failing_checklist():
    def fail():
        raise AssertionError("service unreachable")

    items = [CheckItem("Health check", fail), CheckItem("Smoke test", lambda: None)]
    cl = Checklist("release", items)
    cl.run()
    return cl


# ---------------------------------------------------------------------------
# _build_payload tests
# ---------------------------------------------------------------------------


def test_payload_contains_header_block(passing_checklist):
    payload = _build_payload(passing_checklist)
    block_types = [b["type"] for b in payload["blocks"]]
    assert "header" in block_types


def test_payload_all_passed_message(passing_checklist):
    payload = _build_payload(passing_checklist)
    section_texts = [
        b["text"]["text"] for b in payload["blocks"] if b["type"] == "section"
    ]
    assert any("All checks passed" in t for t in section_texts)


def test_payload_failure_message(failing_checklist):
    payload = _build_payload(failing_checklist)
    section_texts = [
        b["text"]["text"] for b in payload["blocks"] if b["type"] == "section"
    ]
    assert any("Some checks failed" in t for t in section_texts)


def test_payload_includes_environment(passing_checklist):
    payload = _build_payload(passing_checklist, environment="staging")
    section_texts = [
        b["text"]["text"] for b in payload["blocks"] if b["type"] == "section"
    ]
    assert any("staging" in t for t in section_texts)


def test_payload_has_one_block_per_result(passing_checklist):
    payload = _build_payload(passing_checklist)
    # header + summary section + divider + N result sections + footer context
    result_blocks = [
        b for b in payload["blocks"]
        if b["type"] == "section" and b["text"]["text"].startswith((":white_check_mark:", ":x:", ":warning:", ":fast_forward:"))
    ]
    assert len(result_blocks) == len(passing_checklist.results)


# ---------------------------------------------------------------------------
# notify() tests
# ---------------------------------------------------------------------------


def test_notify_returns_true_on_200(passing_checklist):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = notify(passing_checklist, "https://hooks.slack.com/test")

    assert result is True


def test_notify_returns_false_on_exception(passing_checklist):
    with patch("urllib.request.urlopen", side_effect=OSError("network error")):
        result = notify(passing_checklist, "https://hooks.slack.com/test")

    assert result is False
