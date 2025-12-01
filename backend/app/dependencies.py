"""Dependency injection container for FastAPI."""

from functools import lru_cache
from pathlib import Path

from fastapi import Depends

from app.config import Settings, StorageBackend, get_settings
from app.ingestion import FastF1Fetcher
from app.repositories.interfaces import (
    IDriverRepository,
    ILapRepository,
    ISessionRepository,
    IStintRepository,
    ITelemetryRepository,
)
from app.repositories.file import (
    FileDriverRepository,
    FileLapRepository,
    FileSessionRepository,
    FileStintRepository,
    FileTelemetryRepository,
)
from app.services import (
    IngestionService,
    LapService,
    SessionService,
    StrategyService,
    TelemetryService,
)


# Repository Dependencies

def get_session_repository(
    settings: Settings = Depends(get_settings),
) -> ISessionRepository:
    """Get session repository based on storage backend."""
    if settings.storage_backend == StorageBackend.DYNAMODB:
        # Future: return DynamoDBSessionRepository(settings.dynamodb_config)
        raise NotImplementedError("DynamoDB backend not yet implemented")
    return FileSessionRepository(settings.data_dir)


def get_lap_repository(
    settings: Settings = Depends(get_settings),
) -> ILapRepository:
    """Get lap repository based on storage backend."""
    if settings.storage_backend == StorageBackend.DYNAMODB:
        raise NotImplementedError("DynamoDB backend not yet implemented")
    return FileLapRepository(settings.data_dir)


def get_driver_repository(
    settings: Settings = Depends(get_settings),
) -> IDriverRepository:
    """Get driver repository based on storage backend."""
    if settings.storage_backend == StorageBackend.DYNAMODB:
        raise NotImplementedError("DynamoDB backend not yet implemented")
    return FileDriverRepository(settings.data_dir)


def get_stint_repository(
    settings: Settings = Depends(get_settings),
) -> IStintRepository:
    """Get stint repository based on storage backend."""
    if settings.storage_backend == StorageBackend.DYNAMODB:
        raise NotImplementedError("DynamoDB backend not yet implemented")
    return FileStintRepository(settings.data_dir)


def get_telemetry_repository(
    settings: Settings = Depends(get_settings),
) -> ITelemetryRepository:
    """Get telemetry repository based on storage backend."""
    if settings.storage_backend == StorageBackend.DYNAMODB:
        raise NotImplementedError("DynamoDB backend not yet implemented")
    return FileTelemetryRepository(settings.data_dir)


# Service Dependencies

def get_session_service(
    session_repo: ISessionRepository = Depends(get_session_repository),
) -> SessionService:
    """Get session service."""
    return SessionService(session_repo)


def get_lap_service(
    lap_repo: ILapRepository = Depends(get_lap_repository),
) -> LapService:
    """Get lap service."""
    return LapService(lap_repo)


def get_strategy_service(
    stint_repo: IStintRepository = Depends(get_stint_repository),
    lap_repo: ILapRepository = Depends(get_lap_repository),
) -> StrategyService:
    """Get strategy service."""
    return StrategyService(stint_repo, lap_repo)


def get_telemetry_service(
    telemetry_repo: ITelemetryRepository = Depends(get_telemetry_repository),
) -> TelemetryService:
    """Get telemetry service."""
    return TelemetryService(telemetry_repo)


def get_fetcher(
    settings: Settings = Depends(get_settings),
) -> FastF1Fetcher:
    """Get FastF1 fetcher."""
    return FastF1Fetcher(settings.fastf1_cache_dir)


@lru_cache
def get_fastf1_fetcher(
    settings: Settings = Depends(get_settings),
) -> FastF1Fetcher:
    """Get FastF1 fetcher (cached)."""
    return FastF1Fetcher(settings.fastf1_cache_dir)


def get_ingestion_service(
    settings: Settings = Depends(get_settings),
    session_repo: ISessionRepository = Depends(get_session_repository),
    lap_repo: ILapRepository = Depends(get_lap_repository),
    driver_repo: IDriverRepository = Depends(get_driver_repository),
    stint_repo: IStintRepository = Depends(get_stint_repository),
    telemetry_repo: ITelemetryRepository = Depends(get_telemetry_repository),
) -> IngestionService:
    """Get ingestion service."""
    fetcher = FastF1Fetcher(settings.fastf1_cache_dir)
    return IngestionService(
        fetcher=fetcher,
        session_repo=session_repo,
        lap_repo=lap_repo,
        driver_repo=driver_repo,
        stint_repo=stint_repo,
        telemetry_repo=telemetry_repo,
    )
