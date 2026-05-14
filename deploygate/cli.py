"""CLI entry point for running deploygate checklists."""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

from deploygate.checklist import Checklist


DEFAULT_CONFIG = "deploygate.py"


def load_checklist_from_file(path: str) -> Checklist:
    """Dynamically load a Checklist instance from a config file."""
    config_path = Path(path)
    if not config_path.exists():
        print(f"[deploygate] Config file not found: {path}", file=sys.stderr)
        sys.exit(1)

    spec = importlib.util.spec_from_file_location("deploygate_config", config_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "checklist"):
        print("[deploygate] Config file must define a 'checklist' variable.", file=sys.stderr)
        sys.exit(1)

    return module.checklist


def print_summary(summary: dict, use_json: bool) -> None:
    if use_json:
        print(json.dumps(summary, indent=2))
        return

    print(f"\n=== Checklist: {summary['checklist']} ===")
    for item in summary["results"]:
        icon = {"passed": "✅", "failed": "❌", "skipped": "⏭️", "pending": "⏳", "running": "🔄"}.get(
            item["status"], "?"
        )
        line = f"  {icon} [{item['status'].upper():8}] {item['name']} ({item['duration_ms']}ms)"
        if item["message"]:
            line += f" — {item['message']}"
        print(line)

    print(
        f"\nTotal: {summary['total']}  "
        f"Passed: {summary['passed']}  "
        f"Failed: {summary['failed']}  "
        f"Skipped: {summary['skipped']}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="deploygate",
        description="Lightweight pre-deploy checklist runner",
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG,
        help=f"Path to checklist config file (default: {DEFAULT_CONFIG})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    args = parser.parse_args()

    checklist = load_checklist_from_file(args.config)
    passed = checklist.run()
    print_summary(checklist.summary, use_json=args.json)

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
