"""FastF1 data fetcher - retrieves and transforms F1 data."""

import logging
from pathlib import Path
from typing import Any

import fastf1
import pandas as pd

from app.domain.models import Driver, Lap, Session, TelemetryFrame, TireStint
from app.ingestion.transformers import (
    transform_driver,
    transform_lap,
    transform_session,
    transform_stint,
    transform_telemetry,
)

logger = logging.getLogger(__name__)


class FastF1Fetcher:
    """
    Fetches and transforms data from FastF1.

    This class handles all interaction with the FastF1 library,
    including caching and data transformation to domain models.
    """

    def __init__(self, cache_dir: Path):
        """
        Initialize the fetcher with cache directory.

        Args:
            cache_dir: Directory for FastF1 cache files
        """
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        fastf1.Cache.enable_cache(str(cache_dir))
        logger.info(f"FastF1 cache enabled at: {cache_dir}")

    def get_schedule(self, year: int) -> pd.DataFrame:
        """
        Get the event schedule for a year.

        Args:
            year: Season year

        Returns:
            DataFrame with event schedule
        """
        return fastf1.get_event_schedule(year)

    def get_event(self, year: int, event: str | int) -> Any:
        """
        Get a specific event.

        Args:
            year: Season year
            event: Event name or round number

        Returns:
            FastF1 Event object
        """
        return fastf1.get_event(year, event)

    async def fetch_session(
        self,
        year: int,
        event: str | int,
        session_type: str,
        load_telemetry: bool = False
    ) -> tuple[Session, list[Lap], list[Driver]]:
        """
        Fetch session data from FastF1.

        Args:
            year: Season year
            event: Event name or round number
            session_type: Session type (FP1, FP2, FP3, Q, S, R)
            load_telemetry: Whether to load telemetry data

        Returns:
            Tuple of (Session, list of Laps, list of Drivers)
        """
        logger.info(f"Fetching session: {year} {event} {session_type}")

        # Get session from FastF1
        ff1_session = fastf1.get_session(year, event, session_type)
        ff1_session.load(
            laps=True,
            telemetry=load_telemetry,
            weather=True,
            messages=True
        )

        # Transform session
        session = transform_session(ff1_session)
        logger.info(f"Session transformed: {session.id}")

        # Transform drivers
        drivers = []
        for _, driver_info in ff1_session.results.iterrows():
            try:
                driver = transform_driver(driver_info.to_dict(), session.id)
                drivers.append(driver)
            except Exception as e:
                logger.warning(f"Failed to transform driver: {e}")

        logger.info(f"Transformed {len(drivers)} drivers")

        # Transform laps
        laps = []
        for _, row in ff1_session.laps.iterrows():
            try:
                lap = transform_lap(row, session.id)
                laps.append(lap)
            except Exception as e:
                logger.warning(f"Failed to transform lap: {e}")

        logger.info(f"Transformed {len(laps)} laps")

        return session, laps, drivers

    async def fetch_stints(
        self,
        session_id: str,
        laps: list[Lap]
    ) -> list[TireStint]:
        """
        Calculate tire stints from lap data.

        Args:
            session_id: Session ID
            laps: List of laps

        Returns:
            List of TireStint models
        """
        stints = []

        # Group laps by driver and stint
        driver_stints: dict[str, dict[int, list[Lap]]] = {}
        for lap in laps:
            if lap.driver_id not in driver_stints:
                driver_stints[lap.driver_id] = {}
            if lap.stint not in driver_stints[lap.driver_id]:
                driver_stints[lap.driver_id][lap.stint] = []
            driver_stints[lap.driver_id][lap.stint].append(lap)

        # Create stint objects
        for driver_id, stint_laps in driver_stints.items():
            for stint_number, stint_lap_list in stint_laps.items():
                try:
                    stint = transform_stint(
                        stint_lap_list, session_id, driver_id, stint_number
                    )
                    stints.append(stint)
                except Exception as e:
                    logger.warning(
                        f"Failed to create stint for {driver_id} stint {stint_number}: {e}"
                    )

        logger.info(f"Created {len(stints)} stints")
        return stints

    async def fetch_telemetry(
        self,
        year: int,
        event: str | int,
        session_type: str,
        driver: str,
        lap_number: int
    ) -> TelemetryFrame | None:
        """
        Fetch telemetry for a specific lap.

        Args:
            year: Season year
            event: Event name or round number
            session_type: Session type
            driver: Driver abbreviation
            lap_number: Lap number

        Returns:
            TelemetryFrame or None if not available
        """
        logger.info(
            f"Fetching telemetry: {year} {event} {session_type} "
            f"{driver} lap {lap_number}"
        )

        ff1_session = fastf1.get_session(year, event, session_type)
        ff1_session.load(laps=True, telemetry=True)

        # Get the specific lap
        driver_laps = ff1_session.laps.pick_drivers(driver)
        lap = driver_laps[driver_laps["LapNumber"] == lap_number]

        if lap.empty:
            logger.warning(f"Lap not found: {driver} lap {lap_number}")
            return None

        lap = lap.iloc[0]

        # Get car data with distance
        try:
            car_data = lap.get_car_data().add_distance()
            # Merge position data (X, Y, Z) for track map
            try:
                pos_data = lap.get_pos_data()
                if pos_data is not None and not pos_data.empty:
                    # Merge on Time column
                    car_data = pd.merge_asof(
                        car_data.sort_values('Time'),
                        pos_data[['Time', 'X', 'Y', 'Z']].sort_values('Time'),
                        on='Time',
                        direction='nearest'
                    )
            except Exception as pos_e:
                logger.warning(f"Failed to merge position data: {pos_e}")
        except Exception as e:
            logger.warning(f"Failed to get car data: {e}")
            return None

        # Get session ID
        session = transform_session(ff1_session)

        # Transform telemetry
        lap_time_ms = None
        if pd.notna(lap["LapTime"]):
            lap_time_ms = int(lap["LapTime"].total_seconds() * 1000)

        return transform_telemetry(
            car_data,
            session.id,
            driver,
            lap_number,
            lap_time_ms
        )

    async def fetch_all_telemetry_for_driver(
        self,
        year: int,
        event: str | int,
        session_type: str,
        driver: str
    ) -> list[TelemetryFrame]:
        """
        Fetch telemetry for all laps by a driver.

        Args:
            year: Season year
            event: Event name or round number
            session_type: Session type
            driver: Driver abbreviation

        Returns:
            List of TelemetryFrame models
        """
        logger.info(
            f"Fetching all telemetry for {driver}: {year} {event} {session_type}"
        )

        ff1_session = fastf1.get_session(year, event, session_type)
        ff1_session.load(laps=True, telemetry=True)

        session = transform_session(ff1_session)
        driver_laps = ff1_session.laps.pick_drivers(driver)

        frames = []
        for _, lap in driver_laps.iterrows():
            try:
                car_data = lap.get_car_data().add_distance()
                # Merge position data (X, Y, Z) for track map
                try:
                    pos_data = lap.get_pos_data()
                    if pos_data is not None and not pos_data.empty:
                        car_data = pd.merge_asof(
                            car_data.sort_values('Time'),
                            pos_data[['Time', 'X', 'Y', 'Z']].sort_values('Time'),
                            on='Time',
                            direction='nearest'
                        )
                except Exception as pos_e:
                    logger.warning(f"Failed to merge position data: {pos_e}")

                lap_time_ms = None
                if pd.notna(lap["LapTime"]):
                    lap_time_ms = int(lap["LapTime"].total_seconds() * 1000)

                frame = transform_telemetry(
                    car_data,
                    session.id,
                    driver,
                    int(lap["LapNumber"]),
                    lap_time_ms
                )
                frames.append(frame)
            except Exception as e:
                logger.warning(
                    f"Failed to get telemetry for lap {lap['LapNumber']}: {e}"
                )

        logger.info(f"Fetched {len(frames)} telemetry frames for {driver}")
        return frames

    def get_available_sessions(self, year: int, event: str | int) -> list[str]:
        """
        Get list of available sessions for an event.

        Args:
            year: Season year
            event: Event name or round number

        Returns:
            List of session type codes
        """
        event_obj = self.get_event(year, event)
        sessions = []

        for session_name in ["FP1", "FP2", "FP3", "Q", "S", "SS", "R"]:
            try:
                session = fastf1.get_session(year, event, session_name)
                if session is not None:
                    sessions.append(session_name)
            except Exception:
                continue

        return sessions
