"""Deployment history tracking — persists checklist run results to a local JSON file."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from deploygate.checklist import Checklist, CheckStatus

DEFAULT_HISTORY_FILE = ".deploygate_history.json"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _checklist_to_entry(checklist: Checklist, timestamp: Optional[str] = None) -> dict:
    """Serialise a Checklist run into a history entry dict."""
    return {
        "timestamp": timestamp or _utcnow(),
        "name": checklist.name,
        "passed": checklist.passed,
        "total": len(checklist.results),
        "failed": sum(1 for r in checklist.results if r.status == CheckStatus.FAILED),
        "errored": sum(1 for r in checklist.results if r.status == CheckStatus.ERROR),
        "checks": [
            {
                "name": r.name,
                "status": r.status.value,
                "message": r.message,
            }
            for r in checklist.results
        ],
    }


def load_history(path: str = DEFAULT_HISTORY_FILE) -> List[dict]:
    """Load existing history entries from *path*. Returns an empty list if the file does not exist."""
    file = Path(path)
    if not file.exists():
        return []
    with file.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError(f"History file {path!r} must contain a JSON array.")
    return data


def save_history(entries: List[dict], path: str = DEFAULT_HISTORY_FILE) -> None:
    """Persist *entries* to *path*, creating parent directories as needed."""
    file = Path(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    with file.open("w", encoding="utf-8") as fh:
        json.dump(entries, fh, indent=2)


def record(checklist: Checklist, path: str = DEFAULT_HISTORY_FILE) -> dict:
    """Append the current checklist run to the history file and return the new entry."""
    entries = load_history(path)
    entry = _checklist_to_entry(checklist)
    entries.append(entry)
    save_history(entries, path)
    return entry


def last_run(path: str = DEFAULT_HISTORY_FILE) -> Optional[dict]:
    """Return the most recent history entry, or *None* if history is empty."""
    entries = load_history(path)
    return entries[-1] if entries else None
