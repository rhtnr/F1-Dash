"""Telemetry API endpoints."""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_telemetry_service, get_fetcher, get_telemetry_repository, get_session_repository
from app.services import TelemetryService
from app.ingestion import FastF1Fetcher
from app.repositories.interfaces import ITelemetryRepository, ISessionRepository
from app.api.schemas.telemetry import (
    TelemetryResponse,
    SpeedTraceResponse,
    TelemetryComparisonResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@router.get("/{session_id}/{driver_id}/{lap_number}", response_model=TelemetryResponse)
async def get_lap_telemetry(
    session_id: str,
    driver_id: str,
    lap_number: int,
    telemetry_service: TelemetryService = Depends(get_telemetry_service),
):
    """
    Get full telemetry data for a specific lap.

    Returns detailed car data including speed, throttle, brake,
    gear, and position data.
    """
    frame = await telemetry_service.get_lap_telemetry(
        session_id, driver_id, lap_number
    )
    if not frame:
        raise HTTPException(
            status_code=404,
            detail=f"Telemetry not found for {driver_id} lap {lap_number}",
        )
    return TelemetryResponse.from_domain(frame)


@router.get("/{session_id}/{driver_id}/available")
async def get_available_telemetry(
    session_id: str,
    driver_id: str,
    telemetry_service: TelemetryService = Depends(get_telemetry_service),
):
    """Get list of laps with available telemetry."""
    laps = await telemetry_service.get_available_laps(session_id, driver_id)
    return {
        "session_id": session_id,
        "driver_id": driver_id,
        "available_laps": laps,
    }


@router.get("/{session_id}/{driver_id}/{lap_number}/speed-trace", response_model=SpeedTraceResponse)
async def get_speed_trace(
    session_id: str,
    driver_id: str,
    lap_number: int,
    telemetry_service: TelemetryService = Depends(get_telemetry_service),
):
    """
    Get simplified speed trace data for plotting.

    Returns distance, speed, gear, throttle, and brake data.
    """
    trace = await telemetry_service.get_speed_trace(
        session_id, driver_id, lap_number
    )
    if not trace:
        raise HTTPException(status_code=404, detail="Speed trace not available")

    return SpeedTraceResponse(
        session_id=session_id,
        driver_id=driver_id,
        lap_number=lap_number,
        points=trace,
    )


@router.get("/{session_id}/{driver_id}/{lap_number}/gear-changes")
async def get_gear_changes(
    session_id: str,
    driver_id: str,
    lap_number: int,
    telemetry_service: TelemetryService = Depends(get_telemetry_service),
):
    """Get gear change points for visualization."""
    changes = await telemetry_service.get_gear_changes(
        session_id, driver_id, lap_number
    )
    if changes is None:
        raise HTTPException(status_code=404, detail="Gear data not available")

    return {
        "session_id": session_id,
        "driver_id": driver_id,
        "lap_number": lap_number,
        "gear_changes": changes,
    }


@router.post("/{session_id}/compare", response_model=TelemetryComparisonResponse)
async def compare_telemetry(
    session_id: str,
    comparisons: list[dict],  # [{"driver_id": "VER", "lap_number": 10}, ...]
    telemetry_service: TelemetryService = Depends(get_telemetry_service),
    telemetry_repo: ITelemetryRepository = Depends(get_telemetry_repository),
    session_repo: ISessionRepository = Depends(get_session_repository),
    fetcher: FastF1Fetcher = Depends(get_fetcher),
):
    """
    Compare telemetry from multiple laps.

    Send a list of driver/lap combinations to compare.
    Automatically fetches telemetry on-demand if not cached.
    """
    # Get session info to determine year, round for fetching
    session = await session_repo.get_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    # Fetch telemetry on-demand for any missing laps
    for c in comparisons:
        driver_id = c["driver_id"]
        lap_number = c["lap_number"]

        # Check if telemetry exists
        existing = await telemetry_repo.get_by_lap(session_id, driver_id, lap_number)
        if not existing:
            logger.info(f"Fetching telemetry on-demand: {driver_id} lap {lap_number}")
            try:
                frame = await fetcher.fetch_telemetry(
                    session.year,
                    session.round_number,
                    session.session_type.value,
                    driver_id,
                    lap_number
                )
                if frame:
                    await telemetry_repo.add(frame)
                    logger.info(f"Cached telemetry for {driver_id} lap {lap_number}")
            except Exception as e:
                logger.warning(f"Failed to fetch telemetry for {driver_id} lap {lap_number}: {e}")

    comparison_tuples = [
        (c["driver_id"], c["lap_number"]) for c in comparisons
    ]
    results = await telemetry_service.compare_laps(session_id, comparison_tuples)

    return TelemetryComparisonResponse(
        session_id=session_id,
        laps=results,
    )
