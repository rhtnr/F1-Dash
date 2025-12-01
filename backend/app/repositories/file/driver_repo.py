"""File-based driver repository implementation."""

from pathlib import Path

from app.domain.models import Driver
from app.repositories.interfaces import IDriverRepository
from app.repositories.file.base import FileRepository


class FileDriverRepository(FileRepository[Driver], IDriverRepository):
    """File-based implementation of driver repository."""

    def __init__(self, data_dir: Path):
        super().__init__(data_dir, Driver, "drivers")

    async def add(self, entity: Driver) -> Driver:
        """Add a driver and update indexes."""
        result = await super().add(entity)

        # Update team index
        await self._add_to_index(f"team_{entity.team_id}", entity.id)

        # Update number index (special - single driver per number)
        await self._write_index(f"number_{entity.number}", [entity.id])

        return result

    async def get_by_session(self, session_id: str) -> list[Driver]:
        """Get all drivers who participated in a session."""
        # Session-driver mapping is stored as an index
        driver_ids = await self._read_index(f"session_{session_id}")
        drivers = []
        for driver_id in driver_ids:
            driver = await self.get_by_id(driver_id)
            if driver:
                drivers.append(driver)
        return sorted(drivers, key=lambda d: d.number)

    async def add_session_drivers(
        self, session_id: str, driver_ids: list[str]
    ) -> None:
        """Associate drivers with a session."""
        await self._write_index(f"session_{session_id}", driver_ids)

    async def get_by_team(self, team_id: str) -> list[Driver]:
        """Get all drivers for a team."""
        driver_ids = await self._read_index(f"team_{team_id}")
        drivers = []
        for driver_id in driver_ids:
            driver = await self.get_by_id(driver_id)
            if driver:
                drivers.append(driver)
        return sorted(drivers, key=lambda d: d.number)

    async def get_by_year(self, year: int) -> list[Driver]:
        """Get all drivers who participated in a season."""
        driver_ids = await self._read_index(f"year_{year}")
        if not driver_ids:
            # Fallback: get all drivers (simplified)
            return await self.get_all()
        drivers = []
        for driver_id in driver_ids:
            driver = await self.get_by_id(driver_id)
            if driver:
                drivers.append(driver)
        return sorted(drivers, key=lambda d: d.number)

    async def add_year_drivers(self, year: int, driver_ids: list[str]) -> None:
        """Associate drivers with a year."""
        existing = await self._read_index(f"year_{year}")
        combined = list(set(existing + driver_ids))
        await self._write_index(f"year_{year}", combined)

    async def get_by_number(self, number: int) -> Driver | None:
        """Get a driver by their car number."""
        driver_ids = await self._read_index(f"number_{number}")
        if not driver_ids:
            return None
        return await self.get_by_id(driver_ids[0])

    async def search(self, query: str) -> list[Driver]:
        """Search drivers by name or abbreviation."""
        query_lower = query.lower()
        all_drivers = await self.get_all()
        return [
            driver for driver in all_drivers
            if (
                query_lower in driver.id.lower()
                or query_lower in driver.full_name.lower()
                or query_lower in driver.first_name.lower()
                or query_lower in driver.last_name.lower()
            )
        ]
