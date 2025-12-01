# F1-Dash - Architecture Design

## Executive Summary

F1-Dash is a Python-backed D3.js web application for F1 enthusiasts to visualize lap times, tire strategies, driver/team performance, telemetry, and race analytics with ML-powered predictions. Built with FastAPI, following SOLID principles, with a pluggable storage layer.

---

## Research Findings

### FastF1 Library Capabilities

**Data Available (2018+):**
| Category | Data Points |
|----------|-------------|
| **Lap Timing** | LapTime, Sector1/2/3Time, SpeedI1/I2/FL/ST, LapNumber, Position |
| **Tire Data** | Compound (SOFT/MEDIUM/HARD/INTER/WET), TyreLife, FreshTyre, Stint |
| **Telemetry** | Speed, RPM, nGear, Throttle%, Brake, DRS, X/Y/Z position |
| **Session** | Weather, TrackStatus, RaceControlMessages, SessionResults |
| **Driver/Team** | Names, Numbers, TeamColors, Grid/Finish positions, Points |

**Key Classes:**
- `Session` - Entry point via `fastf1.get_session(year, circuit, session_type)`
- `Laps` - DataFrame with filtering: `pick_drivers()`, `pick_compounds()`, `pick_fastest()`
- `Telemetry` - Time-series car data with `add_distance()`, `add_driver_ahead()`

**Caching:** Built-in cache system (~50-100MB per session)

### Reference Features (GP Tempo / F1 Tempo / TracingInsights)

Must-have features for parity:
1. **Lap Time Analysis** - Scatter plots, box plots, lap-by-lap progression
2. **Tire Strategy Visualization** - Stint bars with compound colors, pit stop timing
3. **Telemetry Overlays** - Speed traces, throttle/brake, gear shifts by track position
4. **Driver Comparisons** - Head-to-head lap times, sector comparisons
5. **Race Progression** - Position changes over laps, gap analysis
6. **Session Selection** - Year/Event/Session dropdowns
7. **Stint Analysis** - Tire degradation curves, fuel-corrected pace

### Framework Selection: FastAPI

| Criteria | FastAPI | Flask | Django |
|----------|---------|-------|--------|
| **Async Support** | Native | Extension | Limited |
| **Performance** | ~9000 req/s | ~3000 req/s | ~3000 req/s |
| **Type Hints** | Built-in validation | Manual | Manual |
| **API Docs** | Auto OpenAPI/Swagger | Manual | DRF needed |
| **Learning Curve** | Moderate | Low | High |
| **Best For** | REST APIs, Data apps | Prototypes | Full-stack CMS |

**Decision: FastAPI** - Best fit for data-intensive REST API serving JSON to D3.js frontend.

### D3.js Best Practices

- **DOM Management**: Minimize elements, use enter/update/exit pattern
- **Large Datasets**: Use Canvas over SVG for >1000 elements
- **Performance**: Virtual scrolling, lazy loading, requestAnimationFrame
- **Events**: Delegation at container level, debounce updates
- **Memory**: Clean up unused references, use Web Workers for heavy computation

---

## Application Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (D3.js)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ LapTimes │ │ Strategy │ │Telemetry │ │ Race Progression │   │
│  │  Chart   │ │  Chart   │ │  Chart   │ │     Chart        │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────────┬─────────┘   │
│       └────────────┴────────────┴────────────────┘              │
│                           │ REST API                            │
└───────────────────────────┼─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    API Layer (Routers)                   │   │
│  │  /sessions  /laps  /telemetry  /strategy  /standings    │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                            │                                    │
│  ┌─────────────────────────▼───────────────────────────────┐   │
│  │                   Service Layer                          │   │
│  │  SessionService  LapService  TelemetryService  etc.     │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                            │                                    │
│  ┌─────────────────────────▼───────────────────────────────┐   │
│  │              Domain Models (Pydantic)                    │   │
│  │  Session  Lap  Driver  Team  TireStint  Telemetry       │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                            │                                    │
│  ┌─────────────────────────▼───────────────────────────────┐   │
│  │              Repository Layer (Abstract)                 │   │
│  │  ISessionRepo  ILapRepo  IDriverRepo  ITeamRepo         │   │
│  └──────────┬──────────────────────────────┬───────────────┘   │
│             │                              │                    │
│  ┌──────────▼──────────┐      ┌───────────▼────────────┐       │
│  │  FileRepository     │      │  DynamoDBRepository    │       │
│  │  (JSON/Parquet)     │      │  (Future)              │       │
│  └──────────┬──────────┘      └───────────┬────────────┘       │
└─────────────┼─────────────────────────────┼─────────────────────┘
              │                             │
              ▼                             ▼
        ┌──────────┐               ┌──────────────┐
        │  ./data  │               │ AWS DynamoDB │
        │  (local) │               │   (cloud)    │
        └──────────┘               └──────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    DATA INGESTION                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                FastF1 Data Fetcher                       │   │
