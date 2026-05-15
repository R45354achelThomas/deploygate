"""Simple HTML dashboard generator for checklist run history."""
from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>DeployGate Dashboard</title>
  <style>
    body {{ font-family: sans-serif; margin: 2rem; background: #f5f5f5; }}
    h1 {{ color: #333; }}
    table {{ border-collapse: collapse; width: 100%; background: #fff; }}
    th, td {{ padding: 0.6rem 1rem; border: 1px solid #ddd; text-align: left; }}
    th {{ background: #4a90d9; color: #fff; }}
    tr:nth-child(even) {{ background: #f9f9f9; }}
    .pass {{ color: #2e7d32; font-weight: bold; }}
    .fail {{ color: #c62828; font-weight: bold; }}
  </style>
</head>
<body>
  <h1>DeployGate — Run History</h1>
  <table>
    <thead>
      <tr>
        <th>Timestamp (UTC)</th>
        <th>Checklist</th>
        <th>Result</th>
        <th>Passed</th>
        <th>Failed</th>
        <th>Total</th>
      </tr>
    </thead>
    <tbody>
{rows}
    </tbody>
  </table>
</body>
</html>
"""

ROW_TEMPLATE = (
    "      <tr>"
    "<td>{timestamp}</td>"
    "<td>{name}</td>"
    "<td class=\"{css}\">{result}</td>"
    "<td>{passed}</td>"
    "<td>{failed}</td>"
    "<td>{total}</td>"
    "</tr>"
)


def _entry_to_row(entry: Dict[str, Any]) -> str:
    passed: bool = entry.get("passed", False)
    return ROW_TEMPLATE.format(
        timestamp=entry.get("timestamp", ""),
        name=entry.get("name", ""),
        css="pass" if passed else "fail",
        result="PASS" if passed else "FAIL",
        passed=entry.get("passed_count", 0),
        failed=entry.get("failed_count", 0),
        total=entry.get("total_count", 0),
    )


def build_html(history: List[Dict[str, Any]]) -> str:
    """Return a full HTML page for *history* entries (newest first)."""
    rows = "\n".join(_entry_to_row(e) for e in reversed(history))
    return HTML_TEMPLATE.format(rows=rows)


def write_dashboard(history: List[Dict[str, Any]], output_path: str | Path = "dashboard.html") -> Path:
    """Write the HTML dashboard to *output_path* and return the resolved path."""
    path = Path(output_path)
    path.write_text(build_html(history), encoding="utf-8")
    return path.resolve()
