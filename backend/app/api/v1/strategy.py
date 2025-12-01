"""Strategy API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_strategy_service
from app.domain.enums import TireCompound
from app.services import StrategyService
from app.api.schemas.strategy import (
    StintResponse,
    StintListResponse,
    StrategySummaryResponse,
    DegradationResponse,
)

router = APIRouter(prefix="/strategy", tags=["Strategy"])


@router.get("/{session_id}/stints", response_model=StintListResponse)
async def get_session_stints(
    session_id: str,
    driver_id: str | None = Query(None, description="Filter by driver"),
    compound: str | None = Query(None, description="Filter by compound"),
    strategy_service: StrategyService = Depends(get_strategy_service),
):
    """
    Get tire stint data for a session.

    Filter by driver or tire compound.
    """
    if driver_id:
        stints = await strategy_service.get_driver_stints(session_id, driver_id)
    elif compound:
        try:
            compound_enum = TireCompound(compound.upper())
            stints = await strategy_service.get_compound_stints(
                session_id, compound_enum
            )
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid compound: {compound}"
            )
    else:
        stints = await strategy_service.get_session_stints(session_id)

    return StintListResponse(
        session_id=session_id,
        count=len(stints),
        stints=[StintResponse.from_domain(stint) for stint in stints],
    )


@router.get("/{session_id}/summary", response_model=StrategySummaryResponse)
async def get_strategy_summary(
    session_id: str,
    strategy_service: StrategyService = Depends(get_strategy_service),
):
    """
    Get strategy summary for all drivers.

    Returns compound usage and stint information per driver.
    """
    summaries = await strategy_service.get_strategy_summary(session_id)
    return StrategySummaryResponse(
        session_id=session_id,
        strategies=summaries,
    )


@router.get("/{session_id}/compound-analysis")
async def get_compound_analysis(
    session_id: str,
    strategy_service: StrategyService = Depends(get_strategy_service),
):
    """
    Analyze compound performance across all drivers.

    Returns metrics to help determine optimal compound choice.
    """
    analysis = await strategy_service.get_optimal_compound(session_id)
    return {
        "session_id": session_id,
        "compounds": analysis,
    }


@router.get("/{session_id}/degradation/{driver_id}/{stint_number}", response_model=DegradationResponse)
async def get_stint_degradation(
    session_id: str,
    driver_id: str,
    stint_number: int,
    strategy_service: StrategyService = Depends(get_strategy_service),
):
    """
    Get detailed degradation analysis for a specific stint.

    Returns lap-by-lap performance data and degradation rate.
    """
    result = await strategy_service.calculate_stint_degradation(
        session_id, driver_id, stint_number
    )
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Stint data not found for {driver_id} stint {stint_number}",
        )

    return DegradationResponse(
        session_id=session_id,
        driver_id=driver_id,
        stint_number=stint_number,
        compound=result["compound"],
        total_laps=result["total_laps"],
        degradation_per_lap=result["degradation_per_lap"],
        laps=result["laps"],
    )
