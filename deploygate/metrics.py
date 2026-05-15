"""Metrics aggregation for checklist run history."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from deploygate.history import HistoryEntry


@dataclass
class ChecklistMetrics:
    name: str
    total_runs: int
    passed_runs: int
    failed_runs: int
    pass_rate: float
    avg_passed_checks: float
    avg_failed_checks: float
    last_run_at: str | None


def compute_metrics(entries: List[HistoryEntry]) -> ChecklistMetrics | None:
    """Compute aggregate metrics from a list of history entries.

    Returns None if the entry list is empty.
    """
    if not entries:
        return None

    name = entries[0]["name"]
    total = len(entries)
    passed = sum(1 for e in entries if e["passed"])
    failed = total - passed
    pass_rate = passed / total if total else 0.0
    avg_passed = sum(e["passed_count"] for e in entries) / total
    avg_failed = sum(e["failed_count"] for e in entries) / total
    last_run = entries[-1]["timestamp"] if entries else None

    return ChecklistMetrics(
        name=name,
        total_runs=total,
        passed_runs=passed,
        failed_runs=failed,
        pass_rate=round(pass_rate, 4),
        avg_passed_checks=round(avg_passed, 2),
        avg_failed_checks=round(avg_failed, 2),
        last_run_at=last_run,
    )


def format_metrics_table(metrics: ChecklistMetrics) -> str:
    """Return a human-readable text table for the given metrics."""
    lines = [
        f"Checklist : {metrics.name}",
        f"Total runs: {metrics.total_runs}",
        f"Passed    : {metrics.passed_runs}",
        f"Failed    : {metrics.failed_runs}",
        f"Pass rate : {metrics.pass_rate * 100:.1f}%",
        f"Avg passed checks: {metrics.avg_passed_checks}",
        f"Avg failed checks: {metrics.avg_failed_checks}",
        f"Last run  : {metrics.last_run_at or 'N/A'}",
    ]
    return "\n".join(lines)
