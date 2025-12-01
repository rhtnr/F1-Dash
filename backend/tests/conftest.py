"""Pytest configuration and fixtures."""

import asyncio
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.config import Settings
from app.main import create_app
from app.domain.enums import SessionType, TireCompound, TrackStatus
from app.domain.models import Driver, Lap, Session, TireStint
from app.repositories.file import (
    FileSessionRepository,
    FileLapRepository,
    FileDriverRepository,
    FileStintRepository,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_data_dir() -> Generator[Path, None, None]:
    """Create a temporary data directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_settings(temp_data_dir: Path) -> Settings:
    """Create test settings with temporary directories."""
    return Settings(
        debug=True,
        data_dir=temp_data_dir,
        fastf1_cache_dir=temp_data_dir / "cache",
        storage_backend="file",
    )


@pytest.fixture
def app(test_settings: Settings):
    """Create test FastAPI application."""
    from app.config import get_settings

    # Override settings
    def override_settings():
        return test_settings

    application = create_app()
    application.dependency_overrides[get_settings] = override_settings
    return application


@pytest.fixture
def client(app) -> Generator[TestClient, None, None]:
    """Create test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


# Sample Data Fixtures

@pytest.fixture
def sample_session() -> Session:
    """Create a sample session for testing."""
    return Session(
        id="2024_01_R",
        year=2024,
        round_number=1,
        event_name="Bahrain Grand Prix",
        country="Bahrain",
        location="Sakhir",
        circuit_name="Bahrain International Circuit",
        circuit_short_name="BHR",
        session_type=SessionType.RACE,
        session_date=datetime(2024, 3, 2, 15, 0, 0),
        total_laps=57,
    )


@pytest.fixture
def sample_driver() -> Driver:
    """Create a sample driver for testing."""
    return Driver(
        id="VER",
        number=1,
        full_name="Max Verstappen",
        first_name="Max",
        last_name="Verstappen",
        team_id="red_bull_racing",
        team_name="Red Bull Racing",
        team_color="#3671C6",
        country_code="NED",
    )


@pytest.fixture
def sample_laps(sample_session: Session) -> list[Lap]:
    """Create sample laps for testing."""
    laps = []
    base_time = timedelta(minutes=1, seconds=32)

    for lap_num in range(1, 11):
        # Add some variation
        lap_time = base_time + timedelta(milliseconds=lap_num * 100)

        lap = Lap(
            id=f"{sample_session.id}_VER_{lap_num:03d}",
            session_id=sample_session.id,
            driver_id="VER",
            lap_number=lap_num,
            lap_time=lap_time,
            sector_1_time=timedelta(seconds=28, milliseconds=lap_num * 30),
            sector_2_time=timedelta(seconds=35, milliseconds=lap_num * 40),
            sector_3_time=timedelta(seconds=29, milliseconds=lap_num * 30),
            compound=TireCompound.MEDIUM if lap_num <= 5 else TireCompound.HARD,
            tyre_life=lap_num if lap_num <= 5 else lap_num - 5,
            stint=1 if lap_num <= 5 else 2,
            is_fresh_tyre=lap_num == 1 or lap_num == 6,
            position=1,
            track_status=TrackStatus.GREEN,
            is_personal_best=lap_num == 1,
            is_accurate=True,
        )
        laps.append(lap)

    return laps


@pytest.fixture
def sample_stint() -> TireStint:
    """Create a sample stint for testing."""
    return TireStint(
        id="2024_01_R_VER_stint_1",
        session_id="2024_01_R",
        driver_id="VER",
        stint_number=1,
        compound=TireCompound.MEDIUM,
        is_fresh=True,
        start_lap=1,
        end_lap=20,
        avg_lap_time=timedelta(minutes=1, seconds=33, milliseconds=500),
        degradation_rate=0.05,
    )


# Repository Fixtures

@pytest.fixture
def session_repo(temp_data_dir: Path) -> FileSessionRepository:
    """Create session repository for testing."""
    return FileSessionRepository(temp_data_dir)


@pytest.fixture
def lap_repo(temp_data_dir: Path) -> FileLapRepository:
    """Create lap repository for testing."""
    return FileLapRepository(temp_data_dir)


@pytest.fixture
def driver_repo(temp_data_dir: Path) -> FileDriverRepository:
    """Create driver repository for testing."""
    return FileDriverRepository(temp_data_dir)


@pytest.fixture
def stint_repo(temp_data_dir: Path) -> FileStintRepository:
    """Create stint repository for testing."""
    return FileStintRepository(temp_data_dir)
