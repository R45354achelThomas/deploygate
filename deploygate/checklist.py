"""Core checklist runner module for deploygate."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Optional
import time


class CheckStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class CheckResult:
    name: str
    status: CheckStatus
    message: str = ""
    duration_ms: float = 0.0

    @property
    def passed(self) -> bool:
        return self.status == CheckStatus.PASSED


@dataclass
class CheckItem:
    name: str
    fn: Callable[[], bool]
    description: str = ""
    required: bool = True
    skip: bool = False


@dataclass
class Checklist:
    name: str
    checks: List[CheckItem] = field(default_factory=list)
    results: List[CheckResult] = field(default_factory=list)

    def add(self, check: CheckItem) -> None:
        self.checks.append(check)

    def run(self) -> bool:
        self.results = []
        all_passed = True

        for check in self.checks:
            if check.skip:
                self.results.append(
                    CheckResult(name=check.name, status=CheckStatus.SKIPPED)
                )
                continue

            start = time.monotonic()
            try:
                success = check.fn()
                duration = (time.monotonic() - start) * 1000
                status = CheckStatus.PASSED if success else CheckStatus.FAILED
                message = "" if success else f"Check '{check.name}' returned False"
            except Exception as exc:
                duration = (time.monotonic() - start) * 1000
                status = CheckStatus.FAILED
                message = str(exc)
                success = False

            result = CheckResult(
                name=check.name,
                status=status,
                message=message,
                duration_ms=duration,
            )
            self.results.append(result)

            if not success and check.required:
                all_passed = False

        return all_passed

    @property
    def summary(self) -> dict:
        return {
            "checklist": self.name,
            "total": len(self.results),
            "passed": sum(1 for r in self.results if r.status == CheckStatus.PASSED),
            "failed": sum(1 for r in self.results if r.status == CheckStatus.FAILED),
            "skipped": sum(1 for r in self.results if r.status == CheckStatus.SKIPPED),
            "results": [
                {"name": r.name, "status": r.status.value, "message": r.message, "duration_ms": round(r.duration_ms, 2)}
                for r in self.results
            ],
        }
