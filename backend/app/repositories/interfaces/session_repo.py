"""Session repository interface."""

from abc import abstractmethod

from app.domain.enums import SessionType
from app.domain.models import Session
from app.repositories.interfaces.base import IRepository


class ISessionRepository(IRepository[Session, str]):
    """
    Repository interface for F1 sessions.

    Extends the base repository with session-specific query methods.
    """

    @abstractmethod
    async def get_by_year(self, year: int) -> list[Session]:
        """
        Get all sessions for a specific year.

        Args:
            year: The season year (2018+)

        Returns:
            List of sessions for that year
        """
        pass

    @abstractmethod
    async def get_by_event(self, year: int, round_number: int) -> list[Session]:
        """
        Get all sessions for a specific event.

        Args:
            year: The season year
            round_number: The round number in the season

        Returns:
            List of sessions for that event
        """
        pass

    @abstractmethod
    async def get_by_type(
        self, year: int, session_type: SessionType
    ) -> list[Session]:
        """
        Get all sessions of a specific type in a year.

        Args:
            year: The season year
            session_type: The type of session (FP1, Q, R, etc.)

        Returns:
            List of matching sessions
        """
        pass

    @abstractmethod
    async def get_latest(self, limit: int = 10) -> list[Session]:
        """
        Get the most recent sessions.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of most recent sessions
        """
        pass

    @abstractmethod
    async def get_years(self) -> list[int]:
        """
        Get list of available years.

        Returns:
            List of years with data
        """
        pass

    @abstractmethod
    async def get_events_for_year(self, year: int) -> list[dict]:
        """
        Get list of events for a year with basic info.

        Args:
            year: The season year

        Returns:
            List of event summaries with round_number, event_name, etc.
        """
        pass
