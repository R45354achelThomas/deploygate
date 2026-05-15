"""Tests for deploygate.metrics."""
import pytest

from deploygate.metrics import ChecklistMetrics, compute_metrics, format_metrics_table


def _make_entry(name="deploy", passed=True, passed_count=3, failed_count=0, timestamp="2024-01-01T00:00:00Z"):
    return {
        "name": name,
        "passed": passed,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "timestamp": timestamp,
    }


@pytest.fixture
def mixed_entries():
    return [
        _make_entry(passed=True, passed_count=3, failed_count=0, timestamp="2024-01-01T00:00:00Z"),
        _make_entry(passed=False, passed_count=2, failed_count=1, timestamp="2024-01-02T00:00:00Z"),
        _make_entry(passed=True, passed_count=3, failed_count=0, timestamp="2024-01-03T00:00:00Z"),
        _make_entry(passed=False, passed_count=1, failed_count=2, timestamp="2024-01-04T00:00:00Z"),
    ]


def test_compute_metrics_returns_none_for_empty():
    assert compute_metrics([]) is None


def test_compute_metrics_total_runs(mixed_entries):
    m = compute_metrics(mixed_entries)
    assert m.total_runs == 4


def test_compute_metrics_passed_runs(mixed_entries):
    m = compute_metrics(mixed_entries)
    assert m.passed_runs == 2


def test_compute_metrics_failed_runs(mixed_entries):
    m = compute_metrics(mixed_entries)
    assert m.failed_runs == 2


def test_compute_metrics_pass_rate(mixed_entries):
    m = compute_metrics(mixed_entries)
    assert m.pass_rate == 0.5


def test_compute_metrics_avg_passed_checks(mixed_entries):
    m = compute_metrics(mixed_entries)
    assert m.avg_passed_checks == pytest.approx(2.25)


def test_compute_metrics_avg_failed_checks(mixed_entries):
    m = compute_metrics(mixed_entries)
    assert m.avg_failed_checks == pytest.approx(0.75)


def test_compute_metrics_last_run_at(mixed_entries):
    m = compute_metrics(mixed_entries)
    assert m.last_run_at == "2024-01-04T00:00:00Z"


def test_compute_metrics_name(mixed_entries):
    m = compute_metrics(mixed_entries)
    assert m.name == "deploy"


def test_format_metrics_table_contains_name(mixed_entries):
    m = compute_metrics(mixed_entries)
    table = format_metrics_table(m)
    assert "deploy" in table


def test_format_metrics_table_contains_pass_rate(mixed_entries):
    m = compute_metrics(mixed_entries)
    table = format_metrics_table(m)
    assert "50.0%" in table


def test_format_metrics_table_contains_last_run(mixed_entries):
    m = compute_metrics(mixed_entries)
    table = format_metrics_table(m)
    assert "2024-01-04" in table