│  │  - Scheduled jobs to fetch new session data              │   │
│  │  - Transform FastF1 DataFrames to domain models          │   │
│  │  - Store via Repository interface                        │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
f1-dash/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Settings (Pydantic BaseSettings)
│   │   ├── dependencies.py         # DI container
│   │   │
│   │   ├── api/                    # API Layer
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py       # Aggregates all routers
│   │   │   │   ├── sessions.py     # /sessions endpoints
│   │   │   │   ├── laps.py         # /laps endpoints
│   │   │   │   ├── telemetry.py    # /telemetry endpoints
│   │   │   │   ├── strategy.py     # /strategy endpoints
│   │   │   │   ├── drivers.py      # /drivers endpoints
│   │   │   │   ├── teams.py        # /teams endpoints
│   │   │   │   └── standings.py    # /standings endpoints
│   │   │   └── schemas/            # Request/Response schemas
│   │   │       ├── __init__.py
│   │   │       ├── session.py
│   │   │       ├── lap.py
│   │   │       ├── telemetry.py
│   │   │       └── ...
│   │   │
│   │   ├── domain/                 # Domain Models
│   │   │   ├── __init__.py
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── session.py
│   │   │   │   ├── lap.py
│   │   │   │   ├── driver.py
│   │   │   │   ├── team.py
│   │   │   │   ├── tire.py
│   │   │   │   ├── telemetry.py
│   │   │   │   └── weather.py
│   │   │   └── enums/
│   │   │       ├── __init__.py
│   │   │       ├── compound.py
│   │   │       ├── session_type.py
│   │   │       └── track_status.py
│   │   │
│   │   ├── services/               # Business Logic
│   │   │   ├── __init__.py
│   │   │   ├── session_service.py
│   │   │   ├── lap_service.py
│   │   │   ├── telemetry_service.py
│   │   │   ├── strategy_service.py
│   │   │   └── standings_service.py
│   │   │
│   │   ├── repositories/           # Data Access Layer
│   │   │   ├── __init__.py
│   │   │   ├── interfaces/         # Abstract interfaces
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py         # IRepository base
│   │   │   │   ├── session_repo.py
│   │   │   │   ├── lap_repo.py
│   │   │   │   └── ...
│   │   │   ├── file/               # File-based implementation
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── session_repo.py
│   │   │   │   ├── lap_repo.py
│   │   │   │   └── ...
│   │   │   └── dynamodb/           # Future DynamoDB implementation
│   │   │       ├── __init__.py
│   │   │       └── ...
│   │   │
│   │   └── ingestion/              # Data fetching from FastF1
│   │       ├── __init__.py
│   │       ├── fetcher.py          # FastF1 data fetcher
│   │       ├── transformers.py     # DataFrame to domain model
│   │       └── scheduler.py        # Background job scheduling
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── unit/
│   │   ├── integration/
│   │   └── fixtures/
│   │
│   ├── data/                       # Local file storage
│   │   ├── sessions/
│   │   ├── laps/
│   │   ├── telemetry/
│   │   └── cache/                  # FastF1 cache
│   │
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── index.html
│   ├── css/
│   │   ├── main.css
│   │   └── charts.css
│   ├── js/
│   │   ├── app.js                  # Main application
│   │   ├── api/
│   │   │   └── client.js           # API client
│   │   ├── charts/
│   │   │   ├── base-chart.js       # Base chart class
│   │   │   ├── lap-times.js
│   │   │   ├── tire-strategy.js
│   │   │   ├── telemetry.js
│   │   │   ├── race-progression.js
│   │   │   └── driver-comparison.js
│   │   ├── components/
│   │   │   ├── session-selector.js
│   │   │   ├── driver-filter.js
│   │   │   └── tooltip.js
│   │   └── utils/
│   │       ├── colors.js           # Team/compound colors
│   │       ├── formatters.js       # Time formatting
│   │       └── scales.js           # D3 scale utilities
│   └── assets/
│       └── ...
│
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
└── ARCHITECTURE.md
```

---

## SOLID Principles Implementation

### Single Responsibility Principle (SRP)

Each class has one reason to change:

```python
# services/lap_service.py - Only handles lap business logic
class LapService:
    def __init__(self, lap_repo: ILapRepository):
        self._lap_repo = lap_repo

    def get_fastest_laps(self, session_id: str, top_n: int = 10) -> list[Lap]:
        laps = self._lap_repo.get_by_session(session_id)
        return sorted(laps, key=lambda l: l.lap_time)[:top_n]

    def get_driver_laps(self, session_id: str, driver_id: str) -> list[Lap]:
        return self._lap_repo.get_by_session_and_driver(session_id, driver_id)
