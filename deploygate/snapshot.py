"""Snapshot support: capture and compare checklist results across runs."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from deploygate.checklist import CheckResult, CheckStatus, Checklist


@dataclass
class SnapshotEntry:
    name: str
    status: str  # "passed" | "failed" | "error"
    timestamp: str


@dataclass
class SnapshotDiff:
    name: str
    previous: Optional[str]
    current: str

    @property
    def regressed(self) -> bool:
        return self.previous == CheckStatus.PASSED.value and self.current != CheckStatus.PASSED.value

    @property
    def recovered(self) -> bool:
        return self.previous != CheckStatus.PASSED.value and self.current == CheckStatus.PASSED.value

    @property
    def changed(self) -> bool:
        return self.previous != self.current


def _utcnow() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _checklist_to_entries(checklist: Checklist) -> List[SnapshotEntry]:
    entries = []
    for result in checklist.results:
        entries.append(
            SnapshotEntry(
                name=result.name,
                status=result.status.value,
                timestamp=_utcnow(),
            )
        )
    return entries


def save_snapshot(checklist: Checklist, path: str) -> None:
    """Persist the current checklist results to *path* as JSON."""
    entries = _checklist_to_entries(checklist)
    data = [asdict(e) for e in entries]
    Path(path).write_text(json.dumps(data, indent=2))


def load_snapshot(path: str) -> Dict[str, str]:
    """Return a mapping of check name -> status from a saved snapshot file."""
    raw = json.loads(Path(path).read_text())
    return {item["name"]: item["status"] for item in raw}


def diff_snapshot(checklist: Checklist, path: str) -> List[SnapshotDiff]:
    """Compare *checklist* results against the snapshot stored at *path*.

    Returns a list of :class:`SnapshotDiff` objects for every check,
    including checks that are new (no previous entry).
    """
    previous: Dict[str, str] = {}
    if os.path.exists(path):
        previous = load_snapshot(path)

    diffs = []
    for result in checklist.results:
        diffs.append(
            SnapshotDiff(
                name=result.name,
                previous=previous.get(result.name),
                current=result.status.value,
            )
        )
    return diffs
