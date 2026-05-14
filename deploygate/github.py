"""GitHub Actions integration for deploygate."""

import os
from typing import Optional

from deploygate.checklist import Checklist, CheckStatus


GITHUB_OUTPUT = os.environ.get("GITHUB_OUTPUT", "")
GITHUB_STEP_SUMMARY = os.environ.get("GITHUB_STEP_SUMMARY", "")


def is_github_actions() -> bool:
    """Return True if running inside a GitHub Actions environment."""
    return os.environ.get("GITHUB_ACTIONS") == "true"


def set_output(name: str, value: str) -> None:
    """Write a GitHub Actions output variable."""
    if GITHUB_OUTPUT:
        with open(GITHUB_OUTPUT, "a") as fh:
            fh.write(f"{name}={value}\n")
    else:
        # Fallback for older runner versions
        print(f"::set-output name={name}::{value}")


def write_step_summary(markdown: str) -> None:
    """Append markdown content to the GitHub Actions step summary."""
    if GITHUB_STEP_SUMMARY:
        with open(GITHUB_STEP_SUMMARY, "a") as fh:
            fh.write(markdown + "\n")


def build_summary_markdown(checklist: Checklist) -> str:
    """Build a Markdown summary table from a Checklist."""
    lines = [
        f"## {checklist.name} — Deploy Checklist",
        "",
        "| Check | Status | Message |",
        "| ----- | ------ | ------- |",
    ]
    for result in checklist.results:
        icon = "✅" if result.status == CheckStatus.PASSED else "❌"
        msg = result.message or ""
        lines.append(f"| {result.name} | {icon} {result.status.value} | {msg} |")

    overall = "✅ All checks passed" if checklist.passed else "❌ Some checks failed"
    lines += ["", f"**Overall:** {overall}"]
    return "\n".join(lines)


def report(checklist: Checklist) -> None:
    """Emit GitHub Actions outputs and step summary for a completed checklist."""
    passed_str = "true" if checklist.passed else "false"
    set_output("passed", passed_str)
    set_output("checklist_name", checklist.name)

    failed = [r.name for r in checklist.results if r.status != CheckStatus.PASSED]
    set_output("failed_checks", ",".join(failed))

    summary = build_summary_markdown(checklist)
    write_step_summary(summary)
