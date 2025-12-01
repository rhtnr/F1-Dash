"""Transform FastF1 data to domain models."""

from datetime import timedelta
from typing import Any

import pandas as pd

from app.domain.enums import SessionType, TireCompound, TrackStatus
from app.domain.models import (
    Driver,
    Lap,
    Session,
    TelemetryFrame,
    TelemetryPoint,
    TireStint,
)
from app.domain.models.team import get_team_color


def _safe_timedelta(value: Any) -> timedelta | None:
    """Safely convert a value to timedelta."""
    if pd.isna(value) or value is None:
        return None
    if isinstance(value, timedelta):
        return value
    if isinstance(value, pd.Timedelta):
        return value.to_pytimedelta()
    return None


def _safe_float(value: Any) -> float | None:
    """Safely convert a value to float."""
    if pd.isna(value) or value is None:
        return None
    return float(value)


def _safe_int(value: Any, default: int = 0) -> int:
    """Safely convert a value to int."""
    if pd.isna(value) or value is None:
        return default
    return int(value)


def _safe_bool(value: Any, default: bool = False) -> bool:
    """Safely convert a value to bool."""
    if pd.isna(value) or value is None:
        return default
    return bool(value)


def transform_session(ff1_session: Any) -> Session:
    """
    Transform a FastF1 session to domain model.

    Args:
        ff1_session: FastF1 Session object

    Returns:
        Session domain model
    """
    event = ff1_session.event
    session_type = SessionType.from_fastf1(ff1_session.name)

    return Session(
        id=Session.create_id(
            event["EventDate"].year,
            event["RoundNumber"],
            session_type
        ),
        year=event["EventDate"].year,
        round_number=event["RoundNumber"],
        event_name=event["EventName"],
        country=event["Country"],
        location=event["Location"],
        circuit_name=event.get("CircuitName", event["Location"]),
        circuit_short_name=event.get("CircuitShortName", event["Location"][:3].upper()),
        session_type=session_type,
        session_date=ff1_session.date.to_pydatetime() if hasattr(ff1_session.date, 'to_pydatetime') else ff1_session.date,
        total_laps=ff1_session.total_laps if hasattr(ff1_session, "total_laps") else None,
        official_name=event.get("OfficialEventName"),
    )


def transform_driver(
    driver_info: dict[str, Any],
    session_id: str | None = None
) -> Driver:
    """
    Transform FastF1 driver info to domain model.

    Args:
        driver_info: Driver information dictionary from FastF1
        session_id: Optional session ID for context

    Returns:
        Driver domain model
    """
    team_name = str(driver_info.get("TeamName", "Unknown"))
    team_color = driver_info.get("TeamColor", "")
    if not team_color or team_color == "nan":
        team_color = get_team_color(team_name)
    elif not team_color.startswith("#"):
        team_color = f"#{team_color}"

    return Driver(
        id=str(driver_info["Abbreviation"]),
        number=int(driver_info["DriverNumber"]),
        full_name=str(driver_info.get("FullName", f"{driver_info.get('FirstName', '')} {driver_info.get('LastName', '')}")),
        first_name=str(driver_info.get("FirstName", "")),
        last_name=str(driver_info.get("LastName", "")),
        team_id=team_name.lower().replace(" ", "_"),
        team_name=team_name,
        team_color=team_color,
        country_code=driver_info.get("CountryCode"),
        headshot_url=driver_info.get("HeadshotUrl"),
    )


def transform_lap(
    row: pd.Series,
    session_id: str
) -> Lap:
    """
    Transform a FastF1 lap row to domain model.

    Args:
        row: Pandas Series containing lap data
        session_id: Parent session ID

    Returns:
        Lap domain model
    """
    driver_id = str(row["Driver"])
    lap_number = _safe_int(row["LapNumber"], 1)

    return Lap(
        id=Lap.create_id(session_id, driver_id, lap_number),
        session_id=session_id,
        driver_id=driver_id,
        lap_number=lap_number,
        lap_time=_safe_timedelta(row.get("LapTime")),
        sector_1_time=_safe_timedelta(row.get("Sector1Time")),
        sector_2_time=_safe_timedelta(row.get("Sector2Time")),
        sector_3_time=_safe_timedelta(row.get("Sector3Time")),
        compound=TireCompound.from_fastf1(row.get("Compound")),
        tyre_life=_safe_int(row.get("TyreLife"), 0),
        stint=_safe_int(row.get("Stint"), 1),
        is_fresh_tyre=_safe_bool(row.get("FreshTyre")),
        speed_i1=_safe_float(row.get("SpeedI1")),
        speed_i2=_safe_float(row.get("SpeedI2")),
        speed_fl=_safe_float(row.get("SpeedFL")),
        speed_st=_safe_float(row.get("SpeedST")),
        position=_safe_int(row.get("Position")) if not pd.isna(row.get("Position")) else None,
        track_status=TrackStatus.from_fastf1(row.get("TrackStatus")),
        is_personal_best=_safe_bool(row.get("IsPersonalBest")),
        is_accurate=_safe_bool(row.get("IsAccurate"), True),
        deleted=_safe_bool(row.get("Deleted")),
        deleted_reason=str(row.get("DeletedReason")) if not pd.isna(row.get("DeletedReason")) else None,
        pit_in_time=_safe_timedelta(row.get("PitInTime")),
        pit_out_time=_safe_timedelta(row.get("PitOutTime")),
        is_pit_in_lap=not pd.isna(row.get("PitInTime")),
        is_pit_out_lap=not pd.isna(row.get("PitOutTime")),
    )


