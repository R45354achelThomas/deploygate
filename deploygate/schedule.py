"""Scheduled deployment window checker for deploygate."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import List, Optional


@dataclass
class DeployWindow:
    """Defines an allowed deployment time window."""

    name: str
    days: List[int]  # 0=Monday ... 6=Sunday
    start: time
    end: time
    timezone: str = "UTC"

    def is_open(self, at: Optional[datetime] = None) -> bool:
        """Return True if *at* (default: now UTC) falls within this window."""
        if at is None:
            at = datetime.utcnow()
        if at.weekday() not in self.days:
            return False
        current = at.time().replace(second=0, microsecond=0)
        return self.start <= current <= self.end


@dataclass
class ScheduleConfig:
    """Collection of deployment windows."""

    windows: List[DeployWindow] = field(default_factory=list)
    block_outside_windows: bool = True

    def any_open(self, at: Optional[datetime] = None) -> bool:
        """Return True if at least one window is currently open."""
        return any(w.is_open(at) for w in self.windows)

    def active_window(self, at: Optional[datetime] = None) -> Optional[DeployWindow]:
        """Return the first open window, or None."""
        for w in self.windows:
            if w.is_open(at):
                return w
        return None


def is_deploy_allowed(config: ScheduleConfig, at: Optional[datetime] = None) -> bool:
    """Return True when deployment is permitted according to *config*."""
    if not config.block_outside_windows:
        return True
    if not config.windows:
        return True
    return config.any_open(at)
