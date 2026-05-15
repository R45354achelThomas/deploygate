"""CLI entry point for displaying trend analysis of checklist run history."""

import argparse
import sys
from pathlib import Path

from deploygate.history import load_history
from deploygate.trend import analyze_trend, TrendDirection


def _parse_args(argv=None):
    """Parse command-line arguments for the trend CLI."""
    parser = argparse.ArgumentParser(
        prog="deploygate-trend",
        description="Analyze pass-rate trends from deploygate run history.",
    )
    parser.add_argument(
        "--history-file",
        default="deploygate_history.json",
        help="Path to the history JSON file (default: deploygate_history.json).",
    )
    parser.add_argument(
        "--checklist",
        default=None,
        metavar="NAME",
        help="Filter analysis to a specific checklist name.",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=5,
        help="Number of recent runs to include in the trend window (default: 5).",
    )
    parser.add_argument(
        "--fail-on-decline",
        action="store_true",
        default=False,
        help="Exit with a non-zero status code when the trend is declining.",
    )
    return parser.parse_args(argv)


_DIRECTION_LABEL = {
    TrendDirection.IMPROVING: "\u2197 Improving",
    TrendDirection.DECLINING: "\u2198 Declining",
    TrendDirection.STABLE: "\u2192 Stable",
    TrendDirection.INSUFFICIENT_DATA: "\u2014 Insufficient data",
}


def main(argv=None):
    """Run the trend analysis CLI.

    Loads history from disk, optionally filters by checklist name, runs
    trend analysis, and prints a human-readable summary to stdout.

    Returns an exit code of 1 when --fail-on-decline is set and the
    trend direction is DECLINING; otherwise returns 0.
    """
    args = _parse_args(argv)

    history_path = Path(args.history_file)
    if not history_path.exists():
        print(f"History file not found: {history_path}", file=sys.stderr)
        sys.exit(1)

    entries = load_history(history_path)

    if args.checklist:
        entries = [e for e in entries if e.get("name") == args.checklist]
        if not entries:
            print(
                f"No history entries found for checklist: {args.checklist!r}",
                file=sys.stderr,
            )
            sys.exit(1)

    result = analyze_trend(entries, window=args.window)

    label = _DIRECTION_LABEL.get(result.direction, str(result.direction))
    print(f"Trend direction : {label}")
    print(f"Window size     : {args.window} runs")
    print(f"Entries analysed: {result.total_entries}")

    if result.pass_rates:
        formatted = ", ".join(f"{r:.0%}" for r in result.pass_rates)
        print(f"Recent pass rates: [{formatted}]")
    else:
        print("Recent pass rates: n/a")

    if args.fail_on_decline and result.direction == TrendDirection.DECLINING:
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
