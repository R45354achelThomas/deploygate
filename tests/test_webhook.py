"""Tests for deploygate.webhook."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from deploygate.checklist import CheckResult, Checklist
from deploygate.webhook import WebhookConfig, _build_payload, notify


def _pass(name: str) -> CheckResult:
    return CheckResult(name=name, passed=True, message="ok")


def _fail(name: str) -> CheckResult:
    return CheckResult(name=name, passed=False, message="failed")


@pytest.fixture
def passing_checklist() -> Checklist:
    cl = Checklist(name="deploy-prod")
    cl.results = [_pass("smoke"), _pass("migrations")]
    return cl


@pytest.fixture
def failing_checklist() -> Checklist:
    cl = Checklist(name="deploy-prod")
    cl.results = [_pass("smoke"), _fail("migrations")]
    return cl


@pytest.fixture
def config() -> WebhookConfig:
    return WebhookConfig(url="https://hooks.example.com/deploy")


def test_payload_checklist_name(passing_checklist, config):
    payload = _build_payload(passing_checklist, config)
    assert payload["checklist"] == "deploy-prod"


def test_payload_passed_true(passing_checklist, config):
    payload = _build_payload(passing_checklist, config)
    assert payload["passed"] is True


def test_payload_passed_false(failing_checklist, config):
    payload = _build_payload(failing_checklist, config)
    assert payload["passed"] is False


def test_payload_failure_count(failing_checklist, config):
    payload = _build_payload(failing_checklist, config)
    assert payload["failures"] == 1


def test_payload_includes_results_by_default(passing_checklist, config):
    payload = _build_payload(passing_checklist, config)
    assert "results" in payload
    assert len(payload["results"]) == 2


def test_payload_omits_results_when_disabled(passing_checklist):
    cfg = WebhookConfig(url="https://hooks.example.com/deploy", include_results=False)
    payload = _build_payload(passing_checklist, cfg)
    assert "results" not in payload


def test_notify_returns_status_code(passing_checklist, config):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        status = notify(passing_checklist, config)
    assert status == 200


def test_notify_returns_none_on_error(passing_checklist, config):
    with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
        status = notify(passing_checklist, config)
    assert status is None


def test_notify_sends_json_body(passing_checklist, config):
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["data"] = json.loads(req.data.decode())
        mock_resp = MagicMock()
        mock_resp.status = 204
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        notify(passing_checklist, config)

    assert captured["data"]["checklist"] == "deploy-prod"