```

### Open/Closed Principle (OCP)

Open for extension, closed for modification via abstract interfaces:

```python
# repositories/interfaces/base.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar('T')
ID = TypeVar('ID')

class IRepository(ABC, Generic[T, ID]):
    @abstractmethod
    async def get_by_id(self, id: ID) -> T | None:
        pass

    @abstractmethod
    async def get_all(self) -> list[T]:
        pass

    @abstractmethod
    async def add(self, entity: T) -> T:
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        pass

    @abstractmethod
    async def delete(self, id: ID) -> bool:
        pass
```

### Liskov Substitution Principle (LSP)

All repository implementations are interchangeable:

```python
# Both implementations can be used wherever ILapRepository is expected
class FileLapRepository(ILapRepository):
    async def get_by_id(self, id: str) -> Lap | None:
        # File-based implementation
        ...

class DynamoDBLapRepository(ILapRepository):
    async def get_by_id(self, id: str) -> Lap | None:
        # DynamoDB implementation
        ...
```

### Interface Segregation Principle (ISP)

Specific interfaces for specific needs:

```python
# repositories/interfaces/lap_repo.py
class ILapRepository(IRepository[Lap, str]):
    @abstractmethod
    async def get_by_session(self, session_id: str) -> list[Lap]:
        pass

    @abstractmethod
    async def get_by_session_and_driver(
        self, session_id: str, driver_id: str
    ) -> list[Lap]:
        pass

    @abstractmethod
    async def get_by_compound(
        self, session_id: str, compound: TireCompound
    ) -> list[Lap]:
        pass
```

### Dependency Inversion Principle (DIP)

High-level modules depend on abstractions:

```python
# dependencies.py
from functools import lru_cache
from app.config import Settings
from app.repositories.interfaces import ILapRepository, ISessionRepository
from app.repositories.file import FileLapRepository, FileSessionRepository
from app.services import LapService, SessionService

@lru_cache
def get_settings() -> Settings:
    return Settings()

def get_lap_repository(settings: Settings = Depends(get_settings)) -> ILapRepository:
    # Easy to swap implementation based on config
    if settings.storage_backend == "dynamodb":
        return DynamoDBLapRepository(settings.dynamodb_config)
    return FileLapRepository(settings.data_dir)

def get_lap_service(
    lap_repo: ILapRepository = Depends(get_lap_repository)
) -> LapService:
    return LapService(lap_repo)
```

---

## Domain Models

```python
# domain/models/lap.py
from datetime import timedelta
from pydantic import BaseModel, Field
from app.domain.enums import TireCompound, TrackStatus

class Lap(BaseModel):
    id: str = Field(..., description="Unique lap identifier")
    session_id: str
    driver_id: str
    lap_number: int
    lap_time: timedelta | None
    sector_1_time: timedelta | None
    sector_2_time: timedelta | None
    sector_3_time: timedelta | None
    compound: TireCompound
    tyre_life: int
    stint: int
    is_fresh_tyre: bool
    is_personal_best: bool
    is_accurate: bool
    position: int | None
    speed_trap: float | None  # km/h
    speed_i1: float | None
    speed_i2: float | None
    speed_fl: float | None
    track_status: TrackStatus
    deleted: bool = False
    deleted_reason: str | None = None

    class Config:
        frozen = True  # Immutable domain object


