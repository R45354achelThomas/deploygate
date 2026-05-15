"""CLI sub-command: generate an HTML dashboard from saved history."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from deploygate.history import load_history
from deploygate.dashboard import write_dashboard


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="deploygate-dashboard",
        description="Generate an HTML dashboard from DeployGate run history.",
    )
    parser.add_argument(
        "--history-file",
        default="deploygate_history.json",
        metavar="FILE",
        help="Path to the JSON history file (default: deploygate_history.json).",
    )
    parser.add_argument(
        "--output",
        default="dashboard.html",
        metavar="FILE",
        help="Output HTML file path (default: dashboard.html).",
    )
    parser.add_argument(
        "--open",
        dest="open_browser",
        action="store_true",
        help="Open the generated dashboard in the default browser.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry-point for the dashboard CLI command. Returns exit code."""
    args = _parse_args(argv)

    history_path = Path(args.history_file)
    if not history_path.exists():
        print(f"[deploygate] History file not found: {history_path}", file=sys.stderr)
        return 1

    history = load_history(history_path)
    if not history:
        print("[deploygate] History file is empty — nothing to display.", file=sys.stderr)
        return 1

    output_path = write_dashboard(history, args.output)
    print(f"[deploygate] Dashboard written to {output_path}")

    if args.open_browser:
        import webbrowser
        webbrowser.open(output_path.as_uri())

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
