"""Base file repository implementation."""

import asyncio
import json
import logging
import re
from datetime import timedelta
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)

# Pattern for valid entity IDs (alphanumeric, underscore, hyphen only)
VALID_ENTITY_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


def json_serializer(obj: object) -> str:
    """Custom JSON serializer for non-standard types."""
    if isinstance(obj, timedelta):
        return obj.total_seconds()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def parse_timedelta(value) -> timedelta:
    """Parse a timedelta from various formats."""
    import re

    if isinstance(value, timedelta):
        return value
    if isinstance(value, (int, float)):
        return timedelta(seconds=value)
    if isinstance(value, str):
        # Handle ISO 8601 duration format (e.g., "PT1M32.1S", "PT92.1S", "PT1H2M3.5S")
        if value.startswith("PT"):
            total_seconds = 0.0
            # Extract hours, minutes, seconds
            hours_match = re.search(r"(\d+(?:\.\d+)?)H", value)
            minutes_match = re.search(r"(\d+(?:\.\d+)?)M", value)
            seconds_match = re.search(r"(\d+(?:\.\d+)?)S", value)

            if hours_match:
                total_seconds += float(hours_match.group(1)) * 3600
            if minutes_match:
                total_seconds += float(minutes_match.group(1)) * 60
            if seconds_match:
                total_seconds += float(seconds_match.group(1))

            return timedelta(seconds=total_seconds)
        # Handle HH:MM:SS.mmm format
        if ":" in value:
            parts = value.split(":")
            if len(parts) == 3:
                hours, minutes, seconds = parts
                return timedelta(
                    hours=int(hours),
                    minutes=int(minutes),
                    seconds=float(seconds)
                )
            elif len(parts) == 2:
                minutes, seconds = parts
                return timedelta(minutes=int(minutes), seconds=float(seconds))
    raise ValueError(f"Cannot parse timedelta from: {value}")


def timedelta_decoder(data: dict) -> dict:
    """Decode timedelta fields from various formats."""
    timedelta_fields = [
        "lap_time", "sector_1_time", "sector_2_time", "sector_3_time",
        "pit_in_time", "pit_out_time", "avg_lap_time", "best_lap_time",
        "pit_time", "pit_duration"
    ]
    for field in timedelta_fields:
        if field in data and data[field] is not None:
            try:
                data[field] = parse_timedelta(data[field])
            except (ValueError, TypeError):
                data[field] = None
    return data


