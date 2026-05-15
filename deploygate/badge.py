"""Generate SVG status badges for checklist results."""

from __future__ import annotations

from pathlib import Path

from deploygate.checklist import Checklist

_BADGE_TEMPLATE = """\
<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20">
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <rect rx="3" width="{total_width}" height="20" fill="#555"/>
  <rect rx="3" x="{label_width}" width="{value_width}" height="20" fill="{color}"/>
  <rect rx="3" width="{total_width}" height="20" fill="url(#s)"/>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="{label_cx}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_cx}" y="14">{label}</text>
    <text x="{value_cx}" y="15" fill="#010101" fill-opacity=".3">{value}</text>
    <text x="{value_cx}" y="14">{value}</text>
  </g>
</svg>
"""

_COLOR_PASSED = "#4c1"
_COLOR_FAILED = "#e05d44"
_CHAR_WIDTH = 7
_PADDING = 10


def _text_width(text: str) -> int:
    return len(text) * _CHAR_WIDTH + _PADDING


def build_badge(checklist: Checklist) -> str:
    """Return an SVG badge string reflecting the checklist pass/fail state."""
    results = checklist.run()
    passed = all(r.passed for r in results)

    label = "deploygate"
    value = "passing" if passed else "failing"
    color = _COLOR_PASSED if passed else _COLOR_FAILED

    label_width = _text_width(label)
    value_width = _text_width(value)
    total_width = label_width + value_width

    return _BADGE_TEMPLATE.format(
        total_width=total_width,
        label_width=label_width,
        value_width=value_width,
        label_cx=label_width // 2,
        value_cx=label_width + value_width // 2,
        color=color,
        label=label,
        value=value,
    ).strip()


def write_badge(checklist: Checklist, path: str | Path) -> None:
    """Write the SVG badge for *checklist* to *path*."""
    svg = build_badge(checklist)
    Path(path).write_text(svg, encoding="utf-8")
