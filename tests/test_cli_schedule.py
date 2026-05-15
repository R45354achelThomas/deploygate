"""Tests for deploygate.cli_schedule."""

import json
import textwrap
from pathlib import Path

import pytest

from deploygate.cli_schedule import _load_windows_from_file, _parse_args, _parse_time
from deploygate.schedule import ScheduleConfig, is_deploy_allowed
from datetime import datetime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def window_config_file(tmp_path: Path) -> Path:
    data = {
        "windows": [
            {
                "name": "Business hours",
                "days": [0, 1, 2, 3, 4],
                "start": "09:00",
                "end": "17:00",
                "timezone": "UTC",
            }
        ]
    }
    config_file = tmp_path / "windows.json"
    config_file.write_text(json.dumps(data))
    return config_file


# ---------------------------------------------------------------------------
# _parse_time
# ---------------------------------------------------------------------------

def test_parse_time_valid():
    t = _parse_time("09:30")
    assert t.hour == 9
    assert t.minute == 30


def test_parse_time_invalid_raises():
    import argparse
    with pytest.raises(argparse.ArgumentTypeError):
        _parse_time("not-a-time")


# ---------------------------------------------------------------------------
# _load_windows_from_file
# ---------------------------------------------------------------------------

def test_load_windows_returns_list(window_config_file):
    windows = _load_windows_from_file(str(window_config_file))
    assert len(windows) == 1


def test_load_windows_name(window_config_file):
    windows = _load_windows_from_file(str(window_config_file))
    assert windows[0].name == "Business hours"


def test_load_windows_days(window_config_file):
    windows = _load_windows_from_file(str(window_config_file))
    assert windows[0].days == [0, 1, 2, 3, 4]


def test_load_windows_start_end(window_config_file):
    windows = _load_windows_from_file(str(window_config_file))
    from datetime import time
    assert windows[0].start == time(9, 0)
    assert windows[0].end == time(17, 0)


# ---------------------------------------------------------------------------
# _parse_args
# ---------------------------------------------------------------------------

def test_parse_args_config(window_config_file):
    args = _parse_args(["--config", str(window_config_file)])
    assert args.config == str(window_config_file)


def test_parse_args_allow_outside_default(window_config_file):
    args = _parse_args(["--config", str(window_config_file)])
    assert args.allow_outside is False


def test_parse_args_allow_outside_flag(window_config_file):
    args = _parse_args(["--config", str(window_config_file), "--allow-outside"])
    assert args.allow_outside is True


# ---------------------------------------------------------------------------
# Integration: load + schedule check
# ---------------------------------------------------------------------------

def test_integration_blocked_on_weekend(window_config_file):
    windows = _load_windows_from_file(str(window_config_file))
    config = ScheduleConfig(windows=windows, block_outside_windows=True)
    saturday_noon = datetime(2024, 1, 13, 12, 0, 0)
    assert is_deploy_allowed(config, saturday_noon) is False


def test_integration_allowed_on_weekday(window_config_file):
    windows = _load_windows_from_file(str(window_config_file))
    config = ScheduleConfig(windows=windows, block_outside_windows=True)
    monday_noon = datetime(2024, 1, 8, 12, 0, 0)
    assert is_deploy_allowed(config, monday_noon) is True