class FileRepository(Generic[T]):
    """
    Base class for file-based repository implementations.

    Stores entities as JSON files with optional indexing for
    efficient queries.
    """

    def __init__(self, data_dir: Path, model_class: type[T], entity_name: str):
        """
        Initialize the file repository.

        Args:
            data_dir: Root data directory
            model_class: Pydantic model class for entities
            entity_name: Name for the entity type (used for directory names)
        """
        self._data_dir = data_dir / entity_name
        self._index_dir = data_dir / "indexes" / entity_name
        self._model_class = model_class
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._index_dir.mkdir(parents=True, exist_ok=True)

    def _validate_entity_id(self, entity_id: str) -> None:
        """
        Validate that an entity ID is safe and doesn't contain path traversal.

        Args:
            entity_id: The entity ID to validate

        Raises:
            ValueError: If the entity ID is invalid or unsafe
        """
        if not entity_id:
            raise ValueError("Entity ID cannot be empty")

        # Check for path traversal attempts
        if ".." in entity_id or "/" in entity_id or "\\" in entity_id:
            logger.warning(f"Path traversal attempt detected: {entity_id}")
            raise ValueError("Invalid entity ID: contains path traversal characters")

        # Check against allowed pattern
        if not VALID_ENTITY_ID_PATTERN.match(entity_id):
            logger.warning(f"Invalid entity ID format: {entity_id}")
            raise ValueError("Invalid entity ID: must contain only alphanumeric characters, underscores, and hyphens")

        # Limit length to prevent buffer issues
        if len(entity_id) > 255:
            raise ValueError("Entity ID too long (max 255 characters)")

    def _get_file_path(self, entity_id: str) -> Path:
        """
        Get the file path for an entity with security validation.

        Args:
            entity_id: The entity ID

        Returns:
            Path to the entity file

        Raises:
            ValueError: If the entity ID is invalid
        """
        # Validate the entity ID first
        self._validate_entity_id(entity_id)

        # Use subdirectories for better file system performance
        # e.g., 2024_01_R -> 2024/2024_01_R.json
        parts = entity_id.split("_")
        if len(parts) >= 1 and parts[0].isdigit():
            file_path = self._data_dir / parts[0] / f"{entity_id}.json"
        else:
            file_path = self._data_dir / f"{entity_id}.json"

        # Double-check: ensure the resolved path is within data_dir
        try:
            resolved = file_path.resolve()
            resolved.relative_to(self._data_dir.resolve())
        except ValueError:
            logger.error(f"Path traversal detected after resolution: {entity_id} -> {file_path}")
            raise ValueError("Invalid entity ID: path would escape data directory")

        return file_path

    async def _read_file(self, file_path: Path) -> dict | None:
        """Read and parse a JSON file."""
        if not file_path.exists():
            return None

        def read():
            with open(file_path, "r") as f:
                return json.load(f)

        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, read)
        return timedelta_decoder(data) if data else None

    async def _write_file(self, file_path: Path, data: dict) -> None:
        """Write data to a JSON file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)

        def write():
            with open(file_path, "w") as f:
                json.dump(data, f, default=json_serializer, indent=2)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, write)

    async def _delete_file(self, file_path: Path) -> bool:
        """Delete a file if it exists."""
        if not file_path.exists():
            return False

        def delete():
            file_path.unlink()

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, delete)
        return True

    async def _read_index(self, index_name: str) -> list[str]:
        """Read an index file."""
        index_path = self._index_dir / f"{index_name}.json"
        if not index_path.exists():
            return []

        def read():
            with open(index_path, "r") as f:
                return json.load(f)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, read)

    async def _write_index(self, index_name: str, entity_ids: list[str]) -> None:
        """Write an index file."""
        index_path = self._index_dir / f"{index_name}.json"
        index_path.parent.mkdir(parents=True, exist_ok=True)

        def write():
            with open(index_path, "w") as f:
                json.dump(entity_ids, f)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, write)

    async def _add_to_index(self, index_name: str, entity_id: str) -> None:
        """Add an entity ID to an index."""
        ids = await self._read_index(index_name)
        if entity_id not in ids:
            ids.append(entity_id)
            await self._write_index(index_name, ids)

    async def _list_all_files(self) -> list[Path]:
        """List all entity files."""
        def list_files():
            return list(self._data_dir.rglob("*.json"))

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, list_files)

    async def get_by_id(self, entity_id: str) -> T | None:
        """Get an entity by ID."""
        file_path = self._get_file_path(entity_id)
        data = await self._read_file(file_path)
        if data is None:
            return None
        return self._model_class.model_validate(data)

    async def get_all(self) -> list[T]:
        """Get all entities."""
        files = await self._list_all_files()
        entities = []
        for file_path in files:
            data = await self._read_file(file_path)
            if data:
                entities.append(self._model_class.model_validate(data))
        return entities

    async def add(self, entity: T) -> T:
        """Add an entity."""
        entity_dict = entity.model_dump(mode="json")
        entity_id = entity_dict.get("id")
        file_path = self._get_file_path(entity_id)
        await self._write_file(file_path, entity_dict)
        return entity

    async def add_many(self, entities: list[T]) -> list[T]:
        """Add multiple entities."""
        for entity in entities:
            await self.add(entity)
        return entities

    async def update(self, entity: T) -> T:
        """Update an entity (same as add for file-based)."""
        return await self.add(entity)

    async def delete(self, entity_id: str) -> bool:
        """Delete an entity."""
        file_path = self._get_file_path(entity_id)
        return await self._delete_file(file_path)

    async def exists(self, entity_id: str) -> bool:
        """Check if an entity exists."""
        file_path = self._get_file_path(entity_id)
        return file_path.exists()

    async def count(self) -> int:
        """Count all entities."""
        files = await self._list_all_files()
        return len(files)
