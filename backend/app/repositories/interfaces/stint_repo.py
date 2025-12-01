"""Tire stint repository interface."""

from abc import abstractmethod

from app.domain.enums import TireCompound
from app.domain.models import TireStint, PitStop
from app.repositories.interfaces.base import IRepository


class IStintRepository(IRepository[TireStint, str]):
    """
    Repository interface for tire stint data.

    Extends the base repository with stint-specific query methods.
    """

    @abstractmethod
    async def get_by_session(self, session_id: str) -> list[TireStint]:
        """
        Get all stints for a session.

        Args:
            session_id: The session identifier

        Returns:
            List of all tire stints in the session
        """
        pass

    @abstractmethod
    async def get_by_driver(
        self, session_id: str, driver_id: str
    ) -> list[TireStint]:
        """
        Get all stints for a specific driver in a session.

        Args:
            session_id: The session identifier
            driver_id: The driver abbreviation

        Returns:
            List of driver's stints
        """
        pass

    @abstractmethod
    async def get_by_compound(
        self, session_id: str, compound: TireCompound
    ) -> list[TireStint]:
        """
        Get all stints on a specific compound.

        Args:
            session_id: The session identifier
            compound: The tire compound

        Returns:
            List of stints on that compound
        """
        pass


class IPitStopRepository(IRepository[PitStop, str]):
    """
    Repository interface for pit stop data.
    """

    @abstractmethod
    async def get_by_session(self, session_id: str) -> list[PitStop]:
        """
        Get all pit stops for a session.

        Args:
            session_id: The session identifier

        Returns:
            List of all pit stops in the session
        """
        pass

    @abstractmethod
    async def get_by_driver(
        self, session_id: str, driver_id: str
    ) -> list[PitStop]:
        """
        Get all pit stops for a specific driver.

        Args:
            session_id: The session identifier
            driver_id: The driver abbreviation

        Returns:
            List of driver's pit stops
        """
        pass

    @abstractmethod
    async def get_fastest(
        self, session_id: str, top_n: int = 10
    ) -> list[PitStop]:
        """
        Get the fastest pit stops in a session.

        Args:
            session_id: The session identifier
            top_n: Number of pit stops to return

        Returns:
            List of fastest pit stops
        """
        pass
