"""File-based lap repository implementation."""

from pathlib import Path

from app.domain.enums import TireCompound
from app.domain.models import Lap
from app.repositories.interfaces import ILapRepository
from app.repositories.file.base import FileRepository


class FileLapRepository(FileRepository[Lap], ILapRepository):
    """File-based implementation of lap repository."""

    def __init__(self, data_dir: Path):
        super().__init__(data_dir, Lap, "laps")

    async def add(self, entity: Lap) -> Lap:
        """Add a lap and update indexes."""
        result = await super().add(entity)

        # Update session index
        await self._add_to_index(f"session_{entity.session_id}", entity.id)

        # Update driver index
        driver_key = f"driver_{entity.session_id}_{entity.driver_id}"
        await self._add_to_index(driver_key, entity.id)

        # Update compound index
        compound_key = f"compound_{entity.session_id}_{entity.compound.value}"
        await self._add_to_index(compound_key, entity.id)

        return result

    async def add_many(self, entities: list[Lap]) -> list[Lap]:
        """Add multiple laps with batch index updates."""
        # Group by session for efficient index updates
        by_session: dict[str, list[Lap]] = {}
        for lap in entities:
            if lap.session_id not in by_session:
                by_session[lap.session_id] = []
            by_session[lap.session_id].append(lap)

        for session_id, laps in by_session.items():
            session_ids = []
            driver_ids: dict[str, list[str]] = {}
            compound_ids: dict[str, list[str]] = {}

            for lap in laps:
                await super().add(lap)
                session_ids.append(lap.id)

                # Group driver indexes
                driver_key = f"driver_{session_id}_{lap.driver_id}"
                if driver_key not in driver_ids:
                    driver_ids[driver_key] = []
                driver_ids[driver_key].append(lap.id)

                # Group compound indexes
                compound_key = f"compound_{session_id}_{lap.compound.value}"
                if compound_key not in compound_ids:
                    compound_ids[compound_key] = []
                compound_ids[compound_key].append(lap.id)

            # Batch write indexes
            existing_session_ids = await self._read_index(f"session_{session_id}")
            await self._write_index(
                f"session_{session_id}",
                existing_session_ids + session_ids
            )

            for driver_key, ids in driver_ids.items():
                existing = await self._read_index(driver_key)
                await self._write_index(driver_key, existing + ids)

            for compound_key, ids in compound_ids.items():
                existing = await self._read_index(compound_key)
                await self._write_index(compound_key, existing + ids)

        return entities

    async def get_by_session(self, session_id: str) -> list[Lap]:
        """Get all laps for a session."""
        lap_ids = await self._read_index(f"session_{session_id}")
        laps = []
        for lap_id in lap_ids:
            lap = await self.get_by_id(lap_id)
            if lap:
                laps.append(lap)
        return sorted(laps, key=lambda l: (l.driver_id, l.lap_number))

    async def get_by_session_and_driver(
        self, session_id: str, driver_id: str
    ) -> list[Lap]:
        """Get all laps for a driver in a session."""
        driver_key = f"driver_{session_id}_{driver_id}"
        lap_ids = await self._read_index(driver_key)
        laps = []
        for lap_id in lap_ids:
            lap = await self.get_by_id(lap_id)
            if lap:
                laps.append(lap)
        return sorted(laps, key=lambda l: l.lap_number)

    async def get_by_compound(
        self, session_id: str, compound: TireCompound
    ) -> list[Lap]:
        """Get all laps on a specific compound."""
        compound_key = f"compound_{session_id}_{compound.value}"
        lap_ids = await self._read_index(compound_key)
        laps = []
        for lap_id in lap_ids:
            lap = await self.get_by_id(lap_id)
            if lap:
                laps.append(lap)
        return sorted(laps, key=lambda l: (l.driver_id, l.lap_number))

    async def get_fastest_laps(
        self, session_id: str, top_n: int = 10
    ) -> list[Lap]:
        """Get fastest laps in a session."""
        all_laps = await self.get_by_session(session_id)
        valid_laps = [
            lap for lap in all_laps
            if lap.lap_time is not None and lap.is_valid_for_analysis
        ]
        sorted_laps = sorted(valid_laps, key=lambda l: l.lap_time)
        return sorted_laps[:top_n]

    async def get_valid_laps(self, session_id: str) -> list[Lap]:
        """Get all valid laps for analysis."""
        all_laps = await self.get_by_session(session_id)
        return [lap for lap in all_laps if lap.is_valid_for_analysis]

    async def get_personal_bests(self, session_id: str) -> list[Lap]:
        """Get personal best lap for each driver."""
        all_laps = await self.get_by_session(session_id)

        # Group by driver and find fastest
        best_by_driver: dict[str, Lap] = {}
        for lap in all_laps:
            if lap.lap_time is None or not lap.is_valid_for_analysis:
                continue
            driver_id = lap.driver_id
            if driver_id not in best_by_driver:
                best_by_driver[driver_id] = lap
            elif lap.lap_time < best_by_driver[driver_id].lap_time:
                best_by_driver[driver_id] = lap

        return sorted(
            best_by_driver.values(),
            key=lambda l: l.lap_time if l.lap_time else float("inf")
        )

    async def get_by_stint(
        self, session_id: str, driver_id: str, stint_number: int
    ) -> list[Lap]:
        """Get all laps in a specific stint."""
        driver_laps = await self.get_by_session_and_driver(session_id, driver_id)
        return [lap for lap in driver_laps if lap.stint == stint_number]
