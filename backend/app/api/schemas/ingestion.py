"""Ingestion API schemas."""

import re
from typing import Annotated
from pydantic import BaseModel, Field, field_validator

# Valid session types
VALID_SESSION_TYPES = {"FP1", "FP2", "FP3", "Q", "SQ", "SS", "R", "S"}

# Valid driver ID pattern (3 uppercase letters)
DRIVER_ID_PATTERN = re.compile(r"^[A-Z]{3}$")


class IngestSessionRequest(BaseModel):
    """Request schema for session ingestion."""

    year: int = Field(..., ge=2018, le=2030, description="Season year")
    round_number: int = Field(..., ge=1, le=30, description="Round number")
    session_type: str = Field(..., description="Session type (FP1, Q, R, etc.)")
    include_telemetry: bool = Field(False, description="Include telemetry data")
    force: bool = Field(False, description="Force re-ingestion if already exists")

    @field_validator("session_type")
    @classmethod
    def validate_session_type(cls, v: str) -> str:
        """Validate session type is a known type."""
        v_upper = v.upper()
        if v_upper not in VALID_SESSION_TYPES:
            raise ValueError(f"Invalid session type. Must be one of: {', '.join(sorted(VALID_SESSION_TYPES))}")
        return v_upper


class IngestTelemetryRequest(BaseModel):
    """Request schema for telemetry ingestion."""

    year: int = Field(..., ge=2018, le=2030, description="Season year")
    round_number: int = Field(..., ge=1, le=30, description="Round number")
    session_type: str = Field(..., description="Session type")
    driver_id: str = Field(..., min_length=3, max_length=3, description="Driver abbreviation (3 letters)")
    lap_numbers: list[int] | None = Field(
        None, description="Specific laps (None = all)"
    )

    @field_validator("session_type")
    @classmethod
    def validate_session_type(cls, v: str) -> str:
        """Validate session type is a known type."""
        v_upper = v.upper()
        if v_upper not in VALID_SESSION_TYPES:
            raise ValueError(f"Invalid session type. Must be one of: {', '.join(sorted(VALID_SESSION_TYPES))}")
        return v_upper

    @field_validator("driver_id")
    @classmethod
    def validate_driver_id(cls, v: str) -> str:
        """Validate driver ID is 3 uppercase letters."""
        v_upper = v.upper()
        if not DRIVER_ID_PATTERN.match(v_upper):
            raise ValueError("Driver ID must be exactly 3 uppercase letters")
        return v_upper

    @field_validator("lap_numbers")
    @classmethod
    def validate_lap_numbers(cls, v: list[int] | None) -> list[int] | None:
        """Validate lap numbers are positive."""
        if v is not None:
            if not all(lap > 0 and lap < 200 for lap in v):
                raise ValueError("Lap numbers must be between 1 and 199")
        return v


class IngestEventRequest(BaseModel):
    """Request schema for event ingestion."""

    year: int = Field(..., ge=2018, le=2030, description="Season year")
    round_number: int = Field(..., ge=1, le=30, description="Round number")
    include_telemetry: bool = Field(False, description="Include telemetry data")


class IngestionResponse(BaseModel):
    """Response schema for ingestion operations."""

    success: bool
    message: str
    session_id: str | None = None
    session_ids: list[str] | None = None