# domain/models/tire_stint.py
class TireStint(BaseModel):
    stint_number: int
    driver_id: str
    session_id: str
    compound: TireCompound
    start_lap: int
    end_lap: int
    total_laps: int
    avg_lap_time: timedelta | None
    degradation_rate: float | None  # seconds per lap


# domain/models/telemetry.py
class TelemetryPoint(BaseModel):
    timestamp: datetime
    distance: float  # meters from start
    speed: float  # km/h
    rpm: int
    gear: int
    throttle: float  # 0-100%
    brake: bool
    drs: int  # 0-14 various states
    x: float
    y: float
    z: float


# domain/enums/compound.py
from enum import Enum

class TireCompound(str, Enum):
    SOFT = "SOFT"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    INTERMEDIATE = "INTERMEDIATE"
    WET = "WET"
    UNKNOWN = "UNKNOWN"
```

---

## Repository Pattern - File Implementation

```python
# repositories/file/base.py
import json
import asyncio
from pathlib import Path
from typing import TypeVar, Generic
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class FileRepository(Generic[T]):
    def __init__(self, data_dir: Path, model_class: type[T]):
        self._data_dir = data_dir
        self._model_class = model_class
        self._data_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, id: str) -> Path:
        return self._data_dir / f"{id}.json"

    async def get_by_id(self, id: str) -> T | None:
        file_path = self._get_file_path(id)
        if not file_path.exists():
            return None

        def read_file():
            with open(file_path, 'r') as f:
                return json.load(f)

        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, read_file)
        return self._model_class.model_validate(data)

    async def add(self, entity: T) -> T:
        file_path = self._get_file_path(entity.id)

        def write_file():
            with open(file_path, 'w') as f:
                json.dump(entity.model_dump(mode='json'), f, default=str)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, write_file)
        return entity


# repositories/file/lap_repo.py
from pathlib import Path
from app.repositories.interfaces import ILapRepository
from app.domain.models import Lap
from app.domain.enums import TireCompound

class FileLapRepository(ILapRepository):
    def __init__(self, data_dir: Path):
        self._data_dir = data_dir / "laps"
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._index_dir = data_dir / "indexes" / "laps"
        self._index_dir.mkdir(parents=True, exist_ok=True)

    async def get_by_session(self, session_id: str) -> list[Lap]:
        # Use session index file for efficient lookup
        index_file = self._index_dir / f"session_{session_id}.json"
        if not index_file.exists():
            return []

        with open(index_file, 'r') as f:
            lap_ids = json.load(f)

        laps = []
        for lap_id in lap_ids:
            lap = await self.get_by_id(lap_id)
            if lap:
                laps.append(lap)
        return laps

    async def get_by_session_and_driver(
        self, session_id: str, driver_id: str
    ) -> list[Lap]:
        all_laps = await self.get_by_session(session_id)
        return [lap for lap in all_laps if lap.driver_id == driver_id]

    async def get_by_compound(
        self, session_id: str, compound: TireCompound
    ) -> list[Lap]:
        all_laps = await self.get_by_session(session_id)
        return [lap for lap in all_laps if lap.compound == compound]
```

---

## API Layer

```python
# api/v1/laps.py
from fastapi import APIRouter, Depends, Query, HTTPException
from app.services import LapService
from app.dependencies import get_lap_service
from app.api.schemas.lap import LapResponse, LapListResponse

router = APIRouter(prefix="/laps", tags=["Laps"])

@router.get("/{session_id}", response_model=LapListResponse)
async def get_session_laps(
    session_id: str,
    driver_id: str | None = Query(None, description="Filter by driver"),
    compound: str | None = Query(None, description="Filter by tire compound"),
    lap_service: LapService = Depends(get_lap_service)
):
    """Get all laps for a session with optional filters."""
    if driver_id:
        laps = await lap_service.get_driver_laps(session_id, driver_id)
    else:
        laps = await lap_service.get_session_laps(session_id)

    if compound:
        laps = [l for l in laps if l.compound.value == compound.upper()]

    return LapListResponse(
        session_id=session_id,
        count=len(laps),
        laps=[LapResponse.from_domain(lap) for lap in laps]
    )

@router.get("/{session_id}/fastest", response_model=LapListResponse)
async def get_fastest_laps(
    session_id: str,
    top_n: int = Query(10, ge=1, le=100),
    lap_service: LapService = Depends(get_lap_service)
):
    """Get the fastest laps in a session."""
    laps = await lap_service.get_fastest_laps(session_id, top_n)
    return LapListResponse(
        session_id=session_id,
        count=len(laps),
        laps=[LapResponse.from_domain(lap) for lap in laps]
    )


