"""Ingestion API endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Path, Query

from app.dependencies import get_ingestion_service
from app.services import IngestionService
from app.api.schemas.ingestion import (
    IngestSessionRequest,
    IngestTelemetryRequest,
    IngestEventRequest,
    IngestionResponse,
    VALID_SESSION_TYPES,
)

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


@router.post("/session", response_model=IngestionResponse)
async def ingest_session(
    request: IngestSessionRequest,
    background_tasks: BackgroundTasks,
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    """
    Ingest a session from FastF1.

    Fetches session data, laps, and driver information.
    Optionally includes telemetry data (slower).
    """
    # Check if already ingested
    existing_session_id = await ingestion_service.get_session_id(
        request.year, request.round_number, request.session_type
    )
    if existing_session_id and not request.force:
        # Return existing session instead of error
        return IngestionResponse(
            success=True,
            message=f"Session already exists: {existing_session_id}",
            session_id=existing_session_id,
        )

    try:
        session = await ingestion_service.ingest_session(
            year=request.year,
            event=request.round_number,
            session_type=request.session_type,
            include_telemetry=request.include_telemetry,
        )
        return IngestionResponse(
            success=True,
            message=f"Successfully ingested session: {session.id}",
            session_id=session.id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/telemetry", response_model=IngestionResponse)
async def ingest_telemetry(
    request: IngestTelemetryRequest,
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    """
    Ingest telemetry data for a driver.

    Can ingest all laps or specific lap numbers.
    """
    try:
        count = await ingestion_service.ingest_telemetry(
            year=request.year,
            event=request.round_number,
            session_type=request.session_type,
            driver_id=request.driver_id,
            lap_numbers=request.lap_numbers,
        )
        return IngestionResponse(
            success=True,
            message=f"Ingested {count} telemetry frames for {request.driver_id}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/event", response_model=IngestionResponse)
async def ingest_event(
    request: IngestEventRequest,
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    """
    Ingest all sessions for an event.

    Includes FP1-3, Qualifying, Sprint (if applicable), and Race.
    """
    try:
        sessions = await ingestion_service.ingest_event(
            year=request.year,
            event=request.round_number,
            include_telemetry=request.include_telemetry,
        )
        session_ids = [s.id for s in sessions]
        return IngestionResponse(
            success=True,
            message=f"Ingested {len(sessions)} sessions for {request.year} round {request.round_number}",
            session_ids=session_ids,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{year}/{round_number}/{session_type}")
async def check_ingestion_status(
    year: Annotated[int, Path(ge=2018, le=2030, description="Season year")],
    round_number: Annotated[int, Path(ge=1, le=30, description="Round number")],
    session_type: Annotated[str, Path(pattern=r"^(FP1|FP2|FP3|Q|SQ|SS|R|S)$", description="Session type")],
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    """Check if a session has been ingested."""
    is_ingested = await ingestion_service.is_session_ingested(
        year, round_number, session_type.upper()
    )
    return {
        "year": year,
        "round_number": round_number,
        "session_type": session_type.upper(),
        "is_ingested": is_ingested,
    }
