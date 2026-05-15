"""Approval gate — require explicit sign-off before a deploy proceeds."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class ApprovalEntry:
    checklist: str
    approved_by: str
    approved_at: str  # ISO-8601
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "checklist": self.checklist,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "note": self.note,
        }

    @staticmethod
    def from_dict(d: dict) -> "ApprovalEntry":
        return ApprovalEntry(
            checklist=d["checklist"],
            approved_by=d["approved_by"],
            approved_at=d["approved_at"],
            note=d.get("note", ""),
        )


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_approvals(path: Path) -> List[ApprovalEntry]:
    """Load approval entries from a JSON file."""
    if not path.exists():
        return []
    with path.open() as fh:
        data = json.load(fh)
    return [ApprovalEntry.from_dict(d) for d in data]


def save_approvals(path: Path, entries: List[ApprovalEntry]) -> None:
    """Persist approval entries to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump([e.to_dict() for e in entries], fh, indent=2)


def approve(
    path: Path,
    checklist: str,
    approved_by: str,
    note: str = "",
) -> ApprovalEntry:
    """Record an approval and return the new entry."""
    entries = load_approvals(path)
    entry = ApprovalEntry(
        checklist=checklist,
        approved_by=approved_by,
        approved_at=_utcnow(),
        note=note,
    )
    entries.append(entry)
    save_approvals(path, entries)
    return entry


def is_approved(path: Path, checklist: str) -> bool:
    """Return True if at least one approval exists for *checklist*."""
    return any(e.checklist == checklist for e in load_approvals(path))


def latest_approval(path: Path, checklist: str) -> Optional[ApprovalEntry]:
    """Return the most recent approval for *checklist*, or None."""
    matches = [e for e in load_approvals(path) if e.checklist == checklist]
    return matches[-1] if matches else None
