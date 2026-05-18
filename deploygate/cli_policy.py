"""CLI entry-point: deploygate-policy — evaluate a deployment policy."""
from __future__ import annotations

import argparse
import json
import sys

from deploygate.cli import load_checklist_from_file
from deploygate.policy import PolicyRule, evaluate_policy


def _parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="deploygate-policy",
        description="Evaluate a deployment policy against a checklist.",
    )
    p.add_argument("checklist", help="Path to checklist Python file")
    p.add_argument("--rule-name", default="default", help="Policy rule name")
    p.add_argument(
        "--min-pass-rate",
        type=float,
        default=1.0,
        metavar="RATE",
        help="Minimum pass rate (0.0-1.0, default 1.0)",
    )
    p.add_argument(
        "--required-checks",
        nargs="*",
        default=[],
        metavar="CHECK",
        help="Check names that must pass",
    )
    p.add_argument(
        "--no-block-on-error",
        action="store_true",
        help="Do not block when checks raise errors",
    )
    p.add_argument("--json", action="store_true", help="Output result as JSON")
    return p.parse_args(argv)


def main(argv=None) -> None:  # pragma: no cover
    args = _parse_args(argv)
    checklist = load_checklist_from_file(args.checklist)

    rule = PolicyRule(
        name=args.rule_name,
        min_pass_rate=args.min_pass_rate,
        required_checks=args.required_checks,
        block_on_error=not args.no_block_on_error,
    )

    result = evaluate_policy(checklist, rule)

    if args.json:
        print(json.dumps({
            "rule": rule.name,
            "allowed": result.allowed,
            "reasons": result.reasons,
        }))
    else:
        print(str(result))

    sys.exit(0 if result.allowed else 1)


if __name__ == "__main__":  # pragma: no cover
    main()
