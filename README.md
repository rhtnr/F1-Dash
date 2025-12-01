# F1 Plots

A Python-backed D3.js web application for F1 enthusiasts to visualize lap times, tire strategies, driver/team performance, telemetry, and race analytics.

## Features

- **Lap Time Analysis** - Scatter plots, box plots, lap-by-lap progression
- **Tire Strategy Visualization** - Stint bars with compound colors, pit stop timing
- **Telemetry Overlays** - Speed traces, throttle/brake, gear shifts by track position
- **Driver Comparisons** - Head-to-head lap times, sector comparisons
- **Race Progression** - Position changes over laps, gap analysis
- **Stint Analysis** - Tire degradation curves, compound performance

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework with async support
- **FastF1** - F1 data access library (2018+ seasons)
- **Pydantic** - Data validation and serialization
- **Repository Pattern** - Pluggable storage (file-based JSON, ready for DynamoDB)

### Frontend
- **D3.js** - Data visualization library
- **Vanilla JavaScript** - No framework dependencies

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js (optional, for frontend development server)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (optional)
cp .env.example .env

# Run the server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- OpenAPI Schema: `http://localhost:8000/openapi.json`

### Frontend Setup

```bash
cd frontend

# Option 1: Python simple server
python -m http.server 3000

# Option 2: Any static file server
npx serve -l 3000
```

The frontend will be available at `http://localhost:3000`

## API Endpoints

### Sessions
- `GET /api/v1/sessions` - List sessions (filterable by year)
- `GET /api/v1/sessions/years` - Get available years
- `GET /api/v1/sessions/events/{year}` - Get events for a year
- `GET /api/v1/sessions/id/{session_id}` - Get specific session
- `GET /api/v1/sessions/{year}/{round}` - Get event sessions

### Laps
- `GET /api/v1/laps/{session_id}` - Get session laps
- `GET /api/v1/laps/{session_id}/driver/{driver_id}` - Get driver laps
- `GET /api/v1/laps/{session_id}/fastest` - Get fastest laps
- `GET /api/v1/laps/{session_id}/distribution` - Lap time distribution
- `GET /api/v1/laps/{session_id}/compounds` - Compound performance

### Strategy
- `GET /api/v1/strategy/{session_id}/stints` - Get tire stints
- `GET /api/v1/strategy/{session_id}/summary` - Strategy summary

### Data Ingestion
- `GET /api/v1/ingest/status/{year}/{round}/{session}` - Check ingestion status
- `POST /api/v1/ingest/{year}/{round}/{session}` - Ingest session data

## Development

### Running Tests

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/unit/test_services.py -v
```

### Project Structure

```
f1-plots/
├── ARCHITECTURE.md      # Detailed architecture documentation
├── README.md
├── backend/
│   ├── app/
│   │   ├── api/         # FastAPI routes
│   │   │   ├── schemas/ # Request/Response schemas
│   │   │   └── v1/      # API version 1 endpoints
│   │   ├── config.py    # Settings management
│   │   ├── dependencies.py  # Dependency injection
│   │   ├── domain/      # Domain models and enums
│   │   │   ├── enums.py
│   │   │   └── models/
│   │   ├── ingestion/   # FastF1 data fetching
│   │   ├── main.py      # Application entry point
│   │   ├── repositories/
│   │   │   ├── file/    # File-based implementations
│   │   │   └── interfaces/  # Abstract repository interfaces
│   │   └── services/    # Business logic layer
│   ├── tests/
│   │   ├── integration/ # API integration tests
│   │   └── unit/        # Unit tests
│   ├── pyproject.toml
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── css/
    └── js/
        ├── api.js       # API client
        ├── charts/      # D3.js chart components
        └── app.js       # Main application
```

## Architecture

This application follows SOLID principles with a clean layered architecture:

1. **API Layer** - FastAPI routes handling HTTP requests
2. **Service Layer** - Business logic and data aggregation
3. **Repository Layer** - Abstract data access with pluggable implementations
4. **Domain Layer** - Pydantic models representing F1 concepts

The repository pattern allows switching between storage backends (file-based JSON, DynamoDB, etc.) without changing business logic.

For detailed architecture documentation, see [ARCHITECTURE.md](./ARCHITECTURE.md).

## Data Sources

Data is fetched from the official F1 timing system via the [FastF1](https://github.com/theOehrly/Fast-F1) library. Available data includes:
- Sessions from 2018 onwards
- Lap timing and sector times
- Tire compound and stint information
- Car telemetry (speed, throttle, brake, gear)
- Weather conditions
- Race control messages

## License

MIT