# api/v1/strategy.py
@router.get("/{session_id}/stints", response_model=StintListResponse)
async def get_tire_stints(
    session_id: str,
    driver_id: str | None = Query(None),
    strategy_service: StrategyService = Depends(get_strategy_service)
):
    """Get tire stint data for strategy visualization."""
    stints = await strategy_service.get_stints(session_id, driver_id)
    return StintListResponse(stints=stints)
```

---

## FastF1 Data Ingestion

```python
# ingestion/fetcher.py
import fastf1
from pathlib import Path
from app.domain.models import Session, Lap, TelemetryPoint
from app.domain.enums import TireCompound, SessionType

class FastF1Fetcher:
    def __init__(self, cache_dir: Path):
        self._cache_dir = cache_dir
        fastf1.Cache.enable_cache(str(cache_dir))

    async def fetch_session(
        self, year: int, event: str | int, session_type: str
    ) -> tuple[Session, list[Lap]]:
        """Fetch session and lap data from FastF1."""
        ff1_session = fastf1.get_session(year, event, session_type)
        ff1_session.load(laps=True, telemetry=False, weather=True, messages=True)

        # Transform to domain models
        session = self._transform_session(ff1_session)
        laps = self._transform_laps(ff1_session, session.id)

        return session, laps

    async def fetch_telemetry(
        self, year: int, event: str | int, session_type: str,
        driver: str, lap_number: int
    ) -> list[TelemetryPoint]:
        """Fetch telemetry for a specific lap."""
        ff1_session = fastf1.get_session(year, event, session_type)
        ff1_session.load(laps=True, telemetry=True)

        lap = ff1_session.laps.pick_drivers(driver).pick_laps(lap_number).iloc[0]
        telemetry = lap.get_car_data().add_distance()

        return [
            TelemetryPoint(
                timestamp=row['Date'],
                distance=row['Distance'],
                speed=row['Speed'],
                rpm=row['RPM'],
                gear=row['nGear'],
                throttle=row['Throttle'],
                brake=row['Brake'],
                drs=row['DRS'],
                x=0, y=0, z=0  # Position data separate
            )
            for _, row in telemetry.iterrows()
        ]

    def _transform_laps(self, ff1_session, session_id: str) -> list[Lap]:
        laps = []
        for _, row in ff1_session.laps.iterrows():
            lap = Lap(
                id=f"{session_id}_{row['Driver']}_{row['LapNumber']}",
                session_id=session_id,
                driver_id=row['Driver'],
                lap_number=int(row['LapNumber']),
                lap_time=row['LapTime'] if pd.notna(row['LapTime']) else None,
                sector_1_time=row['Sector1Time'] if pd.notna(row['Sector1Time']) else None,
                sector_2_time=row['Sector2Time'] if pd.notna(row['Sector2Time']) else None,
                sector_3_time=row['Sector3Time'] if pd.notna(row['Sector3Time']) else None,
                compound=TireCompound(row['Compound']) if row['Compound'] else TireCompound.UNKNOWN,
                tyre_life=int(row['TyreLife']) if pd.notna(row['TyreLife']) else 0,
                stint=int(row['Stint']) if pd.notna(row['Stint']) else 1,
                is_fresh_tyre=bool(row['FreshTyre']),
                is_personal_best=bool(row['IsPersonalBest']),
                is_accurate=bool(row['IsAccurate']),
                position=int(row['Position']) if pd.notna(row['Position']) else None,
                speed_trap=row['SpeedST'] if pd.notna(row['SpeedST']) else None,
                speed_i1=row['SpeedI1'] if pd.notna(row['SpeedI1']) else None,
                speed_i2=row['SpeedI2'] if pd.notna(row['SpeedI2']) else None,
                speed_fl=row['SpeedFL'] if pd.notna(row['SpeedFL']) else None,
                track_status=TrackStatus.GREEN,  # Parse from actual data
                deleted=bool(row['Deleted']),
                deleted_reason=row['DeletedReason'] if pd.notna(row['DeletedReason']) else None
            )
            laps.append(lap)
        return laps
