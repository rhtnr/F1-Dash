"""Driver repository interface."""

from abc import abstractmethod

from app.domain.models import Driver
from app.repositories.interfaces.base import IRepository


class IDriverRepository(IRepository[Driver, str]):
    """
    Repository interface for driver data.

    Extends the base repository with driver-specific query methods.
    """

    @abstractmethod
    async def get_by_session(self, session_id: str) -> list[Driver]:
        """
        Get all drivers who participated in a session.

        Args:
            session_id: The session identifier

        Returns:
            List of drivers in the session
        """
        pass

    @abstractmethod
    async def get_by_team(self, team_id: str) -> list[Driver]:
        """
        Get all drivers for a team.

        Args:
            team_id: The team identifier

        Returns:
            List of drivers on that team
        """
        pass

    @abstractmethod
    async def get_by_year(self, year: int) -> list[Driver]:
        """
        Get all drivers who participated in a season.

        Args:
            year: The season year

        Returns:
            List of drivers for that season
        """
        pass

    @abstractmethod
    async def get_by_number(self, number: int) -> Driver | None:
        """
        Get a driver by their car number.

        Args:
            number: The car number

        Returns:
            The driver if found, None otherwise
        """
        pass

    @abstractmethod
    async def search(self, query: str) -> list[Driver]:
        """
        Search drivers by name or abbreviation.

        Args:
            query: Search query string

        Returns:
            List of matching drivers
        """
        pass
