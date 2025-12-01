"""Tests for service layer."""

import pytest

from app.domain.enums import TireCompound
from app.services import SessionService, LapService, StrategyService


class TestSessionService:
    """Tests for SessionService."""

    @pytest.mark.asyncio
    async def test_get_session(self, session_repo, sample_session):
        service = SessionService(session_repo)

        # Save session first
        await session_repo.add(sample_session)

        # Get via service
        result = await service.get_session(sample_session.id)
        assert result is not None
        assert result.id == sample_session.id

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, session_repo):
        service = SessionService(session_repo)

        result = await service.get_session("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_sessions_by_year(self, session_repo, sample_session):
        service = SessionService(session_repo)
        await session_repo.add(sample_session)

        sessions = await service.get_sessions_by_year(2024)
        assert len(sessions) == 1

    @pytest.mark.asyncio
    async def test_session_exists(self, session_repo, sample_session):
        service = SessionService(session_repo)

        assert await service.session_exists(sample_session.id) is False

        await session_repo.add(sample_session)
        assert await service.session_exists(sample_session.id) is True


class TestLapService:
    """Tests for LapService."""

    @pytest.mark.asyncio
    async def test_get_session_laps(self, lap_repo, sample_laps):
        service = LapService(lap_repo)
        await lap_repo.add_many(sample_laps)

        laps = await service.get_session_laps(sample_laps[0].session_id)
        assert len(laps) == len(sample_laps)

    @pytest.mark.asyncio
    async def test_get_driver_laps(self, lap_repo, sample_laps):
        service = LapService(lap_repo)
        await lap_repo.add_many(sample_laps)

        laps = await service.get_driver_laps(
            sample_laps[0].session_id, "VER"
        )
        assert len(laps) == len(sample_laps)

    @pytest.mark.asyncio
    async def test_get_fastest_laps(self, lap_repo, sample_laps):
        service = LapService(lap_repo)
        await lap_repo.add_many(sample_laps)

        laps = await service.get_fastest_laps(
            sample_laps[0].session_id, top_n=5
        )
        assert len(laps) == 5

    @pytest.mark.asyncio
    async def test_get_lap_time_distribution(self, lap_repo, sample_laps):
        service = LapService(lap_repo)
        await lap_repo.add_many(sample_laps)

        distribution = await service.get_lap_time_distribution(
            sample_laps[0].session_id
        )
        assert "VER" in distribution
        assert len(distribution["VER"]) == len(sample_laps)

    @pytest.mark.asyncio
    async def test_get_compound_performance(self, lap_repo, sample_laps):
        service = LapService(lap_repo)
        await lap_repo.add_many(sample_laps)

        performance = await service.get_compound_performance(
            sample_laps[0].session_id
        )
        assert "MEDIUM" in performance
        assert "HARD" in performance
        assert performance["MEDIUM"]["count"] == 5
        assert performance["HARD"]["count"] == 5

    @pytest.mark.asyncio
    async def test_compare_drivers(self, lap_repo, sample_laps):
        service = LapService(lap_repo)
        await lap_repo.add_many(sample_laps)

        # Compare VER with a non-existent driver
        comparison = await service.compare_drivers(
            sample_laps[0].session_id, "VER", "HAM"
        )
        assert "VER" in comparison
        assert comparison["VER"] is not None
        assert "HAM" in comparison
        assert comparison["HAM"] is None  # No data for HAM


class TestStrategyService:
    """Tests for StrategyService."""

    @pytest.mark.asyncio
    async def test_get_session_stints(self, stint_repo, lap_repo, sample_stint):
        service = StrategyService(stint_repo, lap_repo)
        await stint_repo.add(sample_stint)

        stints = await service.get_session_stints(sample_stint.session_id)
        assert len(stints) == 1

    @pytest.mark.asyncio
    async def test_get_driver_stints(self, stint_repo, lap_repo, sample_stint):
        service = StrategyService(stint_repo, lap_repo)
        await stint_repo.add(sample_stint)

        stints = await service.get_driver_stints(
            sample_stint.session_id, "VER"
        )
        assert len(stints) == 1
        assert stints[0].driver_id == "VER"

    @pytest.mark.asyncio
    async def test_get_strategy_summary(self, stint_repo, lap_repo, sample_stint):
        service = StrategyService(stint_repo, lap_repo)
        await stint_repo.add(sample_stint)

        summaries = await service.get_strategy_summary(sample_stint.session_id)
        assert len(summaries) == 1
        assert summaries[0]["driver_id"] == "VER"
        assert summaries[0]["total_stints"] == 1
        assert "MEDIUM" in summaries[0]["compounds"]
