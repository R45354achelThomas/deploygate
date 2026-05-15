"""Periodic digest report builder for deploygate checklists."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from deploygate.history import load_history
from deploygate.metrics import compute_metrics, format_metrics_table


@dataclass
class DigestReport:
    """Holds a rendered digest report."""

    period_label: str
    since: datetime
    until: datetime
    checklist_filter: Optional[str]
    body: str

    def __str__(self) -> str:  # pragma: no cover
        return self.body


def _period_bounds(period: str, now: Optional[datetime] = None) -> tuple[datetime, datetime]:
    """Return (since, until) UTC datetimes for the given period string."""
    until = now or datetime.now(tz=timezone.utc)
    periods = {
        "daily": timedelta(days=1),
        "weekly": timedelta(weeks=1),
        "monthly": timedelta(days=30),
    }
    if period not in periods:
        raise ValueError(f"Unknown period '{period}'. Choose from: {', '.join(periods)}.")
    since = until - periods[period]
    return since, until


def build_digest(
    history_file: str,
    period: str = "weekly",
    checklist: Optional[str] = None,
    now: Optional[datetime] = None,
) -> DigestReport:
    """Build a digest report from history for the given period."""
    since, until = _period_bounds(period, now)

    entries = load_history(history_file)
    # Filter by time window
    entries = [
        e for e in entries
        if since <= datetime.fromisoformat(e["timestamp"]) <= until
    ]
    # Optionally filter by checklist name
    if checklist:
        entries = [e for e in entries if e.get("name") == checklist]

    lines: List[str] = [
        f"# DeployGate Digest ({period.capitalize()})",
        f"Period: {since.strftime('%Y-%m-%d %H:%M')} UTC — {until.strftime('%Y-%m-%d %H:%M')} UTC",
        "",
    ]

    if not entries:
        lines.append("_No runs recorded in this period._")
    else:
        metrics = compute_metrics(entries)
        if metrics:
            lines.append(format_metrics_table([metrics]))
        else:
            lines.append("_No metrics available._")

    body = "\n".join(lines)
    return DigestReport(
        period_label=period,
        since=since,
        until=until,
        checklist_filter=checklist,
        body=body,
    )
