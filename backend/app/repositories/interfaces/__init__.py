"""Repository interfaces - abstract contracts for data access."""

from app.repositories.interfaces.base import IRepository
from app.repositories.interfaces.driver_repo import IDriverRepository
from app.repositories.interfaces.lap_repo import ILapRepository
from app.repositories.interfaces.session_repo import ISessionRepository
from app.repositories.interfaces.stint_repo import IStintRepository
from app.repositories.interfaces.telemetry_repo import ITelemetryRepository

__all__ = [
    "IDriverRepository",
    "ILapRepository",
    "IRepository",
    "ISessionRepository",
    "IStintRepository",
    "ITelemetryRepository",
]
