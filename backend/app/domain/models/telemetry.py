"""Telemetry domain models."""

from datetime import datetime

from pydantic import BaseModel, Field


class TelemetryPoint(BaseModel):
    """A single telemetry data point."""

    # Time reference
    time_ms: int = Field(..., description="Milliseconds from lap start")
    session_time_ms: int | None = Field(None, description="Milliseconds from session start")

    # Position on track
    distance: float = Field(..., ge=0, description="Distance from start line (meters)")

    # Car data
    speed: float = Field(..., ge=0, description="Speed (km/h)")
    rpm: int = Field(..., ge=0, description="Engine RPM")
    gear: int = Field(..., ge=0, le=8, description="Gear (0=neutral)")
    throttle: float = Field(..., ge=0, le=100, description="Throttle position (%)")
    brake: bool = Field(..., description="Brake applied")
    drs: int = Field(0, description="DRS status")

    # Position data (1/10 meter precision from FastF1)
    x: float | None = Field(None, description="X coordinate")
    y: float | None = Field(None, description="Y coordinate")
    z: float | None = Field(None, description="Z coordinate")

    model_config = {"frozen": True}

    @property
    def is_braking(self) -> bool:
        """Check if car is braking."""
        return self.brake

    @property
    def is_full_throttle(self) -> bool:
        """Check if at full throttle (>95%)."""
        return self.throttle >= 95.0

    @property
    def drs_open(self) -> bool:
        """Check if DRS is open."""
        # DRS values: 0-1 = off, 8+ = eligible, 10-14 = active
        return self.drs >= 10


class TelemetryFrame(BaseModel):
    """Complete telemetry data for a lap."""

    session_id: str = Field(..., description="Session ID")
    driver_id: str = Field(..., description="Driver abbreviation")
    lap_number: int = Field(..., ge=1, description="Lap number")

    # Metadata
    lap_time_ms: int | None = Field(None, description="Total lap time in milliseconds")
    timestamp: datetime | None = Field(None, description="When this data was recorded")

    # Telemetry points
    points: list[TelemetryPoint] = Field(
        default_factory=list, description="Telemetry data points"
    )

    model_config = {"frozen": True}

    @property
    def point_count(self) -> int:
        """Get number of telemetry points."""
        return len(self.points)

    @property
    def max_speed(self) -> float:
        """Get maximum speed in this lap."""
        if not self.points:
            return 0.0
        return max(p.speed for p in self.points)

    @property
    def track_length(self) -> float:
        """Get approximate track length from telemetry."""
        if not self.points:
            return 0.0
        return max(p.distance for p in self.points)

    def get_at_distance(self, distance: float) -> TelemetryPoint | None:
        """Get telemetry point closest to given distance."""
        if not self.points:
            return None
        return min(self.points, key=lambda p: abs(p.distance - distance))

    @classmethod
    def create_id(cls, session_id: str, driver_id: str, lap_number: int) -> str:
        """Create a unique telemetry frame ID."""
        return f"{session_id}_{driver_id}_{lap_number:03d}_telemetry"