```

---

## Frontend D3.js Architecture

```javascript
// js/charts/base-chart.js
class BaseChart {
    constructor(container, options = {}) {
        this.container = d3.select(container);
        this.options = {
            margin: { top: 20, right: 30, bottom: 40, left: 50 },
            ...options
        };
        this.svg = null;
        this.tooltip = null;
    }

    init() {
        const { width, height } = this.container.node().getBoundingClientRect();
        this.width = width - this.options.margin.left - this.options.margin.right;
        this.height = height - this.options.margin.top - this.options.margin.bottom;

        this.svg = this.container
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .append('g')
            .attr('transform', `translate(${this.options.margin.left},${this.options.margin.top})`);

        this.tooltip = d3.select('body')
            .append('div')
            .attr('class', 'tooltip')
            .style('opacity', 0);

        return this;
    }

    // Template method pattern - subclasses implement these
    setupScales(data) { throw new Error('Not implemented'); }
    setupAxes() { throw new Error('Not implemented'); }
    render(data) { throw new Error('Not implemented'); }

    update(data) {
        this.setupScales(data);
        this.setupAxes();
        this.render(data);
    }

    destroy() {
        this.svg?.remove();
        this.tooltip?.remove();
    }
}


// js/charts/lap-times.js
class LapTimesChart extends BaseChart {
    constructor(container, options = {}) {
        super(container, {
            ...options,
            yDomain: 'auto'  // or [minTime, maxTime]
        });
        this.xScale = null;
        this.yScale = null;
        this.colorScale = null;
    }

    setupScales(data) {
        // X: Lap number
        this.xScale = d3.scaleLinear()
            .domain([1, d3.max(data, d => d.lapNumber)])
            .range([0, this.width]);

        // Y: Lap time in seconds
        const times = data.map(d => d.lapTimeSeconds).filter(t => t != null);
        this.yScale = d3.scaleLinear()
            .domain([d3.min(times) * 0.98, d3.max(times) * 1.02])
            .range([this.height, 0]);

        // Color by driver
        this.colorScale = d3.scaleOrdinal()
            .domain([...new Set(data.map(d => d.driverId))])
            .range(d3.schemeTableau10);
    }

    setupAxes() {
        // X Axis
        this.svg.selectAll('.x-axis').remove();
        this.svg.append('g')
            .attr('class', 'x-axis')
            .attr('transform', `translate(0,${this.height})`)
            .call(d3.axisBottom(this.xScale).ticks(10));

        // Y Axis
        this.svg.selectAll('.y-axis').remove();
        this.svg.append('g')
            .attr('class', 'y-axis')
            .call(d3.axisLeft(this.yScale).tickFormat(formatLapTime));
    }

    render(data) {
        // Group by driver
        const grouped = d3.group(data, d => d.driverId);

        // Line generator
        const line = d3.line()
            .defined(d => d.lapTimeSeconds != null)
            .x(d => this.xScale(d.lapNumber))
            .y(d => this.yScale(d.lapTimeSeconds));

        // Enter-update-exit pattern for lines
        const lines = this.svg.selectAll('.driver-line')
            .data(grouped, d => d[0]);

        lines.exit().remove();

        lines.enter()
            .append('path')
            .attr('class', 'driver-line')
            .merge(lines)
            .attr('fill', 'none')
            .attr('stroke', d => this.colorScale(d[0]))
            .attr('stroke-width', 2)
            .attr('d', d => line(d[1]));

        // Points for hover
        const points = this.svg.selectAll('.lap-point')
            .data(data.filter(d => d.lapTimeSeconds != null));

        points.exit().remove();

        points.enter()
            .append('circle')
            .attr('class', 'lap-point')
            .merge(points)
            .attr('cx', d => this.xScale(d.lapNumber))
            .attr('cy', d => this.yScale(d.lapTimeSeconds))
            .attr('r', 4)
            .attr('fill', d => this.colorScale(d.driverId))
            .on('mouseenter', (event, d) => this.showTooltip(event, d))
            .on('mouseleave', () => this.hideTooltip());
    }

    showTooltip(event, d) {
        this.tooltip
            .style('opacity', 1)
            .html(`
                <strong>${d.driverId}</strong><br>
                Lap ${d.lapNumber}: ${formatLapTime(d.lapTimeSeconds)}<br>
                Tire: ${d.compound}
            `)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 10) + 'px');
    }

    hideTooltip() {
        this.tooltip.style('opacity', 0);
    }
}


