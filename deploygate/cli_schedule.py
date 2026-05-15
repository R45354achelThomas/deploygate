"""CLI entry-point: check whether the current time is inside a deploy window."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, time
from typing import List

from deploygate.schedule import DeployWindow, ScheduleConfig, is_deploy_allowed


def _parse_time(value: str) -> time:
    try:
        h, m = value.split(":")
        return time(int(h), int(m))
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError(f"Invalid time '{value}' (expected HH:MM)") from exc


def _load_windows_from_file(path: str) -> List[DeployWindow]:
    with open(path) as fh:
        data = json.load(fh)
    windows = []
    for entry in data.get("windows", []):
        windows.append(
            DeployWindow(
                name=entry["name"],
                days=entry["days"],
                start=_parse_time(entry["start"]),
                end=_parse_time(entry["end"]),
                timezone=entry.get("timezone", "UTC"),
            )
        )
    return windows


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check if the current time is inside a permitted deploy window."
    )
    parser.add_argument(
        "--config",
        metavar="FILE",
        required=True,
        help="JSON file containing window definitions.",
    )
    parser.add_argument(
        "--allow-outside",
        action="store_true",
        default=False,
        help="Allow deploys even outside defined windows.",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:  # pragma: no cover
    args = _parse_args(argv)
    windows = _load_windows_from_file(args.config)
    config = ScheduleConfig(
        windows=windows,
        block_outside_windows=not args.allow_outside,
    )
    now = datetime.utcnow()
    allowed = is_deploy_allowed(config, now)
    active = config.active_window(now)

    if allowed:
        label = active.name if active else "(unrestricted)"
        print(f"✅ Deploy allowed — window: {label}")
        return 0
    else:
        print("🚫 Deploy blocked — outside permitted windows.")
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
