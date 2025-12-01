"""Session API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.models import Session


class SessionResponse(BaseModel):
    """Response schema for a session."""

    id: str
    year: int
    round_number: int
    event_name: str
    country: str
    location: str
    circuit_name: str
    circuit_short_name: str
    session_type: str
    session_type_name: str
    session_date: datetime
    total_laps: int | None
    display_name: str

    @classmethod
    def from_domain(cls, session: Session) -> "SessionResponse":
        """Create response from domain model."""
        return cls(
            id=session.id,
            year=session.year,
            round_number=session.round_number,
            event_name=session.event_name,
            country=session.country,
            location=session.location,
            circuit_name=session.circuit_name,
            circuit_short_name=session.circuit_short_name,
            session_type=session.session_type.value,
            session_type_name=session.session_type.display_name,
            session_date=session.session_date,
            total_laps=session.total_laps,
            display_name=session.display_name,
        )


class SessionListResponse(BaseModel):
    """Response schema for list of sessions."""

    count: int
    sessions: list[SessionResponse]


class EventSummary(BaseModel):
    """Summary of an event."""

    round_number: int
    event_name: str
    country: str
    location: str
    circuit_name: str
    session_types: list[str]


class EventListResponse(BaseModel):
    """Response schema for list of events."""

    year: int
    events: list[dict[str, Any]]


class YearListResponse(BaseModel):
    """Response schema for list of years."""

    years: list[int]
