"""Tests for deploygate.badge."""

from __future__ import annotations

import pytest

from deploygate.checklist import CheckItem, Checklist
from deploygate.badge import build_badge, write_badge


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def passing_checklist() -> Checklist:
    return Checklist(
        name="Deploy",
        items=[
            CheckItem(name="tests pass", check=lambda: None),
            CheckItem(name="lint clean", check=lambda: None),
        ],
    )


@pytest.fixture()
def failing_checklist() -> Checklist:
    def _fail() -> None:
        raise RuntimeError("boom")

    return Checklist(
        name="Deploy",
        items=[
            CheckItem(name="tests pass", check=lambda: None),
            CheckItem(name="lint clean", check=_fail),
        ],
    )


# ---------------------------------------------------------------------------
# build_badge
# ---------------------------------------------------------------------------


def test_badge_is_string(passing_checklist: Checklist) -> None:
    svg = build_badge(passing_checklist)
    assert isinstance(svg, str)


def test_badge_contains_svg_tag(passing_checklist: Checklist) -> None:
    svg = build_badge(passing_checklist)
    assert "<svg" in svg
    assert "</svg>" in svg


def test_passing_badge_shows_passing(passing_checklist: Checklist) -> None:
    svg = build_badge(passing_checklist)
    assert "passing" in svg


def test_passing_badge_uses_green(passing_checklist: Checklist) -> None:
    svg = build_badge(passing_checklist)
    assert "#4c1" in svg


def test_failing_badge_shows_failing(failing_checklist: Checklist) -> None:
    svg = build_badge(failing_checklist)
    assert "failing" in svg


def test_failing_badge_uses_red(failing_checklist: Checklist) -> None:
    svg = build_badge(failing_checklist)
    assert "#e05d44" in svg


def test_badge_contains_label(passing_checklist: Checklist) -> None:
    svg = build_badge(passing_checklist)
    assert "deploygate" in svg


def test_badge_svg_is_not_empty(passing_checklist: Checklist) -> None:
    """Ensure build_badge never returns an empty or whitespace-only string."""
    svg = build_badge(passing_checklist)
    assert svg.strip() != ""


# ---------------------------------------------------------------------------
# write_badge
# ---------------------------------------------------------------------------


def test_write_badge_creates_file(tmp_path, passing_checklist: Checklist) -> None:
    out = tmp_path / "badge.svg"
    write_badge(passing_checklist, out)
    assert out.exists()


def test_write_badge_file_content(tmp_path, failing_checklist: Checklist) -> None:
    out = tmp_path / "badge.svg"
    write_badge(failing_checklist, out)
    content = out.read_text(encoding="utf-8")
    assert "failing" in content


def test_write_badge_file_matches_build_badge(
    tmp_path, passing_checklist: Checklist
) -> None:
    """Content written to disk should match what build_badge returns directly."""
    out = tmp_path / "badge.svg"
    expected = build_badge(passing_checklist)
    write_badge(passing_checklist, out)
    assert out.read_text(encoding="utf-8") == expected