// js/charts/tire-strategy.js
class TireStrategyChart extends BaseChart {
    constructor(container, options = {}) {
        super(container, options);
        this.compoundColors = {
            SOFT: '#FF3333',
            MEDIUM: '#FCD500',
            HARD: '#EBEBEB',
            INTERMEDIATE: '#43B02A',
            WET: '#0067AD',
            UNKNOWN: '#888888'
        };
    }

    setupScales(data) {
        const drivers = [...new Set(data.map(d => d.driverId))];
        const maxLap = d3.max(data, d => d.endLap);

        this.xScale = d3.scaleLinear()
            .domain([0, maxLap])
            .range([0, this.width]);

        this.yScale = d3.scaleBand()
            .domain(drivers)
            .range([0, this.height])
            .padding(0.2);
    }

    render(data) {
        // Group stints by driver
        const grouped = d3.group(data, d => d.driverId);

        // Draw stint bars
        const stints = this.svg.selectAll('.stint')
            .data(data, d => `${d.driverId}-${d.stintNumber}`);

        stints.exit().remove();

        stints.enter()
            .append('rect')
            .attr('class', 'stint')
            .merge(stints)
            .attr('x', d => this.xScale(d.startLap))
            .attr('y', d => this.yScale(d.driverId))
            .attr('width', d => this.xScale(d.endLap) - this.xScale(d.startLap))
            .attr('height', this.yScale.bandwidth())
            .attr('fill', d => this.compoundColors[d.compound])
            .attr('stroke', '#333')
            .attr('stroke-width', 1);

        // Compound labels
        const labels = this.svg.selectAll('.stint-label')
            .data(data.filter(d => d.totalLaps >= 5));

        labels.enter()
            .append('text')
            .attr('class', 'stint-label')
            .merge(labels)
            .attr('x', d => this.xScale(d.startLap) + (this.xScale(d.endLap) - this.xScale(d.startLap)) / 2)
            .attr('y', d => this.yScale(d.driverId) + this.yScale.bandwidth() / 2)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('font-size', '10px')
            .text(d => d.compound.charAt(0));
    }
}
```

---

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/sessions` | GET | List all available sessions |
| `/api/v1/sessions/{year}` | GET | List sessions for a year |
| `/api/v1/sessions/{year}/{event}` | GET | Get sessions for an event |
| `/api/v1/sessions/{session_id}` | GET | Get session details |
| `/api/v1/laps/{session_id}` | GET | Get all laps (with filters) |
| `/api/v1/laps/{session_id}/fastest` | GET | Get fastest laps |
| `/api/v1/laps/{session_id}/drivers/{driver}` | GET | Get driver's laps |
| `/api/v1/telemetry/{session_id}/{driver}/{lap}` | GET | Get lap telemetry |
| `/api/v1/strategy/{session_id}/stints` | GET | Get tire stint data |
| `/api/v1/strategy/{session_id}/pit-stops` | GET | Get pit stop data |
| `/api/v1/drivers` | GET | List all drivers |
| `/api/v1/drivers/{driver_id}` | GET | Get driver details |
| `/api/v1/teams` | GET | List all teams |
| `/api/v1/standings/{year}/drivers` | GET | Driver championship |
| `/api/v1/standings/{year}/constructors` | GET | Constructor championship |

---

## Configuration

```python
# config.py
from pydantic_settings import BaseSettings
from pathlib import Path
from enum import Enum

class StorageBackend(str, Enum):
    FILE = "file"
    DYNAMODB = "dynamodb"

class Settings(BaseSettings):
    # API Settings
    app_name: str = "F1-Dash API"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Storage Settings
    storage_backend: StorageBackend = StorageBackend.FILE
    data_dir: Path = Path("./data")

    # FastF1 Settings
    fastf1_cache_dir: Path = Path("./data/cache")

    # DynamoDB Settings (for future)
    dynamodb_endpoint: str | None = None
    dynamodb_region: str = "us-east-1"
    dynamodb_table_prefix: str = "f1plots_"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    class Config:
        env_file = ".env"
        env_prefix = "F1_"
```

---

## Getting Started

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Initialize FastF1 cache and fetch initial data
python -m app.ingestion.cli fetch --year 2024 --event "Bahrain"

# Run the API
uvicorn app.main:app --reload

