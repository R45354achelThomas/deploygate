"""Tests for deploygate.notify email notification module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from deploygate.checklist import CheckItem, CheckResult, CheckStatus, Checklist
from deploygate.notify import EmailConfig, _build_body, _build_subject, notify


@pytest.fixture
def passing_checklist():
    results = [
        CheckResult(name="Migrations", status=CheckStatus.PASSED, message=""),
        CheckResult(name="Tests", status=CheckStatus.PASSED, message=""),
    ]
    cl = MagicMock(spec=Checklist)
    cl.name = "Production Deploy"
    cl.passed = True
    cl.results = results
    return cl


@pytest.fixture
def failing_checklist():
    results = [
        CheckResult(name="Migrations", status=CheckStatus.PASSED, message=""),
        CheckResult(name="Tests", status=CheckStatus.FAILED, message="2 tests failed"),
    ]
    cl = MagicMock(spec=Checklist)
    cl.name = "Staging Deploy"
    cl.passed = False
    cl.results = results
    return cl


def test_subject_passed(passing_checklist):
    subject = _build_subject(passing_checklist)
    assert "PASSED" in subject
    assert "Production Deploy" in subject


def test_subject_failed(failing_checklist):
    subject = _build_subject(failing_checklist)
    assert "FAILED" in subject
    assert "Staging Deploy" in subject


def test_body_contains_checklist_name(passing_checklist):
    body = _build_body(passing_checklist)
    assert "Production Deploy" in body


def test_body_contains_check_names(failing_checklist):
    body = _build_body(failing_checklist)
    assert "Migrations" in body
    assert "Tests" in body


def test_body_contains_failure_message(failing_checklist):
    body = _build_body(failing_checklist)
    assert "2 tests failed" in body


def test_notify_returns_false_with_no_recipients(passing_checklist):
    config = EmailConfig(recipients=[])
    result = notify(passing_checklist, config)
    assert result is False


def test_notify_sends_email(passing_checklist):
    mock_smtp = MagicMock()
    mock_instance = MagicMock()
    mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_instance)
    mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

    config = EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        sender="ci@example.com",
        recipients=["team@example.com"],
        use_tls=False,
    )
    result = notify(passing_checklist, config, _smtp_cls=mock_smtp)
    assert result is True
    mock_instance.sendmail.assert_called_once()


def test_notify_returns_false_on_smtp_error(passing_checklist):
    import smtplib

    mock_smtp = MagicMock()
    mock_smtp.return_value.__enter__ = MagicMock(side_effect=smtplib.SMTPException("err"))
    mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

    config = EmailConfig(recipients=["team@example.com"])
    result = notify(passing_checklist, config, _smtp_cls=mock_smtp)
    assert result is False
