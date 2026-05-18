"""Tests for deploygate.policy."""
import pytest

from deploygate.checklist import CheckResult, CheckStatus, Checklist
from deploygate.policy import PolicyRule, PolicyResult, evaluate_policy


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _pass(name="ok"):
    return CheckResult(name=name, status=CheckStatus.PASSED, message="ok")


def _fail(name="bad"):
    return CheckResult(name=name, status=CheckStatus.FAILED, message="fail")


def _error(name="err"):
    return CheckResult(name=name, status=CheckStatus.ERROR, message="boom")


@pytest.fixture()
def passing_checklist(mocker):
    cl = mocker.MagicMock(spec=Checklist)
    cl.name = "deploy"
    cl.run.return_value = [_pass("check-a"), _pass("check-b")]
    return cl


@pytest.fixture()
def failing_checklist(mocker):
    cl = mocker.MagicMock(spec=Checklist)
    cl.name = "deploy"
    cl.run.return_value = [_pass("check-a"), _fail("check-b")]
    return cl


@pytest.fixture()
def error_checklist(mocker):
    cl = mocker.MagicMock(spec=Checklist)
    cl.name = "deploy"
    cl.run.return_value = [_pass("check-a"), _error("check-b")]
    return cl


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_allowed_when_all_pass(passing_checklist):
    rule = PolicyRule(name="strict")
    result = evaluate_policy(passing_checklist, rule)
    assert result.allowed is True


def test_blocked_when_check_fails(failing_checklist):
    rule = PolicyRule(name="strict")
    result = evaluate_policy(failing_checklist, rule)
    assert result.allowed is False


def test_blocked_reason_mentions_pass_rate(failing_checklist):
    rule = PolicyRule(name="strict", min_pass_rate=1.0)
    result = evaluate_policy(failing_checklist, rule)
    assert any("pass rate" in r for r in result.reasons)


def test_partial_pass_rate_allowed(failing_checklist):
    rule = PolicyRule(name="relaxed", min_pass_rate=0.5)
    result = evaluate_policy(failing_checklist, rule)
    assert result.allowed is True


def test_blocked_on_error_by_default(error_checklist):
    rule = PolicyRule(name="strict")
    result = evaluate_policy(error_checklist, rule)
    assert result.allowed is False
    assert any("error" in r for r in result.reasons)


def test_not_blocked_on_error_when_disabled(error_checklist):
    rule = PolicyRule(name="lenient", block_on_error=False, min_pass_rate=0.5)
    result = evaluate_policy(error_checklist, rule)
    assert result.allowed is True


def test_required_check_missing_blocks(passing_checklist):
    rule = PolicyRule(name="req", required_checks=["nonexistent"])
    result = evaluate_policy(passing_checklist, rule)
    assert result.allowed is False
    assert any("nonexistent" in r for r in result.reasons)


def test_required_check_present_and_passing(passing_checklist):
    rule = PolicyRule(name="req", required_checks=["check-a"])
    result = evaluate_policy(passing_checklist, rule)
    assert result.allowed is True


def test_empty_checklist_blocks(mocker):
    cl = mocker.MagicMock(spec=Checklist)
    cl.run.return_value = []
    rule = PolicyRule(name="empty")
    result = evaluate_policy(cl, rule)
    assert result.allowed is False


def test_policy_result_rule_reference(passing_checklist):
    rule = PolicyRule(name="my-rule")
    result = evaluate_policy(passing_checklist, rule)
    assert result.rule is rule
