"""Tests for the core checklist runner."""

import pytest
from deploygate.checklist import CheckItem, Checklist, CheckStatus


def always_pass() -> bool:
    return True


def always_fail() -> bool:
    return False


def raises_error() -> bool:
    raise RuntimeError("Something went wrong")


@pytest.fixture
def basic_checklist() -> Checklist:
    cl = Checklist(name="pre-deploy")
    cl.add(CheckItem(name="health-check", fn=always_pass, description="Service is healthy"))
    cl.add(CheckItem(name="migrations-check", fn=always_pass, description="Migrations are up to date"))
    return cl


def test_all_checks_pass(basic_checklist):
    result = basic_checklist.run()
    assert result is True
    assert all(r.status == CheckStatus.PASSED for r in basic_checklist.results)


def test_required_failure_returns_false():
    cl = Checklist(name="test")
    cl.add(CheckItem(name="failing-check", fn=always_fail, required=True))
    assert cl.run() is False


def test_optional_failure_does_not_block():
    cl = Checklist(name="test")
    cl.add(CheckItem(name="optional-fail", fn=always_fail, required=False))
    assert cl.run() is True


def test_skipped_check():
    cl = Checklist(name="test")
    cl.add(CheckItem(name="skipped", fn=always_fail, skip=True))
    cl.run()
    assert cl.results[0].status == CheckStatus.SKIPPED


def test_exception_marks_check_failed():
    cl = Checklist(name="test")
    cl.add(CheckItem(name="error-check", fn=raises_error, required=True))
    result = cl.run()
    assert result is False
    assert cl.results[0].status == CheckStatus.FAILED
    assert "Something went wrong" in cl.results[0].message


def test_summary_structure(basic_checklist):
    basic_checklist.run()
    summary = basic_checklist.summary
    assert summary["checklist"] == "pre-deploy"
    assert summary["total"] == 2
    assert summary["passed"] == 2
    assert summary["failed"] == 0
    assert summary["skipped"] == 0
    assert len(summary["results"]) == 2


def test_duration_is_recorded(basic_checklist):
    basic_checklist.run()
    for result in basic_checklist.results:
        assert result.duration_ms >= 0
