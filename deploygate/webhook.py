"""Generic webhook notification support for deploygate."""
from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from deploygate.checklist import Checklist


@dataclass
class WebhookConfig:
    url: str
    method: str = "POST"
    headers: Dict[str, str] = field(default_factory=lambda: {"Content-Type": "application/json"})
    timeout: int = 10
    include_results: bool = True


def _build_payload(checklist: Checklist, config: WebhookConfig) -> Dict[str, Any]:
    """Build the JSON payload for the webhook request."""
    payload: Dict[str, Any] = {
        "checklist": checklist.name,
        "passed": checklist.passed,
        "total": len(checklist.results),
        "failures": sum(1 for r in checklist.results if not r.passed),
    }
    if config.include_results:
        payload["results"] = [
            {
                "name": r.name,
                "passed": r.passed,
                "message": r.message,
            }
            for r in checklist.results
        ]
    return payload


def notify(checklist: Checklist, config: WebhookConfig) -> Optional[int]:
    """Send checklist result to a webhook endpoint.

    Returns the HTTP status code, or None if the request failed.
    """
    payload = _build_payload(checklist, config)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url=config.url,
        data=data,
        method=config.method,
        headers=config.headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=config.timeout) as resp:
            return resp.status
    except Exception:  # noqa: BLE001
        return None
