"""CLI entry-point for sending a checklist result to a webhook."""
from __future__ import annotations

import argparse
import sys

from deploygate.cli import load_checklist_from_file
from deploygate.webhook import WebhookConfig, notify


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="deploygate-webhook",
        description="Run a checklist and POST results to a webhook URL.",
    )
    parser.add_argument("checklist", help="Path to the Python checklist file.")
    parser.add_argument("url", help="Webhook URL to POST results to.")
    parser.add_argument(
        "--method",
        default="POST",
        choices=["POST", "PUT", "PATCH"],
        help="HTTP method (default: POST).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10).",
    )
    parser.add_argument(
        "--no-results",
        action="store_true",
        help="Omit per-check results from the payload.",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:  # pragma: no cover
    args = _parse_args(argv)
    checklist = load_checklist_from_file(args.checklist)
    checklist.run()

    config = WebhookConfig(
        url=args.url,
        method=args.method,
        timeout=args.timeout,
        include_results=not args.no_results,
    )
    status = notify(checklist, config)
    if status is None:
        print("webhook: request failed", file=sys.stderr)
        return 1
    print(f"webhook: HTTP {status}")
    return 0 if checklist.passed else 1


if __name__ == "__main__":
    sys.exit(main())
