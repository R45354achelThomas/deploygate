"""Tests for the unified reporter module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from deploygate.checklist import CheckItem, Checklist, CheckResult, CheckStatus
from deploygate.reporter import Reporter, ReporterConfig, build_reporter_from_env


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def passing_checklist() -> Checklist:
    cl = Checklist(name="deploy-prod")
    cl.results.append(CheckResult(name="tests", status=CheckStatus.PASSED, message="OK"))
    cl.results.append(CheckResult(name="lint", status=CheckStatus.PASSED, message="OK"))
    return cl


@pytest.fixture()
def failing_checklist() -> Checklist:
    cl = Checklist(name="deploy-prod")
    cl.results.append(CheckResult(name="tests", status=CheckStatus.PASSED, message="OK"))
    cl.results.append(CheckResult(name="lint", status=CheckStatus.FAILED, message="Errors found"))
    return cl


# ---------------------------------------------------------------------------
# ReporterConfig defaults
# ---------------------------------------------------------------------------


def test_reporter_config_defaults():
    config = ReporterConfig()
    assert config.slack_webhook_url is None
    assert config.github_enabled is True
    assert config.exit_on_failure is True
    assert config.slack_username == "DeployGate"


# ---------------------------------------------------------------------------
# Reporter.report — GitHub path
# ---------------------------------------------------------------------------


@patch("deploygate.reporter.github.is_github_actions", return_value=True)
@patch("deploygate.reporter.github.report")
def test_report_calls_github_when_in_actions(mock_gh_report, _mock_is_ga, passing_checklist):
    reporter = Reporter(ReporterConfig(github_enabled=True))
    result = reporter.report(passing_checklist)
    mock_gh_report.assert_called_once_with(passing_checklist)
    assert result is True


@patch("deploygate.reporter.github.is_github_actions", return_value=False)
@patch("deploygate.reporter.github.report")
def test_report_skips_github_outside_actions(mock_gh_report, _mock_is_ga, passing_checklist):
    reporter = Reporter(ReporterConfig(github_enabled=True))
    reporter.report(passing_checklist)
    mock_gh_report.assert_not_called()


@patch("deploygate.reporter.github.is_github_actions", return_value=True)
@patch("deploygate.reporter.github.report")
def test_report_skips_github_when_disabled(mock_gh_report, _mock_is_ga, passing_checklist):
    reporter = Reporter(ReporterConfig(github_enabled=False))
    reporter.report(passing_checklist)
    mock_gh_report.assert_not_called()


# ---------------------------------------------------------------------------
# Reporter.report — Slack path
# ---------------------------------------------------------------------------


@patch("deploygate.reporter.slack.notify")
def test_report_calls_slack_when_webhook_set(mock_notify, passing_checklist):
    config = ReporterConfig(slack_webhook_url="https://hooks.slack.com/xxx", slack_channel="#deploys")
    reporter = Reporter(config)
    reporter.report(passing_checklist)
    mock_notify.assert_called_once()
    _, kwargs = mock_notify.call_args
    assert kwargs["webhook_url"] == "https://hooks.slack.com/xxx"
    assert kwargs["channel"] == "#deploys"


@patch("deploygate.reporter.slack.notify")
def test_report_skips_slack_when_no_webhook(mock_notify, passing_checklist):
    reporter = Reporter(ReporterConfig())
    reporter.report(passing_checklist)
    mock_notify.assert_not_called()


# ---------------------------------------------------------------------------
# build_reporter_from_env
# ---------------------------------------------------------------------------


def test_build_reporter_from_env_reads_env_vars(monkeypatch):
    monkeypatch.setenv("DEPLOYGATE_SLACK_WEBHOOK_URL", "https://hooks.slack.com/env")
    monkeypatch.setenv("DEPLOYGATE_SLACK_CHANNEL", "#ci")
    monkeypatch.setenv("DEPLOYGATE_GITHUB_ENABLED", "false")
    monkeypatch.setenv("DEPLOYGATE_EXIT_ON_FAILURE", "false")

    reporter = build_reporter_from_env()
    assert reporter.config.slack_webhook_url == "https://hooks.slack.com/env"
    assert reporter.config.slack_channel == "#ci"
    assert reporter.config.github_enabled is False
    assert reporter.config.exit_on_failure is False
