"""CLI entry point for displaying checklist run metrics."""
from __future__ import annotations

import argparse
import sys

from deploygate.history import load_history
from deploygate.metrics import compute_metrics, format_metrics_table


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Display aggregate metrics for a checklist run history."
    )
    parser.add_argument(
        "history_file",
        help="Path to the JSON history file produced by deploygate.",
    )
    parser.add_argument(
        "--checklist",
        default=None,
        metavar="NAME",
        help="Filter entries by checklist name (default: first checklist found).",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:  # pragma: no cover
    args = _parse_args(argv)

    try:
        all_entries = load_history(args.history_file)
    except FileNotFoundError:
        print(f"Error: history file not found: {args.history_file}", file=sys.stderr)
        return 1

    if not all_entries:
        print("No history entries found.", file=sys.stderr)
        return 1

    if args.checklist:
        entries = [e for e in all_entries if e["name"] == args.checklist]
        if not entries:
            print(f"No entries for checklist '{args.checklist}'.", file=sys.stderr)
            return 1
    else:
        entries = all_entries

    metrics = compute_metrics(entries)
    if metrics is None:
        print("Could not compute metrics.", file=sys.stderr)
        return 1

    print(format_metrics_table(metrics))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
