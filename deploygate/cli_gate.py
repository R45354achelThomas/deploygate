"""CLI entry point for the deployment gate."""
from __future__ import annotations

import argparse
import sys

from deploygate.cli import load_checklist_from_file
from deploygate.gate import GateConfig, evaluate


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate a deployment gate against a checklist."
    )
    parser.add_argument("checklist", help="Path to checklist Python file")
    parser.add_argument(
        "--no-require-all",
        dest="require_all_passed",
        action="store_false",
        default=True,
        help="Allow deploy even when some checks fail",
    )
    parser.add_argument(
        "--enforce-schedule",
        action="store_true",
        default=False,
        help="Block deploy outside of configured schedule windows",
    )
    parser.add_argument(
        "--min-approvals",
        type=int,
        default=0,
        metavar="N",
        help="Minimum number of approvals required",
    )
    parser.add_argument(
        "--approvers",
        nargs="*",
        default=[],
        metavar="USER",
        help="List of users who have approved",
    )
    parser.add_argument(
        "--allowed-approvers",
        nargs="*",
        default=[],
        metavar="USER",
        help="Restrict valid approvers to this list",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:  # pragma: no cover
    args = _parse_args(argv)
    checklist = load_checklist_from_file(args.checklist)
    checklist.run()

    config = GateConfig(
        require_all_passed=args.require_all_passed,
        enforce_schedule=args.enforce_schedule,
        min_approvals=args.min_approvals,
        allowed_approvers=args.allowed_approvers,
    )

    result = evaluate(checklist, config, approvers=args.approvers)
    print(result)
    return 0 if result.allowed else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
