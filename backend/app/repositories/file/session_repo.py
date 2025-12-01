"""File-based session repository implementation."""

from pathlib import Path

from app.domain.enums import SessionType
from app.domain.models import Session
from app.repositories.interfaces import ISessionRepository
from app.repositories.file.base import FileRepository


class FileSessionRepository(FileRepository[Session], ISessionRepository):
    """File-based implementation of session repository."""

    def __init__(self, data_dir: Path):
        super().__init__(data_dir, Session, "sessions")

    async def add(self, entity: Session) -> Session:
        """Add a session and update indexes."""
        result = await super().add(entity)

        # Update year index
        await self._add_to_index(f"year_{entity.year}", entity.id)

        # Update event index
        event_key = f"event_{entity.year}_{entity.round_number:02d}"
        await self._add_to_index(event_key, entity.id)

        # Update type index
        type_key = f"type_{entity.year}_{entity.session_type.value}"
        await self._add_to_index(type_key, entity.id)

        return result

    async def get_by_year(self, year: int) -> list[Session]:
        """Get all sessions for a year."""
        session_ids = await self._read_index(f"year_{year}")
        sessions = []
        for session_id in session_ids:
            session = await self.get_by_id(session_id)
            if session:
                sessions.append(session)
        return sorted(sessions, key=lambda s: (s.round_number, s.session_type.value))

    async def get_by_event(self, year: int, round_number: int) -> list[Session]:
        """Get all sessions for a specific event."""
        event_key = f"event_{year}_{round_number:02d}"
        session_ids = await self._read_index(event_key)
        sessions = []
        for session_id in session_ids:
            session = await self.get_by_id(session_id)
            if session:
                sessions.append(session)
        # Sort by session type order
        type_order = {
            SessionType.PRACTICE_1: 1,
            SessionType.PRACTICE_2: 2,
            SessionType.PRACTICE_3: 3,
            SessionType.SPRINT_SHOOTOUT: 4,
            SessionType.SPRINT: 5,
            SessionType.QUALIFYING: 6,
            SessionType.RACE: 7,
        }
        return sorted(sessions, key=lambda s: type_order.get(s.session_type, 99))

    async def get_by_type(
        self, year: int, session_type: SessionType
    ) -> list[Session]:
        """Get all sessions of a specific type in a year."""
        type_key = f"type_{year}_{session_type.value}"
        session_ids = await self._read_index(type_key)
        sessions = []
        for session_id in session_ids:
            session = await self.get_by_id(session_id)
            if session:
                sessions.append(session)
        return sorted(sessions, key=lambda s: s.round_number)

    async def get_latest(self, limit: int = 10) -> list[Session]:
        """Get the most recent sessions."""
        all_sessions = await self.get_all()
        sorted_sessions = sorted(
            all_sessions,
            key=lambda s: s.session_date,
            reverse=True
        )
        return sorted_sessions[:limit]

    async def get_years(self) -> list[int]:
        """Get list of available years."""
        all_sessions = await self.get_all()
        years = set(s.year for s in all_sessions)
        return sorted(years, reverse=True)

    async def get_events_for_year(self, year: int) -> list[dict]:
        """Get list of events for a year with basic info."""
        sessions = await self.get_by_year(year)

        # Group by round
        events: dict[int, dict] = {}
        for session in sessions:
            if session.round_number not in events:
                events[session.round_number] = {
                    "round_number": session.round_number,
                    "event_name": session.event_name,
                    "country": session.country,
                    "location": session.location,
                    "circuit_name": session.circuit_name,
                    "session_types": [],
                }
            events[session.round_number]["session_types"].append(
                session.session_type.value
            )

        return sorted(events.values(), key=lambda e: e["round_number"])
