"""Slack notification support for deploygate checklist results."""

from __future__ import annotations

import json
import urllib.request
from typing import Optional

from deploygate.checklist import CheckStatus, Checklist


STATUS_EMOJI = {
    CheckStatus.PASSED: ":white_check_mark:",
    CheckStatus.FAILED: ":x:",
    CheckStatus.ERROR: ":warning:",
    CheckStatus.SKIPPED: ":fast_forward:",
}


def _build_payload(checklist: Checklist, environment: Optional[str] = None) -> dict:
    """Build a Slack Block Kit message payload from checklist results."""
    overall = ":white_check_mark: *All checks passed*" if checklist.passed else ":x: *Some checks failed*"
    env_text = f" — `{environment}`" if environment else ""
    header = f"{overall}{env_text}"

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "DeployGate Checklist", "emoji": True},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": header},
        },
        {"type": "divider"},
    ]

    for result in checklist.results:
        emoji = STATUS_EMOJI.get(result.status, ":question:")
        line = f"{emoji} *{result.name}*"
        if result.message:
            line += f"\n> {result.message}"
        blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": line}}
        )

    summary = checklist.summary()
    footer = (
        f"Passed: {summary['passed']}  "
        f"Failed: {summary['failed']}  "
        f"Errors: {summary['errors']}  "
        f"Skipped: {summary['skipped']}"
    )
    blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": footer}]})

    return {"blocks": blocks}


def notify(
    checklist: Checklist,
    webhook_url: str,
    environment: Optional[str] = None,
    timeout: int = 10,
) -> bool:
    """Send checklist results to a Slack incoming webhook.

    Returns True on success, False on failure.
    """
    payload = _build_payload(checklist, environment=environment)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:  # noqa: BLE001
        return False
