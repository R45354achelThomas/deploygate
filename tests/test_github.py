"""Tests for deploygate.github module."""

import pytest

from deploygate.checklist import CheckResult, CheckStatus, Checklist
from deploygate.github import build_summary_markdown, report, set_output


@pytest.fixture()
def passing_checklist():
    cl = Checklist(name="Release v1.0")
    cl.results = [
        CheckResult(name="Lint", status=CheckStatus.PASSED, message="All good"),
        CheckResult(name="Tests", status=CheckStatus.PASSED, message="100% pass"),
    ]
    return cl


@pytest.fixture()
def failing_checklist():
    cl = Checklist(name="Release v1.0")
    cl.results = [
        CheckResult(name="Lint", status=CheckStatus.PASSED, message="All good"),
        CheckResult(name="Tests", status=CheckStatus.FAILED, message="2 failures"),
    ]
    return cl


@pytest.fixture()
def github_output_env(tmp_path, monkeypatch):
    """Set up a temporary GITHUB_OUTPUT file and patch the module-level variable."""
    import deploygate.github as gh

    output_file = tmp_path / "github_output"
    output_file.touch()
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    monkeypatch.setattr(gh, "GITHUB_OUTPUT", str(output_file))
    monkeypatch.setattr(gh, "GITHUB_STEP_SUMMARY", "")
    return output_file


def test_summary_contains_checklist_name(passing_checklist):
    md = build_summary_markdown(passing_checklist)
    assert "Release v1.0" in md


def test_summary_passed_icon(passing_checklist):
    md = build_summary_markdown(passing_checklist)
    assert "✅" in md
    assert "❌" not in md


def test_summary_failed_icon(failing_checklist):
    md = build_summary_markdown(failing_checklist)
    assert "❌" in md


def test_summary_overall_passed(passing_checklist):
    md = build_summary_markdown(passing_checklist)
    assert "All checks passed" in md


def test_summary_overall_failed(failing_checklist):
    md = build_summary_markdown(failing_checklist)
    assert "Some checks failed" in md


def test_summary_contains_check_names(passing_checklist):
    md = build_summary_markdown(passing_checklist)
    assert "Lint" in md
    assert "Tests" in md


def test_report_writes_outputs(github_output_env, passing_checklist):
    report(passing_checklist)
    content = github_output_env.read_text()
    assert "passed=true" in content
    assert "checklist_name=Release v1.0" in content
    assert "failed_checks=" in content


def test_report_failed_checks_listed(github_output_env, failing_checklist):
    report(failing_checklist)
    content = github_output_env.read_text()
    assert "passed=false" in content
    assert "Tests" in content