# Frontend (simple static server)
cd frontend
python -m http.server 3000
```

---

## Security Architecture

### Backend Security Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    INCOMING REQUEST                              │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  TrustedHostMiddleware                           │
│            (Production only - validates Host header)             │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SecurityHeadersMiddleware                       │
│    X-Content-Type-Options | X-Frame-Options | CSP | HSTS        │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  RequestValidationMiddleware                     │
│              (Request ID, Content-Type validation)               │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RateLimitMiddleware                           │
│         /api/: 100/min | /ingest: 5/min | /train: 2/min         │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    APIKeyMiddleware                              │
│         (Optional - protects /ingest and /train endpoints)       │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CORSMiddleware                              │
│              (Explicit origins, no wildcards)                    │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Router                                │
│              (Pydantic validation on all inputs)                 │
└─────────────────────────────────────────────────────────────────┘
```

### Security Features

| Feature | Implementation | Location |
|---------|---------------|----------|
| **Security Headers** | CSP, X-Frame-Options, HSTS, etc. | `middleware/security.py` |
| **Rate Limiting** | In-memory sliding window | `middleware/security.py` |
| **API Key Auth** | Constant-time comparison | `middleware/security.py` |
| **Input Validation** | Pydantic schemas with validators | `api/schemas/*.py` |
| **Path Traversal** | Regex + resolved path check | `repositories/file/base.py` |
| **XSS Prevention** | Safe DOM methods (no innerHTML) | `frontend/js/utils/security.js` |
| **Error Handling** | Internal details hidden in prod | `main.py` |

### Frontend Security

```javascript
// Safe DOM manipulation utilities (frontend/js/utils/security.js)
export function escapeHtml(text) { ... }
export function createOption(value, text) { ... }
export function populateSelect(select, options, placeholder) { ... }
export function clearElement(element) { ... }
```

All dynamic content rendering uses `textContent` instead of `innerHTML`.

---

## Deployment Architecture

### Render Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                         RENDER                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               f1-dash-api (Web Service)                  │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │  uvicorn app.main:app --host 0.0.0.0 --port $PORT │    │   │
│  │  │                                                   │    │   │
│  │  │  Environment:                                     │    │   │
│  │  │  - F1_ENVIRONMENT=production                      │    │   │
│  │  │  - F1_CORS_ORIGINS=https://frontend.onrender.com │    │   │
│  │  │  - F1_API_KEYS=<secret>                          │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  │  Health Check: /health                                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │            f1-dash-frontend (Static Site)               │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │  Static files served from frontend/              │    │   │
│  │  │  config.js points to API URL                     │    │   │
│  │  │  SPA routing: /* → /index.html                   │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  │  Headers: X-Content-Type-Options, X-Frame-Options       │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Configuration Files

- `render.yaml` - Render blueprint defining both services
- `frontend/config.js` - Runtime API URL configuration
- `.env` - Local environment variables (not committed)

---

## Future Enhancements

1. **DynamoDB Implementation** - Complete the DynamoDB repository for cloud deployment
2. **Real-time Updates** - WebSocket support for live session data
3. **User Preferences** - Save favorite drivers, comparison presets
4. **Additional Visualizations** - Track maps, sector analysis, weather overlays
5. **Mobile Responsive** - Touch-friendly D3.js interactions
6. **Data Export** - CSV/JSON download of visualized data
7. **Authentication** - User accounts with JWT tokens
8. **Caching** - Redis/Memcached for API response caching

---

## Sources & References

- [FastF1 Documentation](https://docs.fastf1.dev/)
- [FastF1 GitHub](https://github.com/theOehrly/Fast-F1)
- [FastF1 Core Module](https://theoehrly.github.io/Fast-F1/core.html)
- [D3.js Official](https://d3js.org/)
- [D3.js Performance Optimization](https://moldstud.com/articles/p-optimizing-d3js-rendering-best-practices-for-faster-graphics-performance)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastAPI vs Django vs Flask Comparison](https://betterstack.com/community/guides/scaling-nodejs/fastapi-vs-django-vs-flask/)
- [Repository Pattern in Python](https://www.cosmicpython.com/book/chapter_02_repository.html)
- [F1 Tempo](https://www.f1-tempo.com/)
- [TracingInsights](https://tracinginsights.com)
- [RacingDataLab FastF1 Tutorials](https://www.racingdatalab.com/c02.php)
