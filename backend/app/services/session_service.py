"""Session service - business logic for session operations."""

from app.domain.enums import SessionType
from app.domain.models import Session
from app.repositories.interfaces import ISessionRepository


class SessionService:
    """
    Service for session-related operations.

    Implements business logic for querying and managing F1 sessions.
    """

    def __init__(self, session_repo: ISessionRepository):
        """
        Initialize the service with repository.

        Args:
            session_repo: Session repository implementation
        """
        self._session_repo = session_repo

    async def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID."""
        return await self._session_repo.get_by_id(session_id)

    async def get_sessions_by_year(self, year: int) -> list[Session]:
        """Get all sessions for a year."""
        return await self._session_repo.get_by_year(year)

    async def get_event_sessions(
        self, year: int, round_number: int
    ) -> list[Session]:
        """Get all sessions for an event."""
        return await self._session_repo.get_by_event(year, round_number)

    async def get_races(self, year: int) -> list[Session]:
        """Get all race sessions for a year."""
        return await self._session_repo.get_by_type(year, SessionType.RACE)

    async def get_qualifying(self, year: int) -> list[Session]:
        """Get all qualifying sessions for a year."""
        return await self._session_repo.get_by_type(year, SessionType.QUALIFYING)

    async def get_latest_sessions(self, limit: int = 10) -> list[Session]:
        """Get the most recent sessions."""
        return await self._session_repo.get_latest(limit)

    async def get_available_years(self) -> list[int]:
        """Get list of years with available data."""
        return await self._session_repo.get_years()

    async def get_events_for_year(self, year: int) -> list[dict]:
        """Get list of events for a year."""
        return await self._session_repo.get_events_for_year(year)

    async def save_session(self, session: Session) -> Session:
        """Save a session."""
        return await self._session_repo.add(session)

    async def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return await self._session_repo.exists(session_id)
