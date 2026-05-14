"""Unified reporter that aggregates GitHub and Slack notifications."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from deploygate.checklist import Checklist
from deploygate import github, slack


@dataclass
class ReporterConfig:
    """Configuration for the unified reporter."""

    slack_webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None
    slack_username: str = "DeployGate"
    slack_icon_emoji: str = ":rocket:"
    github_enabled: bool = True
    exit_on_failure: bool = True
    extra_context: dict = field(default_factory=dict)


class Reporter:
    """Runs all configured reporters against a completed checklist."""

    def __init__(self, config: ReporterConfig) -> None:
        self.config = config
        self._errors: list[str] = []

    def report(self, checklist: Checklist) -> bool:
        """Send reports to all configured destinations.

        Returns True if all reports were sent successfully.
        """
        success = True

        if self.config.github_enabled and github.is_github_actions():
            try:
                github.report(checklist)
            except Exception as exc:  # pragma: no cover
                self._errors.append(f"GitHub reporting failed: {exc}")
                success = False

        if self.config.slack_webhook_url:
            try:
                slack.notify(
                    checklist,
                    webhook_url=self.config.slack_webhook_url,
                    channel=self.config.slack_channel,
                    username=self.config.slack_username,
                    icon_emoji=self.config.slack_icon_emoji,
                )
            except Exception as exc:  # pragma: no cover
                self._errors.append(f"Slack reporting failed: {exc}")
                success = False

        return success

    @property
    def errors(self) -> list[str]:
        """Return any errors encountered during reporting."""
        return list(self._errors)


def build_reporter_from_env() -> Reporter:
    """Build a Reporter using environment variables for configuration."""
    import os

    config = ReporterConfig(
        slack_webhook_url=os.environ.get("DEPLOYGATE_SLACK_WEBHOOK_URL"),
        slack_channel=os.environ.get("DEPLOYGATE_SLACK_CHANNEL"),
        slack_username=os.environ.get("DEPLOYGATE_SLACK_USERNAME", "DeployGate"),
        slack_icon_emoji=os.environ.get("DEPLOYGATE_SLACK_ICON_EMOJI", ":rocket:"),
        github_enabled=os.environ.get("DEPLOYGATE_GITHUB_ENABLED", "true").lower() == "true",
        exit_on_failure=os.environ.get("DEPLOYGATE_EXIT_ON_FAILURE", "true").lower() == "true",
    )
    return Reporter(config)
