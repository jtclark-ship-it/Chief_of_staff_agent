from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from app.services.window_resolver import resolve_preset, resolve_window
from app.utils.errors import InvalidTimeRange, MissingTimeWindow, RangeExceedsLimit

TZ = ZoneInfo("America/Denver")

# Fixed "now" for deterministic tests
FIXED_NOW = datetime(2025, 6, 11, 10, 30, 0, tzinfo=TZ)  # Wednesday


def _patch_now():
    return patch("app.services.window_resolver.now_in_tz", return_value=FIXED_NOW)


class TestResolvePreset:
    def test_today(self):
        with _patch_now():
            start, end = resolve_preset("today", TZ)
        assert start == datetime(2025, 6, 11, 0, 0, 0, tzinfo=TZ)
        assert end == datetime(2025, 6, 12, 0, 0, 0, tzinfo=TZ)

    def test_tomorrow(self):
        with _patch_now():
            start, end = resolve_preset("tomorrow", TZ)
        assert start == datetime(2025, 6, 12, 0, 0, 0, tzinfo=TZ)
        assert end == datetime(2025, 6, 13, 0, 0, 0, tzinfo=TZ)

    def test_next_7_days(self):
        with _patch_now():
            start, end = resolve_preset("next_7_days", TZ)
        assert start == FIXED_NOW
        assert end == FIXED_NOW + timedelta(days=7)

    def test_next_14_days(self):
        with _patch_now():
            start, end = resolve_preset("next_14_days", TZ)
        assert start == FIXED_NOW
        assert end == FIXED_NOW + timedelta(days=14)

    def test_this_week(self):
        with _patch_now():
            start, end = resolve_preset("this_week", TZ)
        # June 11 2025 is Wednesday, so Monday is June 9
        assert start == datetime(2025, 6, 9, 0, 0, 0, tzinfo=TZ)
        assert end == datetime(2025, 6, 16, 0, 0, 0, tzinfo=TZ)

    def test_next_week(self):
        with _patch_now():
            start, end = resolve_preset("next_week", TZ)
        assert start == datetime(2025, 6, 16, 0, 0, 0, tzinfo=TZ)
        assert end == datetime(2025, 6, 23, 0, 0, 0, tzinfo=TZ)

    def test_morning_brief_today(self):
        with _patch_now():
            start, end = resolve_preset("morning_brief_today", TZ)
        assert start == datetime(2025, 6, 11, 0, 0, 0, tzinfo=TZ)
        assert end == datetime(2025, 6, 12, 0, 0, 0, tzinfo=TZ)

    def test_unknown_preset(self):
        with _patch_now():
            with pytest.raises(InvalidTimeRange):
                resolve_preset("nonexistent", TZ)


class TestResolveWindow:
    def test_explicit_window(self):
        t_min = "2025-06-11T00:00:00-06:00"
        t_max = "2025-06-12T00:00:00-06:00"
        with _patch_now():
            window = resolve_window(time_min=t_min, time_max=t_max)
        assert window.resolved_from.explicit is True
        assert window.clamped is False

    def test_preset_window(self):
        with _patch_now():
            window = resolve_window(preset="today", timezone="America/Denver")
        assert window.resolved_from.preset == "today"
        assert window.clamped is False

    def test_missing_window(self):
        with pytest.raises(MissingTimeWindow):
            resolve_window()

    def test_invalid_range(self):
        with _patch_now():
            with pytest.raises(InvalidTimeRange):
                resolve_window(
                    time_min="2025-06-12T00:00:00-06:00",
                    time_max="2025-06-11T00:00:00-06:00",
                )

    def test_exceeds_limit_no_clamping(self):
        far_future_min = (FIXED_NOW + timedelta(days=60)).isoformat()
        far_future_max = (FIXED_NOW + timedelta(days=61)).isoformat()
        with _patch_now():
            with pytest.raises(RangeExceedsLimit):
                resolve_window(time_min=far_future_min, time_max=far_future_max)

    @patch("app.services.window_resolver.get_settings")
    def test_clamping_enabled(self, mock_settings):
        from app.config import Settings

        s = Settings()
        s.ALLOW_CLAMPING = True
        s.MAX_LOOKAHEAD_DAYS = 30
        s.MAX_LOOKBACK_DAYS = 30
        s.DEFAULT_TIMEZONE = "America/Denver"
        mock_settings.return_value = s

        far_past = (FIXED_NOW - timedelta(days=60)).isoformat()
        far_future = (FIXED_NOW + timedelta(days=60)).isoformat()
        with _patch_now():
            window = resolve_window(time_min=far_past, time_max=far_future)
        assert window.clamped is True
        assert window.clamp_reason is not None
