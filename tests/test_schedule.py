"""Tests for deploygate.schedule."""

from datetime import datetime, time

import pytest

from deploygate.schedule import DeployWindow, ScheduleConfig, is_deploy_allowed


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _monday_noon() -> datetime:
    """Return a fixed Monday 12:00 UTC datetime."""
    return datetime(2024, 1, 8, 12, 0, 0)  # Monday


def _saturday_noon() -> datetime:
    return datetime(2024, 1, 13, 12, 0, 0)  # Saturday


@pytest.fixture
def weekday_window() -> DeployWindow:
    return DeployWindow(
        name="Weekdays",
        days=[0, 1, 2, 3, 4],
        start=time(9, 0),
        end=time(17, 0),
    )


# ---------------------------------------------------------------------------
# DeployWindow.is_open
# ---------------------------------------------------------------------------

def test_window_open_on_valid_day_and_time(weekday_window):
    assert weekday_window.is_open(_monday_noon()) is True


def test_window_closed_on_weekend(weekday_window):
    assert weekday_window.is_open(_saturday_noon()) is False


def test_window_closed_before_start(weekday_window):
    early = datetime(2024, 1, 8, 8, 0, 0)  # Monday 08:00
    assert weekday_window.is_open(early) is False


def test_window_closed_after_end(weekday_window):
    late = datetime(2024, 1, 8, 18, 0, 0)  # Monday 18:00
    assert weekday_window.is_open(late) is False


def test_window_open_at_exact_start(weekday_window):
    exact = datetime(2024, 1, 8, 9, 0, 0)
    assert weekday_window.is_open(exact) is True


def test_window_open_at_exact_end(weekday_window):
    exact = datetime(2024, 1, 8, 17, 0, 0)
    assert weekday_window.is_open(exact) is True


# ---------------------------------------------------------------------------
# ScheduleConfig
# ---------------------------------------------------------------------------

def test_any_open_returns_true_when_window_open(weekday_window):
    config = ScheduleConfig(windows=[weekday_window])
    assert config.any_open(_monday_noon()) is True


def test_any_open_returns_false_when_all_closed(weekday_window):
    config = ScheduleConfig(windows=[weekday_window])
    assert config.any_open(_saturday_noon()) is False


def test_active_window_returns_matching_window(weekday_window):
    config = ScheduleConfig(windows=[weekday_window])
    result = config.active_window(_monday_noon())
    assert result is weekday_window


def test_active_window_returns_none_when_closed(weekday_window):
    config = ScheduleConfig(windows=[weekday_window])
    assert config.active_window(_saturday_noon()) is None


# ---------------------------------------------------------------------------
# is_deploy_allowed
# ---------------------------------------------------------------------------

def test_deploy_allowed_inside_window(weekday_window):
    config = ScheduleConfig(windows=[weekday_window])
    assert is_deploy_allowed(config, _monday_noon()) is True


def test_deploy_blocked_outside_window(weekday_window):
    config = ScheduleConfig(windows=[weekday_window])
    assert is_deploy_allowed(config, _saturday_noon()) is False


def test_deploy_allowed_when_blocking_disabled(weekday_window):
    config = ScheduleConfig(windows=[weekday_window], block_outside_windows=False)
    assert is_deploy_allowed(config, _saturday_noon()) is True


def test_deploy_allowed_with_no_windows_defined():
    config = ScheduleConfig(windows=[])
    assert is_deploy_allowed(config, _saturday_noon()) is True
