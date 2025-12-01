"""Lap domain model."""

from datetime import timedelta

from pydantic import BaseModel, Field, computed_field

from app.domain.enums import TireCompound, TrackStatus


class Lap(BaseModel):
    """Represents a single lap recorded during a session."""

    id: str = Field(..., description="Unique lap identifier")
    session_id: str = Field(..., description="Parent session ID")
    driver_id: str = Field(..., description="Driver abbreviation")
    lap_number: int = Field(..., ge=1, description="Lap number")

    # Timing data
    lap_time: timedelta | None = Field(None, description="Total lap time")
    sector_1_time: timedelta | None = Field(None, description="Sector 1 time")
    sector_2_time: timedelta | None = Field(None, description="Sector 2 time")
    sector_3_time: timedelta | None = Field(None, description="Sector 3 time")

    # Tire data
    compound: TireCompound = Field(TireCompound.UNKNOWN, description="Tire compound")
    tyre_life: int = Field(0, ge=0, description="Laps on current tires")
    stint: int = Field(1, ge=1, description="Stint number")
    is_fresh_tyre: bool = Field(False, description="New tires this stint")

    # Speed traps (km/h)
    speed_i1: float | None = Field(None, description="Speed at intermediate 1")
    speed_i2: float | None = Field(None, description="Speed at intermediate 2")
    speed_fl: float | None = Field(None, description="Speed at finish line")
    speed_st: float | None = Field(None, description="Speed trap (max speed)")

    # Status
    position: int | None = Field(None, description="Position at end of lap")
    track_status: TrackStatus = Field(TrackStatus.GREEN, description="Track status")
    is_personal_best: bool = Field(False, description="Personal best lap")
    is_accurate: bool = Field(True, description="Timing data is accurate")
    deleted: bool = Field(False, description="Lap time deleted")
    deleted_reason: str | None = Field(None, description="Reason for deletion")

    # Pit stop
    pit_in_time: timedelta | None = Field(None, description="Pit entry time")
    pit_out_time: timedelta | None = Field(None, description="Pit exit time")
    is_pit_in_lap: bool = Field(False, description="Pitted at end of lap")
    is_pit_out_lap: bool = Field(False, description="Started from pit")

    model_config = {"frozen": True}

    @computed_field
    @property
    def lap_time_seconds(self) -> float | None:
        """Get lap time in seconds for easier plotting."""
        if self.lap_time is None:
            return None
        return self.lap_time.total_seconds()

    @computed_field
    @property
    def is_valid_for_analysis(self) -> bool:
        """Check if lap should be included in analysis."""
        return (
            self.lap_time is not None
            and self.is_accurate
            and not self.deleted
            and not self.is_pit_in_lap
            and not self.is_pit_out_lap
            and self.track_status == TrackStatus.GREEN
        )

    @classmethod
    def create_id(cls, session_id: str, driver_id: str, lap_number: int) -> str:
        """Create a unique lap ID."""
        return f"{session_id}_{driver_id}_{lap_number:03d}"


def timedelta_to_lap_string(td: timedelta | None) -> str:
    """Convert timedelta to lap time string format (M:SS.mmm)."""
    if td is None:
        return "--:--.---"

    total_seconds = td.total_seconds()
    minutes = int(total_seconds // 60)
    seconds = total_seconds % 60

    return f"{minutes}:{seconds:06.3f}"
