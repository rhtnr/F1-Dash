"""Tire stint domain model."""

from datetime import timedelta

from pydantic import BaseModel, Field, computed_field

from app.domain.enums import TireCompound


class TireStint(BaseModel):
    """Represents a tire stint (period between pit stops on same tires)."""

    id: str = Field(..., description="Unique stint identifier")
    session_id: str = Field(..., description="Parent session ID")
    driver_id: str = Field(..., description="Driver abbreviation")
    stint_number: int = Field(..., ge=1, description="Stint number (1-indexed)")

    # Tire info
    compound: TireCompound = Field(..., description="Tire compound")
    is_fresh: bool = Field(True, description="New tires (vs. used)")

    # Stint boundaries
    start_lap: int = Field(..., ge=1, description="First lap of stint")
    end_lap: int = Field(..., ge=1, description="Last lap of stint")

    # Performance metrics
    avg_lap_time: timedelta | None = Field(None, description="Average lap time")
    best_lap_time: timedelta | None = Field(None, description="Best lap time in stint")
    degradation_rate: float | None = Field(
        None, description="Degradation rate (seconds/lap)"
    )

    model_config = {"frozen": True}

    @computed_field
    @property
    def total_laps(self) -> int:
        """Calculate total laps in this stint."""
        return self.end_lap - self.start_lap + 1

    @computed_field
    @property
    def avg_lap_time_seconds(self) -> float | None:
        """Get average lap time in seconds."""
        if self.avg_lap_time is None:
            return None
        return self.avg_lap_time.total_seconds()

    @classmethod
    def create_id(cls, session_id: str, driver_id: str, stint_number: int) -> str:
        """Create a unique stint ID."""
        return f"{session_id}_{driver_id}_stint_{stint_number}"


class PitStop(BaseModel):
    """Represents a pit stop."""

    id: str = Field(..., description="Unique pit stop identifier")
    session_id: str = Field(..., description="Parent session ID")
    driver_id: str = Field(..., description="Driver abbreviation")
    stop_number: int = Field(..., ge=1, description="Pit stop number")
    lap: int = Field(..., ge=1, description="Lap of pit stop")

    # Timing
    pit_time: timedelta | None = Field(None, description="Total pit time")
    pit_duration: timedelta | None = Field(None, description="Stationary time")

    # Tire change
    old_compound: TireCompound | None = Field(None, description="Previous compound")
    new_compound: TireCompound | None = Field(None, description="New compound")
    is_fresh_tyre: bool = Field(True, description="New tires fitted")

    model_config = {"frozen": True}

    @computed_field
    @property
    def pit_time_seconds(self) -> float | None:
        """Get pit time in seconds."""
        if self.pit_time is None:
            return None
        return self.pit_time.total_seconds()

    @classmethod
    def create_id(cls, session_id: str, driver_id: str, stop_number: int) -> str:
        """Create a unique pit stop ID."""
        return f"{session_id}_{driver_id}_pit_{stop_number}"
