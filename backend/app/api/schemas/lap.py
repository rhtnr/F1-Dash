"""Lap API schemas."""

from typing import Any

from pydantic import BaseModel

from app.domain.models import Lap
from app.domain.models.lap import timedelta_to_lap_string


class LapResponse(BaseModel):
    """Response schema for a lap."""

    id: str
    session_id: str
    driver_id: str
    lap_number: int

    # Timing (as strings for display)
    lap_time: str | None
    lap_time_seconds: float | None
    sector_1_time: str | None
    sector_2_time: str | None
    sector_3_time: str | None

    # Tire data
    compound: str
    compound_color: str
    tyre_life: int
    stint: int
    is_fresh_tyre: bool

    # Speed data
    speed_i1: float | None
    speed_i2: float | None
    speed_fl: float | None
    speed_st: float | None

    # Status
    position: int | None
    track_status: str
    is_personal_best: bool
    is_accurate: bool
    deleted: bool
    deleted_reason: str | None

    # Pit info
    is_pit_in_lap: bool
    is_pit_out_lap: bool
    is_valid_for_analysis: bool

    @classmethod
    def from_domain(cls, lap: Lap) -> "LapResponse":
        """Create response from domain model."""
        return cls(
            id=lap.id,
            session_id=lap.session_id,
            driver_id=lap.driver_id,
            lap_number=lap.lap_number,
            lap_time=timedelta_to_lap_string(lap.lap_time),
            lap_time_seconds=lap.lap_time_seconds,
            sector_1_time=timedelta_to_lap_string(lap.sector_1_time),
            sector_2_time=timedelta_to_lap_string(lap.sector_2_time),
            sector_3_time=timedelta_to_lap_string(lap.sector_3_time),
            compound=lap.compound.value,
            compound_color=lap.compound.color,
            tyre_life=lap.tyre_life,
            stint=lap.stint,
            is_fresh_tyre=lap.is_fresh_tyre,
            speed_i1=lap.speed_i1,
            speed_i2=lap.speed_i2,
            speed_fl=lap.speed_fl,
            speed_st=lap.speed_st,
            position=lap.position,
            track_status=lap.track_status.value,
            is_personal_best=lap.is_personal_best,
            is_accurate=lap.is_accurate,
            deleted=lap.deleted,
            deleted_reason=lap.deleted_reason,
            is_pit_in_lap=lap.is_pit_in_lap,
            is_pit_out_lap=lap.is_pit_out_lap,
            is_valid_for_analysis=lap.is_valid_for_analysis,
        )


class LapListResponse(BaseModel):
    """Response schema for list of laps."""

    session_id: str
    count: int
    laps: list[LapResponse]


class LapComparisonResponse(BaseModel):
    """Response schema for driver comparison."""

    session_id: str
    comparison: dict[str, dict | None]


class CompoundPerformanceResponse(BaseModel):
    """Response schema for compound performance."""

    session_id: str
    compounds: dict[str, dict[str, Any]]
