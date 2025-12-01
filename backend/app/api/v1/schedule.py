"""Schedule API endpoints - FastF1 event schedule data."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.ingestion import FastF1Fetcher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schedule", tags=["Schedule"])


class ScheduleYearListResponse(BaseModel):
    """Response for available years from FastF1."""
    years: list[int]


class ScheduleEventInfo(BaseModel):
    """Event info from FastF1 schedule."""
    round_number: int
    event_name: str
    country: str
    location: str
    event_date: str | None = None
    event_format: str | None = None


class ScheduleEventListResponse(BaseModel):
    """Response for events in a year from FastF1."""
    year: int
    events: list[ScheduleEventInfo]


class ScheduleSessionInfo(BaseModel):
    """Session info from FastF1 schedule."""
    session_type: str
    session_name: str


class ScheduleSessionListResponse(BaseModel):
    """Response for sessions in an event from FastF1."""
    year: int
    round_number: int
    event_name: str
    sessions: list[ScheduleSessionInfo]


def get_fetcher(settings: Settings = Depends(get_settings)) -> FastF1Fetcher:
    """Get FastF1 fetcher."""
    return FastF1Fetcher(settings.fastf1_cache_dir)


@router.get("/years", response_model=ScheduleYearListResponse)
async def list_available_years():
    """
    Get list of years available in FastF1.

    FastF1 supports data from 2018 onwards.
    """
    current_year = datetime.now().year
    # FastF1 supports 2018+ and current year may have data for upcoming races
    years = list(range(current_year, 2017, -1))
    return ScheduleYearListResponse(years=years)


@router.get("/events/{year}", response_model=ScheduleEventListResponse)
async def list_events_for_year(
    year: int,
    fetcher: FastF1Fetcher = Depends(get_fetcher),
):
    """
    Get list of events for a specific year from FastF1.

    This fetches directly from the FastF1 schedule, not from ingested data.
    """
    try:
        schedule = fetcher.get_schedule(year)

        events = []
        for _, row in schedule.iterrows():
            # Skip testing events
            event_name = str(row.get("EventName", ""))
            if "testing" in event_name.lower():
                continue

            round_number = int(row.get("RoundNumber", 0))
            if round_number == 0:
                continue

            event_date = None
            if "EventDate" in row and row["EventDate"] is not None:
                try:
                    event_date = str(row["EventDate"])[:10]  # Just the date part
                except Exception:
                    pass

            events.append(ScheduleEventInfo(
                round_number=round_number,
                event_name=event_name,
                country=str(row.get("Country", "")),
                location=str(row.get("Location", "")),
                event_date=event_date,
                event_format=str(row.get("EventFormat", "")) if "EventFormat" in row else None,
            ))

        return ScheduleEventListResponse(year=year, events=events)

    except Exception as e:
        logger.error(f"Failed to fetch schedule for {year}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch schedule: {str(e)}"
        )


@router.get("/sessions/{year}/{round_number}", response_model=ScheduleSessionListResponse)
async def list_sessions_for_event(
    year: int,
    round_number: int,
    fetcher: FastF1Fetcher = Depends(get_fetcher),
):
    """
    Get list of available sessions for a specific event from FastF1.

    This fetches directly from FastF1, not from ingested data.
    """
    try:
        event = fetcher.get_event(year, round_number)
        event_name = str(event.get("EventName", f"Round {round_number}"))

        sessions = []
        session_mapping = {
            "FP1": "Practice 1",
            "FP2": "Practice 2",
            "FP3": "Practice 3",
            "Q": "Qualifying",
            "SQ": "Sprint Qualifying",
            "S": "Sprint",
            "SS": "Sprint Shootout",
            "R": "Race",
        }

        # Check which sessions exist for this event
        for session_type, session_name in session_mapping.items():
            try:
                # Try to get session info from event
                session_key = f"Session{list(session_mapping.keys()).index(session_type) + 1}"
                if hasattr(event, session_type) or session_type in ["FP1", "FP2", "FP3", "Q", "S", "R"]:
                    # Verify by attempting to reference the session
                    import fastf1
                    try:
                        _ = fastf1.get_session(year, round_number, session_type)
                        sessions.append(ScheduleSessionInfo(
                            session_type=session_type,
                            session_name=session_name,
                        ))
                    except Exception:
                        continue
            except Exception:
                continue

        return ScheduleSessionListResponse(
            year=year,
            round_number=round_number,
            event_name=event_name,
            sessions=sessions,
        )

    except Exception as e:
        logger.error(f"Failed to fetch sessions for {year} round {round_number}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch sessions: {str(e)}"
        )
