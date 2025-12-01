"""Telemetry repository interface."""

from abc import abstractmethod

from app.domain.models import TelemetryFrame
from app.repositories.interfaces.base import IRepository


class ITelemetryRepository(IRepository[TelemetryFrame, str]):
    """
    Repository interface for telemetry data.

    Telemetry data is large, so this repository provides
    specialized methods for efficient access.
    """

    @abstractmethod
    async def get_by_lap(
        self, session_id: str, driver_id: str, lap_number: int
    ) -> TelemetryFrame | None:
        """
        Get telemetry for a specific lap.

        Args:
            session_id: The session identifier
            driver_id: The driver abbreviation
            lap_number: The lap number

        Returns:
            TelemetryFrame if available, None otherwise
        """
        pass

    @abstractmethod
    async def get_driver_laps(
        self, session_id: str, driver_id: str
    ) -> list[TelemetryFrame]:
        """
        Get telemetry for all laps by a driver.

        Args:
            session_id: The session identifier
            driver_id: The driver abbreviation

        Returns:
            List of telemetry frames for driver's laps
        """
        pass

    @abstractmethod
    async def get_fastest_lap_telemetry(
        self, session_id: str, driver_id: str
    ) -> TelemetryFrame | None:
        """
        Get telemetry for a driver's fastest lap.

        Args:
            session_id: The session identifier
            driver_id: The driver abbreviation

        Returns:
            TelemetryFrame for fastest lap if available
        """
        pass

    @abstractmethod
    async def has_telemetry(
        self, session_id: str, driver_id: str, lap_number: int
    ) -> bool:
        """
        Check if telemetry exists for a specific lap.

        Args:
            session_id: The session identifier
            driver_id: The driver abbreviation
            lap_number: The lap number

        Returns:
            True if telemetry exists
        """
        pass

    @abstractmethod
    async def get_available_laps(
        self, session_id: str, driver_id: str
    ) -> list[int]:
        """
        Get list of lap numbers with available telemetry.

        Args:
            session_id: The session identifier
            driver_id: The driver abbreviation

        Returns:
            List of lap numbers with telemetry data
        """
        pass
