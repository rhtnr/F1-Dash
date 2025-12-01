"""Tests for domain models."""

from datetime import datetime, timedelta

import pytest

from app.domain.enums import SessionType, TireCompound, TrackStatus
from app.domain.models import Driver, Lap, Session, TireStint
from app.domain.models.lap import timedelta_to_lap_string


class TestTireCompound:
    """Tests for TireCompound enum."""

    def test_from_fastf1_valid(self):
        assert TireCompound.from_fastf1("SOFT") == TireCompound.SOFT
        assert TireCompound.from_fastf1("soft") == TireCompound.SOFT
        assert TireCompound.from_fastf1("MEDIUM") == TireCompound.MEDIUM

    def test_from_fastf1_invalid(self):
        assert TireCompound.from_fastf1(None) == TireCompound.UNKNOWN
        assert TireCompound.from_fastf1("INVALID") == TireCompound.UNKNOWN

    def test_color(self):
        assert TireCompound.SOFT.color == "#FF3333"
        assert TireCompound.MEDIUM.color == "#FCD500"
        assert TireCompound.HARD.color == "#EBEBEB"

    def test_short_name(self):
        assert TireCompound.SOFT.short_name == "S"
        assert TireCompound.MEDIUM.short_name == "M"
        assert TireCompound.UNKNOWN.short_name == "?"


class TestSessionType:
    """Tests for SessionType enum."""

    def test_from_fastf1(self):
        assert SessionType.from_fastf1("Race") == SessionType.RACE
        assert SessionType.from_fastf1("Qualifying") == SessionType.QUALIFYING
        assert SessionType.from_fastf1("Practice 1") == SessionType.PRACTICE_1
        assert SessionType.from_fastf1("FP1") == SessionType.PRACTICE_1

    def test_display_name(self):
        assert SessionType.RACE.display_name == "Race"
        assert SessionType.QUALIFYING.display_name == "Qualifying"

    def test_is_race(self):
        assert SessionType.RACE.is_race is True
        assert SessionType.SPRINT.is_race is True
        assert SessionType.QUALIFYING.is_race is False


class TestTrackStatus:
    """Tests for TrackStatus enum."""

    def test_from_fastf1(self):
        assert TrackStatus.from_fastf1("1") == TrackStatus.GREEN
        assert TrackStatus.from_fastf1("4") == TrackStatus.SC
        assert TrackStatus.from_fastf1("5") == TrackStatus.RED
        assert TrackStatus.from_fastf1(None) == TrackStatus.GREEN

    def test_affects_lap_time(self):
        assert TrackStatus.GREEN.affects_lap_time is False
        assert TrackStatus.SC.affects_lap_time is True
        assert TrackStatus.RED.affects_lap_time is True


class TestSession:
    """Tests for Session model."""

    def test_create_id(self):
        session_id = Session.create_id(2024, 1, SessionType.RACE)
        assert session_id == "2024_01_R"

    def test_display_name(self, sample_session):
        assert "2024" in sample_session.display_name
        assert "Bahrain" in sample_session.display_name
        assert "Race" in sample_session.display_name

    def test_immutable(self, sample_session):
        with pytest.raises(Exception):
            sample_session.year = 2025


class TestLap:
    """Tests for Lap model."""

    def test_create_id(self):
        lap_id = Lap.create_id("2024_01_R", "VER", 10)
        assert lap_id == "2024_01_R_VER_010"

    def test_lap_time_seconds(self):
        lap = Lap(
            id="test",
            session_id="2024_01_R",
            driver_id="VER",
            lap_number=1,
            lap_time=timedelta(minutes=1, seconds=32, milliseconds=500),
            compound=TireCompound.SOFT,
        )
        assert lap.lap_time_seconds == pytest.approx(92.5, rel=0.001)

    def test_lap_time_seconds_none(self):
        lap = Lap(
            id="test",
            session_id="2024_01_R",
            driver_id="VER",
            lap_number=1,
            lap_time=None,
            compound=TireCompound.SOFT,
        )
        assert lap.lap_time_seconds is None

    def test_is_valid_for_analysis(self, sample_laps):
        # Regular lap should be valid
        assert sample_laps[0].is_valid_for_analysis is True

    def test_is_valid_for_analysis_pit_lap(self):
        lap = Lap(
            id="test",
            session_id="2024_01_R",
            driver_id="VER",
            lap_number=1,
            lap_time=timedelta(minutes=1, seconds=32),
            compound=TireCompound.SOFT,
            is_pit_in_lap=True,
        )
        assert lap.is_valid_for_analysis is False


class TestTimedeltaFormatting:
    """Tests for lap time formatting."""

    def test_format_normal_time(self):
        td = timedelta(minutes=1, seconds=32, milliseconds=456)
        assert timedelta_to_lap_string(td) == "1:32.456"

    def test_format_none(self):
        assert timedelta_to_lap_string(None) == "--:--.---"

    def test_format_sub_minute(self):
        td = timedelta(seconds=45, milliseconds=123)
        assert timedelta_to_lap_string(td) == "0:45.123"


class TestTireStint:
    """Tests for TireStint model."""

    def test_total_laps(self, sample_stint):
        assert sample_stint.total_laps == 20

    def test_avg_lap_time_seconds(self, sample_stint):
        assert sample_stint.avg_lap_time_seconds == pytest.approx(93.5, rel=0.001)

    def test_create_id(self):
        stint_id = TireStint.create_id("2024_01_R", "VER", 1)
        assert stint_id == "2024_01_R_VER_stint_1"


class TestDriver:
    """Tests for Driver model."""

    def test_display_name(self, sample_driver):
        assert sample_driver.display_name == "M. Verstappen"

    def test_create_id(self):
        driver_id = Driver.create_id("ver")
        assert driver_id == "VER"
