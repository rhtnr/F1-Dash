"""File-based telemetry repository implementation."""

import gzip
import json
from pathlib import Path

from app.domain.models import TelemetryFrame
from app.repositories.interfaces import ITelemetryRepository
from app.repositories.file.base import FileRepository


class FileTelemetryRepository(FileRepository[TelemetryFrame], ITelemetryRepository):
    """
    File-based implementation of telemetry repository.

    Telemetry data is compressed using gzip due to its size.
    Each lap's telemetry is stored in a separate file.
    """

    def __init__(self, data_dir: Path):
        super().__init__(data_dir, TelemetryFrame, "telemetry")

    def _get_file_path(self, entity_id: str) -> Path:
        """Get the file path for telemetry (uses .json.gz extension)."""
        parts = entity_id.split("_")
        if len(parts) >= 3:
            # session_driver_lap format -> session/driver/lap.json.gz
            session_id = "_".join(parts[:-2])
            driver_id = parts[-2]
            return self._data_dir / session_id / driver_id / f"{entity_id}.json.gz"
        return self._data_dir / f"{entity_id}.json.gz"

    async def _read_file(self, file_path: Path) -> dict | None:
        """Read and decompress a gzipped JSON file."""
        if not file_path.exists():
            return None

        import asyncio

        def read():
            with gzip.open(file_path, "rt", encoding="utf-8") as f:
                return json.load(f)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, read)

    async def _write_file(self, file_path: Path, data: dict) -> None:
        """Write data to a gzipped JSON file."""
        import asyncio

        file_path.parent.mkdir(parents=True, exist_ok=True)

        def write():
            with gzip.open(file_path, "wt", encoding="utf-8") as f:
                json.dump(data, f)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, write)

    async def add(self, entity: TelemetryFrame) -> TelemetryFrame:
        """Add telemetry and update indexes."""
        # Create a unique ID if not present
        entity_id = TelemetryFrame.create_id(
            entity.session_id, entity.driver_id, entity.lap_number
        )

        entity_dict = entity.model_dump(mode="json")
        entity_dict["id"] = entity_id

        file_path = self._get_file_path(entity_id)
        await self._write_file(file_path, entity_dict)

        # Update driver index for this session
        driver_key = f"driver_{entity.session_id}_{entity.driver_id}"
        await self._add_to_index(driver_key, str(entity.lap_number))

        return entity

    async def get_by_lap(
        self, session_id: str, driver_id: str, lap_number: int
    ) -> TelemetryFrame | None:
        """Get telemetry for a specific lap."""
        entity_id = TelemetryFrame.create_id(session_id, driver_id, lap_number)
        file_path = self._get_file_path(entity_id)
        data = await self._read_file(file_path)
        if data is None:
            return None
        return TelemetryFrame.model_validate(data)

    async def get_driver_laps(
        self, session_id: str, driver_id: str
    ) -> list[TelemetryFrame]:
        """Get telemetry for all laps by a driver."""
        available_laps = await self.get_available_laps(session_id, driver_id)
        frames = []
        for lap_number in available_laps:
            frame = await self.get_by_lap(session_id, driver_id, lap_number)
            if frame:
                frames.append(frame)
        return sorted(frames, key=lambda f: f.lap_number)

    async def get_fastest_lap_telemetry(
        self, session_id: str, driver_id: str
    ) -> TelemetryFrame | None:
        """Get telemetry for a driver's fastest lap."""
        # This would need lap data to determine fastest
        # For now, return the first available lap
        available = await self.get_available_laps(session_id, driver_id)
        if not available:
            return None
        return await self.get_by_lap(session_id, driver_id, available[0])

    async def has_telemetry(
        self, session_id: str, driver_id: str, lap_number: int
    ) -> bool:
        """Check if telemetry exists for a specific lap."""
        entity_id = TelemetryFrame.create_id(session_id, driver_id, lap_number)
        file_path = self._get_file_path(entity_id)
        return file_path.exists()

    async def get_available_laps(
        self, session_id: str, driver_id: str
    ) -> list[int]:
        """Get list of lap numbers with available telemetry."""
        driver_key = f"driver_{session_id}_{driver_id}"
        lap_strings = await self._read_index(driver_key)
        return sorted([int(lap) for lap in lap_strings if lap.isdigit()])

    # Override base methods that don't apply well to telemetry
    async def get_by_id(self, entity_id: str) -> TelemetryFrame | None:
        """Get telemetry by its full ID."""
        file_path = self._get_file_path(entity_id)
        data = await self._read_file(file_path)
        if data is None:
            return None
        return TelemetryFrame.model_validate(data)

    async def get_all(self) -> list[TelemetryFrame]:
        """Not recommended for telemetry due to size."""
        raise NotImplementedError(
            "get_all() is not supported for telemetry due to data size. "
            "Use get_driver_laps() or get_by_lap() instead."
        )

    async def count(self) -> int:
        """Count telemetry files."""
        import asyncio

        def count_files():
            return len(list(self._data_dir.rglob("*.json.gz")))

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, count_files)
