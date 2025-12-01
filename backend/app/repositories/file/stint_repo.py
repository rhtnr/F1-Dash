"""File-based stint repository implementation."""

from pathlib import Path

from app.domain.enums import TireCompound
from app.domain.models import TireStint, PitStop
from app.repositories.interfaces import IStintRepository
from app.repositories.interfaces.stint_repo import IPitStopRepository
from app.repositories.file.base import FileRepository


class FileStintRepository(FileRepository[TireStint], IStintRepository):
    """File-based implementation of stint repository."""

    def __init__(self, data_dir: Path):
        super().__init__(data_dir, TireStint, "stints")

    async def add(self, entity: TireStint) -> TireStint:
        """Add a stint and update indexes."""
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

    async def get_by_session(self, session_id: str) -> list[TireStint]:
        """Get all stints for a session."""
        stint_ids = await self._read_index(f"session_{session_id}")
        stints = []
        for stint_id in stint_ids:
            stint = await self.get_by_id(stint_id)
            if stint:
                stints.append(stint)
        return sorted(stints, key=lambda s: (s.driver_id, s.stint_number))

    async def get_by_driver(
        self, session_id: str, driver_id: str
    ) -> list[TireStint]:
        """Get all stints for a driver in a session."""
        driver_key = f"driver_{session_id}_{driver_id}"
        stint_ids = await self._read_index(driver_key)
        stints = []
        for stint_id in stint_ids:
            stint = await self.get_by_id(stint_id)
            if stint:
                stints.append(stint)
        return sorted(stints, key=lambda s: s.stint_number)

    async def get_by_compound(
        self, session_id: str, compound: TireCompound
    ) -> list[TireStint]:
        """Get all stints on a specific compound."""
        compound_key = f"compound_{session_id}_{compound.value}"
        stint_ids = await self._read_index(compound_key)
        stints = []
        for stint_id in stint_ids:
            stint = await self.get_by_id(stint_id)
            if stint:
                stints.append(stint)
        return sorted(stints, key=lambda s: (s.driver_id, s.stint_number))


class FilePitStopRepository(FileRepository[PitStop], IPitStopRepository):
    """File-based implementation of pit stop repository."""

    def __init__(self, data_dir: Path):
        super().__init__(data_dir, PitStop, "pitstops")

    async def add(self, entity: PitStop) -> PitStop:
        """Add a pit stop and update indexes."""
        result = await super().add(entity)

        # Update session index
        await self._add_to_index(f"session_{entity.session_id}", entity.id)

        # Update driver index
        driver_key = f"driver_{entity.session_id}_{entity.driver_id}"
        await self._add_to_index(driver_key, entity.id)

        return result

    async def get_by_session(self, session_id: str) -> list[PitStop]:
        """Get all pit stops for a session."""
        stop_ids = await self._read_index(f"session_{session_id}")
        stops = []
        for stop_id in stop_ids:
            stop = await self.get_by_id(stop_id)
            if stop:
                stops.append(stop)
        return sorted(stops, key=lambda s: (s.lap, s.driver_id))

    async def get_by_driver(
        self, session_id: str, driver_id: str
    ) -> list[PitStop]:
        """Get all pit stops for a driver."""
        driver_key = f"driver_{session_id}_{driver_id}"
        stop_ids = await self._read_index(driver_key)
        stops = []
        for stop_id in stop_ids:
            stop = await self.get_by_id(stop_id)
            if stop:
                stops.append(stop)
        return sorted(stops, key=lambda s: s.stop_number)

    async def get_fastest(
        self, session_id: str, top_n: int = 10
    ) -> list[PitStop]:
        """Get fastest pit stops in a session."""
        all_stops = await self.get_by_session(session_id)
        valid_stops = [s for s in all_stops if s.pit_duration is not None]
        sorted_stops = sorted(valid_stops, key=lambda s: s.pit_duration)
        return sorted_stops[:top_n]
