"""Ingestion service - orchestrates data fetching and storage."""

import logging
from pathlib import Path

from app.domain.models import Session
from app.ingestion import FastF1Fetcher
from app.repositories.interfaces import (
    ISessionRepository,
    ILapRepository,
    IDriverRepository,
    IStintRepository,
    ITelemetryRepository,
)

logger = logging.getLogger(__name__)


class IngestionService:
    """
    Service for orchestrating data ingestion.

    Coordinates fetching data from FastF1 and storing it
    via the repository layer.
    """

    def __init__(
        self,
        fetcher: FastF1Fetcher,
        session_repo: ISessionRepository,
        lap_repo: ILapRepository,
        driver_repo: IDriverRepository,
        stint_repo: IStintRepository,
        telemetry_repo: ITelemetryRepository,
    ):
        """
        Initialize with all required dependencies.

        Args:
            fetcher: FastF1 data fetcher
            session_repo: Session repository
            lap_repo: Lap repository
            driver_repo: Driver repository
            stint_repo: Stint repository
            telemetry_repo: Telemetry repository
        """
        self._fetcher = fetcher
        self._session_repo = session_repo
        self._lap_repo = lap_repo
        self._driver_repo = driver_repo
        self._stint_repo = stint_repo
        self._telemetry_repo = telemetry_repo

    async def ingest_session(
        self,
        year: int,
        event: str | int,
        session_type: str,
        include_telemetry: bool = False
    ) -> Session:
        """
        Ingest a complete session with all related data.

        Args:
            year: Season year
            event: Event name or round number
            session_type: Session type code
            include_telemetry: Whether to also fetch telemetry

        Returns:
            The ingested Session
        """
        logger.info(f"Starting ingestion: {year} {event} {session_type}")

        # Fetch session data
        session, laps, drivers = await self._fetcher.fetch_session(
            year, event, session_type, load_telemetry=include_telemetry
        )

        # Save session
        await self._session_repo.add(session)
        logger.info(f"Saved session: {session.id}")

        # Save drivers
        driver_ids = []
        for driver in drivers:
            await self._driver_repo.add(driver)
            driver_ids.append(driver.id)
        await self._driver_repo.add_session_drivers(session.id, driver_ids)
        await self._driver_repo.add_year_drivers(year, driver_ids)
        logger.info(f"Saved {len(drivers)} drivers")

        # Save laps
        await self._lap_repo.add_many(laps)
        logger.info(f"Saved {len(laps)} laps")

        # Calculate and save stints
        stints = await self._fetcher.fetch_stints(session.id, laps)
        for stint in stints:
            await self._stint_repo.add(stint)
        logger.info(f"Saved {len(stints)} stints")

        logger.info(f"Ingestion complete: {session.id}")
        return session

    async def ingest_telemetry(
        self,
        year: int,
        event: str | int,
        session_type: str,
        driver_id: str,
        lap_numbers: list[int] | None = None
    ) -> int:
        """
        Ingest telemetry data for a driver.

        Args:
            year: Season year
            event: Event name or round number
            session_type: Session type code
            driver_id: Driver abbreviation
            lap_numbers: Specific laps to fetch (None = all)

        Returns:
            Number of telemetry frames saved
        """
        logger.info(
            f"Ingesting telemetry for {driver_id}: {year} {event} {session_type}"
        )

        if lap_numbers:
            # Fetch specific laps
            count = 0
            for lap_number in lap_numbers:
                frame = await self._fetcher.fetch_telemetry(
                    year, event, session_type, driver_id, lap_number
                )
                if frame:
                    await self._telemetry_repo.add(frame)
                    count += 1
            return count
        else:
            # Fetch all laps
            frames = await self._fetcher.fetch_all_telemetry_for_driver(
                year, event, session_type, driver_id
            )
            for frame in frames:
                await self._telemetry_repo.add(frame)
            return len(frames)

    async def ingest_event(
        self,
        year: int,
        event: str | int,
        include_telemetry: bool = False
    ) -> list[Session]:
        """
        Ingest all sessions for an event.

        Args:
            year: Season year
            event: Event name or round number
            include_telemetry: Whether to include telemetry

        Returns:
            List of ingested sessions
        """
        logger.info(f"Ingesting event: {year} {event}")

        available_sessions = self._fetcher.get_available_sessions(year, event)
        sessions = []

        for session_type in available_sessions:
            try:
                session = await self.ingest_session(
                    year, event, session_type, include_telemetry
                )
                sessions.append(session)
            except Exception as e:
                logger.error(f"Failed to ingest {session_type}: {e}")

        return sessions

    async def ingest_season(
        self,
        year: int,
        session_types: list[str] | None = None
    ) -> int:
        """
        Ingest all sessions for a season.

        Args:
            year: Season year
            session_types: Session types to ingest (default: all)

        Returns:
            Number of sessions ingested
        """
        logger.info(f"Ingesting season: {year}")

        schedule = self._fetcher.get_schedule(year)
        count = 0

        types_to_fetch = session_types or ["R", "Q"]  # Default: Race and Qualifying

        for _, event_row in schedule.iterrows():
            round_number = event_row["RoundNumber"]
            for session_type in types_to_fetch:
                try:
                    await self.ingest_session(year, round_number, session_type)
                    count += 1
                except Exception as e:
                    logger.warning(
                        f"Failed {year} R{round_number} {session_type}: {e}"
                    )

        logger.info(f"Season ingestion complete: {count} sessions")
        return count

    async def is_session_ingested(
        self, year: int, round_number: int, session_type: str
    ) -> bool:
        """Check if a session has already been ingested."""
        from app.domain.enums import SessionType
        session_id = Session.create_id(
            year, round_number, SessionType.from_fastf1(session_type)
        )
        return await self._session_repo.exists(session_id)

    async def get_session_id(
        self, year: int, round_number: int, session_type: str
    ) -> str | None:
        """Get session ID if it exists, otherwise None."""
        from app.domain.enums import SessionType
        session_id = Session.create_id(
            year, round_number, SessionType.from_fastf1(session_type)
        )
        if await self._session_repo.exists(session_id):
            return session_id
        return None
