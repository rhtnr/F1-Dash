"""Tests for repository implementations."""

import pytest

from app.domain.enums import TireCompound
from app.domain.models import Session, Lap, Driver, TireStint


class TestFileSessionRepository:
    """Tests for FileSessionRepository."""

    @pytest.mark.asyncio
    async def test_add_and_get(self, session_repo, sample_session):
        # Add session
        result = await session_repo.add(sample_session)
        assert result.id == sample_session.id

        # Get session
        retrieved = await session_repo.get_by_id(sample_session.id)
        assert retrieved is not None
        assert retrieved.id == sample_session.id
        assert retrieved.year == sample_session.year
        assert retrieved.event_name == sample_session.event_name

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, session_repo):
        result = await session_repo.get_by_id("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_exists(self, session_repo, sample_session):
        # Before adding
        assert await session_repo.exists(sample_session.id) is False

        # After adding
        await session_repo.add(sample_session)
        assert await session_repo.exists(sample_session.id) is True

    @pytest.mark.asyncio
    async def test_get_by_year(self, session_repo, sample_session):
        await session_repo.add(sample_session)

        sessions = await session_repo.get_by_year(2024)
        assert len(sessions) == 1
        assert sessions[0].id == sample_session.id

    @pytest.mark.asyncio
    async def test_get_by_year_empty(self, session_repo):
        sessions = await session_repo.get_by_year(2024)
        assert len(sessions) == 0

    @pytest.mark.asyncio
    async def test_delete(self, session_repo, sample_session):
        await session_repo.add(sample_session)

        # Delete
        result = await session_repo.delete(sample_session.id)
        assert result is True

        # Verify deleted
        assert await session_repo.exists(sample_session.id) is False

    @pytest.mark.asyncio
    async def test_count(self, session_repo, sample_session):
        assert await session_repo.count() == 0

        await session_repo.add(sample_session)
        assert await session_repo.count() == 1


class TestFileLapRepository:
    """Tests for FileLapRepository."""

    @pytest.mark.asyncio
    async def test_add_and_get(self, lap_repo, sample_laps):
        lap = sample_laps[0]

        result = await lap_repo.add(lap)
        assert result.id == lap.id

        retrieved = await lap_repo.get_by_id(lap.id)
        assert retrieved is not None
        assert retrieved.lap_number == lap.lap_number
        assert retrieved.driver_id == lap.driver_id

    @pytest.mark.asyncio
    async def test_add_many(self, lap_repo, sample_laps):
        result = await lap_repo.add_many(sample_laps)
        assert len(result) == len(sample_laps)

        # Verify all laps were saved
        count = await lap_repo.count()
        assert count == len(sample_laps)

    @pytest.mark.asyncio
    async def test_get_by_session(self, lap_repo, sample_laps):
        await lap_repo.add_many(sample_laps)

        laps = await lap_repo.get_by_session(sample_laps[0].session_id)
        assert len(laps) == len(sample_laps)

    @pytest.mark.asyncio
    async def test_get_by_session_and_driver(self, lap_repo, sample_laps):
        await lap_repo.add_many(sample_laps)

        laps = await lap_repo.get_by_session_and_driver(
            sample_laps[0].session_id, "VER"
        )
        assert len(laps) == len(sample_laps)
        assert all(lap.driver_id == "VER" for lap in laps)

    @pytest.mark.asyncio
    async def test_get_by_compound(self, lap_repo, sample_laps):
        await lap_repo.add_many(sample_laps)

        # Sample laps have MEDIUM for laps 1-5, HARD for 6-10
        medium_laps = await lap_repo.get_by_compound(
            sample_laps[0].session_id, TireCompound.MEDIUM
        )
        assert len(medium_laps) == 5

        hard_laps = await lap_repo.get_by_compound(
            sample_laps[0].session_id, TireCompound.HARD
        )
        assert len(hard_laps) == 5

    @pytest.mark.asyncio
    async def test_get_fastest_laps(self, lap_repo, sample_laps):
        await lap_repo.add_many(sample_laps)

        fastest = await lap_repo.get_fastest_laps(
            sample_laps[0].session_id, top_n=3
        )
        assert len(fastest) == 3
        # Should be sorted by lap time
        assert fastest[0].lap_time <= fastest[1].lap_time <= fastest[2].lap_time

    @pytest.mark.asyncio
    async def test_get_valid_laps(self, lap_repo, sample_laps):
        await lap_repo.add_many(sample_laps)

        valid = await lap_repo.get_valid_laps(sample_laps[0].session_id)
        assert len(valid) == len(sample_laps)  # All sample laps are valid

    @pytest.mark.asyncio
    async def test_get_personal_bests(self, lap_repo, sample_laps):
        await lap_repo.add_many(sample_laps)

        bests = await lap_repo.get_personal_bests(sample_laps[0].session_id)
        assert len(bests) == 1  # Only one driver
        assert bests[0].driver_id == "VER"


class TestFileDriverRepository:
    """Tests for FileDriverRepository."""

    @pytest.mark.asyncio
    async def test_add_and_get(self, driver_repo, sample_driver):
        result = await driver_repo.add(sample_driver)
        assert result.id == sample_driver.id

        retrieved = await driver_repo.get_by_id(sample_driver.id)
        assert retrieved is not None
        assert retrieved.full_name == sample_driver.full_name

    @pytest.mark.asyncio
    async def test_get_by_number(self, driver_repo, sample_driver):
        await driver_repo.add(sample_driver)

        retrieved = await driver_repo.get_by_number(1)
        assert retrieved is not None
        assert retrieved.id == "VER"

    @pytest.mark.asyncio
    async def test_search(self, driver_repo, sample_driver):
        await driver_repo.add(sample_driver)

        # Search by name
        results = await driver_repo.search("verstappen")
        assert len(results) == 1
        assert results[0].id == "VER"

        # Search by abbreviation
        results = await driver_repo.search("VER")
        assert len(results) == 1


class TestFileStintRepository:
    """Tests for FileStintRepository."""

    @pytest.mark.asyncio
    async def test_add_and_get(self, stint_repo, sample_stint):
        result = await stint_repo.add(sample_stint)
        assert result.id == sample_stint.id

        retrieved = await stint_repo.get_by_id(sample_stint.id)
        assert retrieved is not None
        assert retrieved.compound == sample_stint.compound

    @pytest.mark.asyncio
    async def test_get_by_session(self, stint_repo, sample_stint):
        await stint_repo.add(sample_stint)

        stints = await stint_repo.get_by_session(sample_stint.session_id)
        assert len(stints) == 1

    @pytest.mark.asyncio
    async def test_get_by_driver(self, stint_repo, sample_stint):
        await stint_repo.add(sample_stint)

        stints = await stint_repo.get_by_driver(
            sample_stint.session_id, sample_stint.driver_id
        )
        assert len(stints) == 1
        assert stints[0].driver_id == "VER"

    @pytest.mark.asyncio
    async def test_get_by_compound(self, stint_repo, sample_stint):
        await stint_repo.add(sample_stint)

        stints = await stint_repo.get_by_compound(
            sample_stint.session_id, TireCompound.MEDIUM
        )
        assert len(stints) == 1
