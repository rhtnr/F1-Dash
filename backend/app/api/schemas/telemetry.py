"""Telemetry API schemas."""

from typing import Any

from pydantic import BaseModel

from app.domain.models import TelemetryFrame


class TelemetryPointResponse(BaseModel):
    """Response schema for a telemetry point."""

    time_ms: int
    distance: float
    speed: float
    rpm: int
    gear: int
    throttle: float
    brake: bool
    drs: int
    x: float | None
    y: float | None
    z: float | None


class TelemetryResponse(BaseModel):
    """Response schema for telemetry data."""

    session_id: str
    driver_id: str
    lap_number: int
    lap_time_ms: int | None
    point_count: int
    max_speed: float
    track_length: float
    points: list[TelemetryPointResponse]

    @classmethod
    def from_domain(cls, frame: TelemetryFrame) -> "TelemetryResponse":
        """Create response from domain model."""
        return cls(
            session_id=frame.session_id,
            driver_id=frame.driver_id,
            lap_number=frame.lap_number,
            lap_time_ms=frame.lap_time_ms,
            point_count=frame.point_count,
            max_speed=frame.max_speed,
            track_length=frame.track_length,
            points=[
                TelemetryPointResponse(
                    time_ms=p.time_ms,
                    distance=p.distance,
                    speed=p.speed,
                    rpm=p.rpm,
                    gear=p.gear,
                    throttle=p.throttle,
                    brake=p.brake,
                    drs=p.drs,
                    x=p.x,
                    y=p.y,
                    z=p.z,
                )
                for p in frame.points
            ],
        )


class SpeedTraceResponse(BaseModel):
    """Response schema for speed trace data."""

    session_id: str
    driver_id: str
    lap_number: int
    points: list[dict[str, Any]]


class TelemetryComparisonResponse(BaseModel):
    """Response schema for telemetry comparison."""

    session_id: str
    laps: list[dict[str, Any]]
