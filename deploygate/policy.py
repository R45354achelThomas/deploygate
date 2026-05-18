"""Deployment policy enforcement — block deploys based on configurable rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from deploygate.checklist import Checklist, CheckStatus


@dataclass
class PolicyRule:
    """A single policy rule that can block a deployment."""
    name: str
    min_pass_rate: float = 1.0          # 0.0 – 1.0
    required_checks: List[str] = field(default_factory=list)
    block_on_error: bool = True


@dataclass
class PolicyResult:
    """Outcome of evaluating a PolicyRule against a Checklist."""
    rule: PolicyRule
    allowed: bool
    reasons: List[str] = field(default_factory=list)

    def __str__(self) -> str:  # pragma: no cover
        status = "ALLOWED" if self.allowed else "BLOCKED"
        detail = "; ".join(self.reasons) if self.reasons else "all conditions met"
        return f"[{status}] {self.rule.name}: {detail}"


def evaluate_policy(checklist: Checklist, rule: PolicyRule) -> PolicyResult:
    """Evaluate *rule* against *checklist* and return a PolicyResult."""
    reasons: List[str] = []

    results = checklist.run()
    total = len(results)
    if total == 0:
        reasons.append("no checks were executed")
        return PolicyResult(rule=rule, allowed=False, reasons=reasons)

    passed = sum(1 for r in results if r.status == CheckStatus.PASSED)
    errors = sum(1 for r in results if r.status == CheckStatus.ERROR)
    pass_rate = passed / total

    if rule.block_on_error and errors:
        reasons.append(f"{errors} check(s) raised errors")

    if pass_rate < rule.min_pass_rate:
        pct = int(rule.min_pass_rate * 100)
        actual = int(pass_rate * 100)
        reasons.append(f"pass rate {actual}% is below required {pct}%")

    result_map = {r.name: r for r in results}
    for check_name in rule.required_checks:
        r = result_map.get(check_name)
        if r is None:
            reasons.append(f"required check '{check_name}' not found")
        elif r.status != CheckStatus.PASSED:
            reasons.append(f"required check '{check_name}' did not pass")

    return PolicyResult(rule=rule, allowed=len(reasons) == 0, reasons=reasons)