def transform_stint(
    laps: list[Lap],
    session_id: str,
    driver_id: str,
    stint_number: int
) -> TireStint:
    """
    Create a TireStint from a group of laps.

    Args:
        laps: List of laps in the stint
        session_id: Session ID
        driver_id: Driver abbreviation
        stint_number: Stint number

    Returns:
        TireStint domain model
    """
    if not laps:
        raise ValueError("Cannot create stint from empty lap list")

    # Sort laps by lap number
    sorted_laps = sorted(laps, key=lambda l: l.lap_number)

    # Get compound from first lap
    compound = sorted_laps[0].compound
    is_fresh = sorted_laps[0].is_fresh_tyre

    # Calculate metrics
    valid_times = [
        l.lap_time for l in sorted_laps
        if l.lap_time is not None and l.is_valid_for_analysis
    ]

    avg_time = None
    best_time = None
    if valid_times:
        avg_seconds = sum(t.total_seconds() for t in valid_times) / len(valid_times)
        avg_time = timedelta(seconds=avg_seconds)
        best_time = min(valid_times)

    # Calculate degradation (simplified linear regression)
    degradation_rate = None
    if len(valid_times) >= 3:
        times_seconds = [t.total_seconds() for t in valid_times]
        # Simple linear slope calculation
        n = len(times_seconds)
        x_mean = (n + 1) / 2
        y_mean = sum(times_seconds) / n
        numerator = sum((i + 1 - x_mean) * (t - y_mean) for i, t in enumerate(times_seconds))
        denominator = sum((i + 1 - x_mean) ** 2 for i in range(n))
        if denominator > 0:
            degradation_rate = numerator / denominator

    return TireStint(
        id=TireStint.create_id(session_id, driver_id, stint_number),
        session_id=session_id,
        driver_id=driver_id,
        stint_number=stint_number,
        compound=compound,
        is_fresh=is_fresh,
        start_lap=sorted_laps[0].lap_number,
        end_lap=sorted_laps[-1].lap_number,
        avg_lap_time=avg_time,
        best_lap_time=best_time,
        degradation_rate=degradation_rate,
    )


def transform_telemetry(
    car_data: pd.DataFrame,
    session_id: str,
    driver_id: str,
    lap_number: int,
    lap_time_ms: int | None = None
) -> TelemetryFrame:
    """
    Transform FastF1 car telemetry to domain model.

    Args:
        car_data: DataFrame with car telemetry
        session_id: Session ID
        driver_id: Driver abbreviation
        lap_number: Lap number
        lap_time_ms: Total lap time in milliseconds

    Returns:
        TelemetryFrame domain model
    """
    points = []

    for _, row in car_data.iterrows():
        point = TelemetryPoint(
            time_ms=int(row.get("Time", pd.Timedelta(0)).total_seconds() * 1000) if hasattr(row.get("Time", 0), "total_seconds") else 0,
            session_time_ms=int(row.get("SessionTime", pd.Timedelta(0)).total_seconds() * 1000) if hasattr(row.get("SessionTime", 0), "total_seconds") else None,
            distance=float(row.get("Distance", 0)),
            speed=float(row.get("Speed", 0)),
            rpm=int(row.get("RPM", 0)),
            gear=int(row.get("nGear", 0)),
            throttle=float(row.get("Throttle", 0)),
            brake=bool(row.get("Brake", False)),
            drs=int(row.get("DRS", 0)),
            x=_safe_float(row.get("X")),
            y=_safe_float(row.get("Y")),
            z=_safe_float(row.get("Z")),
        )
        points.append(point)

    return TelemetryFrame(
        session_id=session_id,
        driver_id=driver_id,
        lap_number=lap_number,
        lap_time_ms=lap_time_ms,
        points=points,
    )
