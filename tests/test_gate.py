"""Tests for deploygate.gate."""
from __future__ import annotations

import pytest

from deploygate.checklist import CheckItem, Checklist, CheckResult, CheckStatus
from deploygate.gate import GateConfig, GateResult, evaluate
from deploygate.schedule import DeployWindow, ScheduleConfig


def _pass(name="ok"):
    return CheckResult(name=name, status=CheckStatus.PASSED)


def _fail(name="bad"):
    return CheckResult(name=name, status=CheckStatus.FAILED)


@pytest.fixture
def passing_checklist():
    cl = Checklist(name="deploy")
    cl._results = [_pass("a"), _pass("b")]
    return cl


@pytest.fixture
def failing_checklist():
    cl = Checklist(name="deploy")
    cl._results = [_pass("a"), _fail("b")]
    return cl


# --- basic gate evaluation ---

def test_gate_allows_when_all_pass(passing_checklist):
    result = evaluate(passing_checklist, GateConfig())
    assert result.allowed is True


def test_gate_blocks_when_check_fails(failing_checklist):
    result = evaluate(failing_checklist, GateConfig())
    assert result.allowed is False


def test_gate_reason_lists_failing_check(failing_checklist):
    result = evaluate(failing_checklist, GateConfig())
    assert any("b" in r for r in result.reasons)


def test_gate_allows_failures_when_require_all_disabled(failing_checklist):
    config = GateConfig(require_all_passed=False)
    result = evaluate(failing_checklist, config)
    assert result.allowed is True


# --- schedule enforcement ---

def test_gate_blocks_outside_schedule(passing_checklist):
    # A window that is never open (empty days list)
    window = DeployWindow(name="never", days=[], start="09:00", end="17:00")
    schedule = ScheduleConfig(windows=[window])
    config = GateConfig(enforce_schedule=True, schedule=schedule)
    result = evaluate(passing_checklist, config)
    assert result.allowed is False


def test_gate_reason_mentions_schedule(passing_checklist):
    window = DeployWindow(name="never", days=[], start="09:00", end="17:00")
    schedule = ScheduleConfig(windows=[window])
    config = GateConfig(enforce_schedule=True, schedule=schedule)
    result = evaluate(passing_checklist, config)
    assert any("window" in r.lower() for r in result.reasons)


# --- approval enforcement ---

def test_gate_blocks_without_required_approvals(passing_checklist):
    config = GateConfig(min_approvals=2)
    result = evaluate(passing_checklist, config, approvers=["alice"])
    assert result.allowed is False


def test_gate_allows_with_sufficient_approvals(passing_checklist):
    config = GateConfig(min_approvals=2)
    result = evaluate(passing_checklist, config, approvers=["alice", "bob"])
    assert result.allowed is True


def test_gate_filters_approvers_by_allowed_list(passing_checklist):
    config = GateConfig(min_approvals=1, allowed_approvers=["alice"])
    result = evaluate(passing_checklist, config, approvers=["eve"])
    assert result.allowed is False


# --- GateResult __str__ ---

def test_gate_result_str_allowed():
    r = GateResult(allowed=True, reasons=["All gate conditions satisfied"])
    assert "ALLOWED" in str(r)


def test_gate_result_str_blocked():
    r = GateResult(allowed=False, reasons=["Failing checks: x"])
    assert "BLOCKED" in str(r)
    assert "x" in str(r)
