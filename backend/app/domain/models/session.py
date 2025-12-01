"""Session domain model."""

from datetime import datetime

from pydantic import BaseModel, Field, computed_field

from app.domain.enums import SessionType


class Session(BaseModel):
    """Represents an F1 session (practice, qualifying, race, etc.)."""

    id: str = Field(..., description="Unique session identifier")
    year: int = Field(..., ge=2018, description="Season year")
    round_number: int = Field(..., ge=1, description="Round number in the season")
    event_name: str = Field(..., description="Grand Prix name")
    country: str = Field(..., description="Country name")
    location: str = Field(..., description="Circuit location/city")
    circuit_name: str = Field(..., description="Circuit name")
    circuit_short_name: str = Field(..., description="Circuit short name")
    session_type: SessionType = Field(..., description="Type of session")
    session_date: datetime = Field(..., description="Session date and time")
    total_laps: int | None = Field(None, description="Total laps (for races)")

    # Optional metadata
    official_name: str | None = Field(None, description="Official event name")

    model_config = {"frozen": True}

    @computed_field
    @property
    def display_name(self) -> str:
        """Get formatted display name."""
        return f"{self.year} {self.event_name} - {self.session_type.display_name}"

    @classmethod
    def create_id(cls, year: int, round_number: int, session_type: SessionType) -> str:
        """Create a unique session ID."""
        return f"{year}_{round_number:02d}_{session_type.value}"


class Event(BaseModel):
    """Represents an F1 race weekend event."""

    year: int = Field(..., ge=1950, description="Season year")
    round_number: int = Field(..., ge=1, description="Round number")
    event_name: str = Field(..., description="Grand Prix name")
    country: str = Field(..., description="Country name")
    location: str = Field(..., description="Circuit location")
    circuit_name: str = Field(..., description="Circuit name")
    event_date: datetime = Field(..., description="Event start date")
    event_format: str = Field("conventional", description="Event format")
    sessions: list[Session] = Field(default_factory=list, description="Sessions in this event")

    model_config = {"frozen": True}

    @property
    def is_sprint_weekend(self) -> bool:
        """Check if this is a sprint weekend."""
        return self.event_format == "sprint" or any(
            s.session_type in (SessionType.SPRINT, SessionType.SPRINT_SHOOTOUT)
            for s in self.sessions
        )
