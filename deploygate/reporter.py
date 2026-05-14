"""High-level reporter that orchestrates GitHub, Slack, and history recording."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from deploygate import github, slack
from deploygate.checklist import Checklist


@dataclass
class ReporterConfig:
    """Configuration for the Reporter."""

    slack_webhook: Optional[str] = None
    """If set, a Slack notification is sent after every run."""

    history_file: Optional[str] = None
    """If set, results are appended to this JSON history file."""

    fail_on_error: bool = True
    """Whether an errored check should be treated as a failure."""


class Reporter:
    """Runs all post-checklist reporting side-effects in one place."""

    def __init__(self, config: Optional[ReporterConfig] = None) -> None:
        self.config: ReporterConfig = config or ReporterConfig()
        self._errors: List[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def report(self, checklist: Checklist) -> None:
        """Execute all configured reporters for *checklist*."""
        self._errors.clear()
        self._report_github(checklist)
        self._report_slack(checklist)
        self._record_history(checklist)

    @property
    def errors(self) -> List[str]:
        """Accumulated non-fatal errors from the last :meth:`report` call."""
        return list(self._errors)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _report_github(self, checklist: Checklist) -> None:
        if not github.is_github_actions():
            return
        try:
            github.report(checklist)
        except Exception as exc:  # pragma: no cover
            self._errors.append(f"GitHub reporting failed: {exc}")

    def _report_slack(self, checklist: Checklist) -> None:
        webhook = self.config.slack_webhook
        if not webhook:
            return
        try:
            slack.notify(checklist, webhook)
        except Exception as exc:
            self._errors.append(f"Slack notification failed: {exc}")

    def _record_history(self, checklist: Checklist) -> None:
        path = self.config.history_file
        if not path:
            return
        try:
            from deploygate import history as _history

            _history.record(checklist, path)
        except Exception as exc:
            self._errors.append(f"History recording failed: {exc}")
