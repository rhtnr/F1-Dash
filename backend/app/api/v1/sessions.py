"""Session API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_session_service
from app.services import SessionService
from app.api.schemas.session import (
    SessionResponse,
    SessionListResponse,
    EventListResponse,
    YearListResponse,
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    year: int | None = Query(None, ge=2018, description="Filter by year"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    session_service: SessionService = Depends(get_session_service),
):
    """
    List available sessions.

    Optionally filter by year. Returns sessions sorted by date.
    """
    if year:
        sessions = await session_service.get_sessions_by_year(year)
    else:
        sessions = await session_service.get_latest_sessions(limit)

    return SessionListResponse(
        count=len(sessions),
        sessions=[SessionResponse.from_domain(s) for s in sessions],
    )


@router.get("/years", response_model=YearListResponse)
async def list_years(
    session_service: SessionService = Depends(get_session_service),
):
    """Get list of years with available data."""
    years = await session_service.get_available_years()
    return YearListResponse(years=years)


@router.get("/events/{year}", response_model=EventListResponse)
async def list_events(
    year: int,
    session_service: SessionService = Depends(get_session_service),
):
    """Get list of events for a specific year."""
    events = await session_service.get_events_for_year(year)
    return EventListResponse(year=year, events=events)


@router.get("/id/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
):
    """Get a specific session by ID."""
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse.from_domain(session)


@router.get("/{year}/{round_number}", response_model=SessionListResponse)
async def get_event_sessions(
    year: int,
    round_number: int,
    session_service: SessionService = Depends(get_session_service),
):
    """Get all sessions for a specific event."""
    sessions = await session_service.get_event_sessions(year, round_number)
    if not sessions:
        raise HTTPException(
            status_code=404,
            detail=f"No sessions found for {year} round {round_number}",
        )
    return SessionListResponse(
        count=len(sessions),
        sessions=[SessionResponse.from_domain(s) for s in sessions],
    )
