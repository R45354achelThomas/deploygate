"""CLI entry-point for the approval gate."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from deploygate.approval import approve, is_approved, latest_approval, load_approvals


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="deploygate-approval",
        description="Manage deploy approvals.",
    )
    parser.add_argument(
        "--file",
        default=".deploygate/approvals.json",
        help="Path to approval store (default: .deploygate/approvals.json)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # approve sub-command
    ap = sub.add_parser("approve", help="Record an approval.")
    ap.add_argument("checklist", help="Name of the checklist to approve.")
    ap.add_argument("--by", required=True, dest="approved_by", help="Approver identity.")
    ap.add_argument("--note", default="", help="Optional note.")

    # status sub-command
    st = sub.add_parser("status", help="Check approval status.")
    st.add_argument("checklist", help="Name of the checklist to query.")

    # list sub-command
    sub.add_parser("list", help="List all recorded approvals.")

    return parser.parse_args(argv)


def main(argv=None) -> int:  # noqa: C901
    args = _parse_args(argv)
    path = Path(args.file)

    if args.command == "approve":
        entry = approve(path, checklist=args.checklist, approved_by=args.approved_by, note=args.note)
        print(f"✅  Approved '{entry.checklist}' by {entry.approved_by} at {entry.approved_at}")
        if entry.note:
            print(f"   Note: {entry.note}")
        return 0

    if args.command == "status":
        latest = latest_approval(path, args.checklist)
        if latest is None:
            print(f"❌  No approval found for '{args.checklist}'.")
            return 1
        print(f"✅  '{args.checklist}' approved by {latest.approved_by} at {latest.approved_at}")
        return 0

    if args.command == "list":
        entries = load_approvals(path)
        if not entries:
            print("No approvals recorded.")
            return 0
        for e in entries:
            note_part = f" — {e.note}" if e.note else ""
            print(f"  {e.approved_at}  {e.checklist}  (by {e.approved_by}){note_part}")
        return 0

    return 1  # unreachable but satisfies type checkers


if __name__ == "__main__":
    sys.exit(main())
