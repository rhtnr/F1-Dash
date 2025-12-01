"""Lap API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_lap_service, get_session_service
from app.domain.enums import TireCompound
from app.services import LapService, SessionService
from app.api.schemas.lap import (
    LapResponse,
    LapListResponse,
    LapComparisonResponse,
    CompoundPerformanceResponse,
)

router = APIRouter(prefix="/laps", tags=["Laps"])


@router.get("/{session_id}", response_model=LapListResponse)
async def get_session_laps(
    session_id: str,
    driver_id: str | None = Query(None, description="Filter by driver"),
    compound: str | None = Query(None, description="Filter by tire compound"),
    valid_only: bool = Query(False, description="Only return valid laps"),
    lap_service: LapService = Depends(get_lap_service),
    session_service: SessionService = Depends(get_session_service),
):
    """
    Get laps for a session with optional filters.

    Filter by driver, tire compound, or get only valid laps for analysis.
    """
    # Verify session exists
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get laps based on filters
    if driver_id:
        laps = await lap_service.get_driver_laps(session_id, driver_id)
    elif valid_only:
        laps = await lap_service.get_valid_laps(session_id)
    else:
        laps = await lap_service.get_session_laps(session_id)

    # Apply compound filter
    if compound:
        try:
            compound_enum = TireCompound(compound.upper())
            laps = [l for l in laps if l.compound == compound_enum]
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid compound: {compound}"
            )

    return LapListResponse(
        session_id=session_id,
        count=len(laps),
        laps=[LapResponse.from_domain(lap) for lap in laps],
    )


@router.get("/{session_id}/fastest", response_model=LapListResponse)
async def get_fastest_laps(
    session_id: str,
    top_n: int = Query(10, ge=1, le=100, description="Number of laps"),
    lap_service: LapService = Depends(get_lap_service),
):
    """Get the fastest laps in a session."""
    laps = await lap_service.get_fastest_laps(session_id, top_n)
    return LapListResponse(
        session_id=session_id,
        count=len(laps),
        laps=[LapResponse.from_domain(lap) for lap in laps],
    )


@router.get("/{session_id}/personal-bests", response_model=LapListResponse)
async def get_personal_bests(
    session_id: str,
    lap_service: LapService = Depends(get_lap_service),
):
    """Get the personal best lap for each driver."""
    laps = await lap_service.get_personal_bests(session_id)
    return LapListResponse(
        session_id=session_id,
        count=len(laps),
        laps=[LapResponse.from_domain(lap) for lap in laps],
    )


@router.get("/{session_id}/distribution")
async def get_lap_distribution(
    session_id: str,
    lap_service: LapService = Depends(get_lap_service),
):
    """Get lap time distribution by driver."""
    distribution = await lap_service.get_lap_time_distribution(session_id)
    return {
        "session_id": session_id,
        "drivers": distribution,
    }


@router.get("/{session_id}/compound-performance", response_model=CompoundPerformanceResponse)
async def get_compound_performance(
    session_id: str,
    lap_service: LapService = Depends(get_lap_service),
):
    """Get performance statistics by tire compound."""
    performance = await lap_service.get_compound_performance(session_id)
    return CompoundPerformanceResponse(
        session_id=session_id,
        compounds=performance,
    )


@router.get("/{session_id}/compare", response_model=LapComparisonResponse)
async def compare_drivers(
    session_id: str,
    driver1: str = Query(..., description="First driver ID"),
    driver2: str = Query(..., description="Second driver ID"),
    lap_service: LapService = Depends(get_lap_service),
):
    """Compare two drivers' lap performance."""
    comparison = await lap_service.compare_drivers(session_id, driver1, driver2)
    return LapComparisonResponse(
        session_id=session_id,
        comparison=comparison,
    )


@router.get("/{session_id}/driver/{driver_id}/stint/{stint_number}", response_model=LapListResponse)
async def get_stint_laps(
    session_id: str,
    driver_id: str,
    stint_number: int,
    lap_service: LapService = Depends(get_lap_service),
):
    """Get all laps in a specific stint."""
    laps = await lap_service.get_stint_laps(session_id, driver_id, stint_number)
    return LapListResponse(
        session_id=session_id,
        count=len(laps),
        laps=[LapResponse.from_domain(lap) for lap in laps],
    )
