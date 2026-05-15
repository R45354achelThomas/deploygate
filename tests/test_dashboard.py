"""Tests for deploygate.dashboard."""
from __future__ import annotations

import pytest
from pathlib import Path

from deploygate.dashboard import build_html, write_dashboard, _entry_to_row


SAMPLE_HISTORY = [
    {
        "timestamp": "2024-05-01T12:00:00Z",
        "name": "pre-deploy",
        "passed": True,
        "passed_count": 3,
        "failed_count": 0,
        "total_count": 3,
    },
    {
        "timestamp": "2024-05-02T08:30:00Z",
        "name": "pre-deploy",
        "passed": False,
        "passed_count": 2,
        "failed_count": 1,
        "total_count": 3,
    },
]


def test_build_html_returns_string():
    html = build_html(SAMPLE_HISTORY)
    assert isinstance(html, str)


def test_build_html_contains_doctype():
    html = build_html(SAMPLE_HISTORY)
    assert "<!DOCTYPE html>" in html


def test_build_html_contains_checklist_name():
    html = build_html(SAMPLE_HISTORY)
    assert "pre-deploy" in html


def test_build_html_contains_timestamps():
    html = build_html(SAMPLE_HISTORY)
    assert "2024-05-01T12:00:00Z" in html
    assert "2024-05-02T08:30:00Z" in html


def test_build_html_pass_css_class():
    html = build_html(SAMPLE_HISTORY)
    assert 'class="pass"' in html


def test_build_html_fail_css_class():
    html = build_html(SAMPLE_HISTORY)
    assert 'class="fail"' in html


def test_build_html_empty_history():
    html = build_html([])
    assert "<tbody>" in html
    # No data rows should appear
    assert "<tr><td>" not in html


def test_entry_to_row_pass():
    row = _entry_to_row(SAMPLE_HISTORY[0])
    assert "PASS" in row
    assert 'class="pass"' in row


def test_entry_to_row_fail():
    row = _entry_to_row(SAMPLE_HISTORY[1])
    assert "FAIL" in row
    assert 'class="fail"' in row


def test_write_dashboard_creates_file(tmp_path: Path):
    output = tmp_path / "dashboard.html"
    result = write_dashboard(SAMPLE_HISTORY, output)
    assert result == output.resolve()
    assert output.exists()


def test_write_dashboard_file_content(tmp_path: Path):
    output = tmp_path / "dashboard.html"
    write_dashboard(SAMPLE_HISTORY, output)
    content = output.read_text(encoding="utf-8")
    assert "pre-deploy" in content
    assert "DeployGate" in content
