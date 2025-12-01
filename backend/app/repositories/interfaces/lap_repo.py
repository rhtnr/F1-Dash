"""Lap repository interface."""

from abc import abstractmethod

from app.domain.enums import TireCompound
from app.domain.models import Lap
from app.repositories.interfaces.base import IRepository


class ILapRepository(IRepository[Lap, str]):
    """
    Repository interface for lap data.

    Extends the base repository with lap-specific query methods.
    """

    @abstractmethod
    async def get_by_session(self, session_id: str) -> list[Lap]:
        """
        Get all laps for a session.

        Args:
            session_id: The session identifier

        Returns:
            List of all laps in the session
        """
        pass

    @abstractmethod
    async def get_by_session_and_driver(
        self, session_id: str, driver_id: str
    ) -> list[Lap]:
        """
        Get all laps for a specific driver in a session.

        Args:
            session_id: The session identifier
            driver_id: The driver abbreviation

        Returns:
            List of driver's laps in the session
        """
        pass

    @abstractmethod
    async def get_by_compound(
        self, session_id: str, compound: TireCompound
    ) -> list[Lap]:
        """
        Get all laps on a specific tire compound.

        Args:
            session_id: The session identifier
            compound: The tire compound

        Returns:
            List of laps on that compound
        """
        pass

    @abstractmethod
    async def get_fastest_laps(
        self, session_id: str, top_n: int = 10
    ) -> list[Lap]:
        """
        Get the fastest laps in a session.

        Args:
            session_id: The session identifier
            top_n: Number of laps to return

        Returns:
            List of fastest laps, sorted by lap time
        """
        pass

    @abstractmethod
    async def get_valid_laps(self, session_id: str) -> list[Lap]:
        """
        Get all valid laps for analysis (excludes pit laps, deleted laps, etc.).

        Args:
            session_id: The session identifier

        Returns:
            List of valid laps
        """
        pass

    @abstractmethod
    async def get_personal_bests(self, session_id: str) -> list[Lap]:
        """
        Get the personal best lap for each driver.

        Args:
            session_id: The session identifier

        Returns:
            List of personal best laps (one per driver)
        """
        pass

    @abstractmethod
    async def get_by_stint(
        self, session_id: str, driver_id: str, stint_number: int
    ) -> list[Lap]:
        """
        Get all laps in a specific stint.

        Args:
            session_id: The session identifier
            driver_id: The driver abbreviation
            stint_number: The stint number

        Returns:
            List of laps in that stint
        """
        pass
