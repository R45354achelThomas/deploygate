"""Deployment gate: block or allow a deploy based on checklist results and schedule."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from deploygate.checklist import Checklist
from deploygate.schedule import ScheduleConfig, any_open


@dataclass
class GateConfig:
    """Configuration for a deployment gate."""
    require_all_passed: bool = True
    enforce_schedule: bool = False
    schedule: Optional[ScheduleConfig] = None
    allowed_approvers: List[str] = field(default_factory=list)
    min_approvals: int = 0


@dataclass
class GateResult:
    """Result of evaluating a deployment gate."""
    allowed: bool
    reasons: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        status = "ALLOWED" if self.allowed else "BLOCKED"
        lines = [f"Gate: {status}"]
        for reason in self.reasons:
            lines.append(f"  - {reason}")
        return "\n".join(lines)


def evaluate(
    checklist: Checklist,
    config: GateConfig,
    approvers: Optional[List[str]] = None,
) -> GateResult:
    """Evaluate whether a deployment should be allowed."""
    reasons: List[str] = []
    allowed = True

    if config.require_all_passed and not checklist.all_passed:
        allowed = False
        failed = [r.name for r in checklist.results if not r.passed]
        reasons.append(f"Failing checks: {', '.join(failed)}")

    if config.enforce_schedule and config.schedule is not None:
        if not any_open(config.schedule):
            allowed = False
            reasons.append("Outside of allowed deployment window")

    if config.min_approvals > 0:
        approved_by = approvers or []
        if config.allowed_approvers:
            approved_by = [a for a in approved_by if a in config.allowed_approvers]
        if len(approved_by) < config.min_approvals:
            allowed = False
            reasons.append(
                f"Insufficient approvals: {len(approved_by)}/{config.min_approvals}"
            )

    if allowed:
        reasons.append("All gate conditions satisfied")

    return GateResult(allowed=allowed, reasons=reasons)
