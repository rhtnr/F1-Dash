"""Strategy API schemas."""

from typing import Any

from pydantic import BaseModel

from app.domain.models import TireStint


class StintResponse(BaseModel):
    """Response schema for a tire stint."""

    id: str
    session_id: str
    driver_id: str
    stint_number: int
    compound: str
    compound_color: str
    is_fresh: bool
    start_lap: int
    end_lap: int
    total_laps: int
    avg_lap_time_seconds: float | None
    degradation_rate: float | None

    @classmethod
    def from_domain(cls, stint: TireStint) -> "StintResponse":
        """Create response from domain model."""
        return cls(
            id=stint.id,
            session_id=stint.session_id,
            driver_id=stint.driver_id,
            stint_number=stint.stint_number,
            compound=stint.compound.value,
            compound_color=stint.compound.color,
            is_fresh=stint.is_fresh,
            start_lap=stint.start_lap,
            end_lap=stint.end_lap,
            total_laps=stint.total_laps,
            avg_lap_time_seconds=stint.avg_lap_time_seconds,
            degradation_rate=stint.degradation_rate,
        )


class StintListResponse(BaseModel):
    """Response schema for list of stints."""

    session_id: str
    count: int
    stints: list[StintResponse]


class StrategySummaryResponse(BaseModel):
    """Response schema for strategy summary."""

    session_id: str
    strategies: list[dict[str, Any]]


class DegradationResponse(BaseModel):
    """Response schema for stint degradation analysis."""

    session_id: str
    driver_id: str
    stint_number: int
    compound: str | None
    total_laps: int
    degradation_per_lap: float
    laps: list[dict[str, Any]]
