"""API v1 router - aggregates all endpoint routers."""

from fastapi import APIRouter

from app.api.v1 import sessions, laps, telemetry, strategy, ingestion, schedule, predictions

router = APIRouter()

router.include_router(sessions.router)
router.include_router(laps.router)
router.include_router(telemetry.router)
router.include_router(strategy.router)
router.include_router(ingestion.router)
router.include_router(schedule.router)
router.include_router(predictions.router)
