"""Telemetry service - car telemetry analysis."""

from app.domain.models import TelemetryFrame
from app.repositories.interfaces import ITelemetryRepository


class TelemetryService:
    """
    Service for telemetry-related operations.

    Provides business logic for querying and analyzing car telemetry.
    """

    def __init__(self, telemetry_repo: ITelemetryRepository):
        """
        Initialize the service with repository.

        Args:
            telemetry_repo: Telemetry repository implementation
        """
        self._telemetry_repo = telemetry_repo

    async def get_lap_telemetry(
        self,
        session_id: str,
        driver_id: str,
        lap_number: int
    ) -> TelemetryFrame | None:
        """Get telemetry for a specific lap."""
        return await self._telemetry_repo.get_by_lap(
            session_id, driver_id, lap_number
        )

    async def get_driver_telemetry(
        self,
        session_id: str,
        driver_id: str
    ) -> list[TelemetryFrame]:
        """Get telemetry for all laps by a driver."""
        return await self._telemetry_repo.get_driver_laps(session_id, driver_id)

    async def get_fastest_lap_telemetry(
        self,
        session_id: str,
        driver_id: str
    ) -> TelemetryFrame | None:
        """Get telemetry for a driver's fastest lap."""
        return await self._telemetry_repo.get_fastest_lap_telemetry(
            session_id, driver_id
        )

    async def has_telemetry(
        self,
        session_id: str,
        driver_id: str,
        lap_number: int
    ) -> bool:
        """Check if telemetry exists for a lap."""
        return await self._telemetry_repo.has_telemetry(
            session_id, driver_id, lap_number
        )

    async def get_available_laps(
        self,
        session_id: str,
        driver_id: str
    ) -> list[int]:
        """Get list of lap numbers with telemetry."""
        return await self._telemetry_repo.get_available_laps(
            session_id, driver_id
        )

    async def save_telemetry(self, frame: TelemetryFrame) -> TelemetryFrame:
        """Save telemetry data."""
        return await self._telemetry_repo.add(frame)

    async def compare_laps(
        self,
        session_id: str,
        comparisons: list[tuple[str, int]]  # [(driver_id, lap_number), ...]
    ) -> list[dict]:
        """
        Compare telemetry from multiple laps.

        Args:
            session_id: Session ID
            comparisons: List of (driver_id, lap_number) tuples

        Returns:
            List of telemetry data for comparison
        """
        results = []
        for driver_id, lap_number in comparisons:
            frame = await self.get_lap_telemetry(
                session_id, driver_id, lap_number
            )
            if frame:
                results.append({
                    "driver_id": driver_id,
                    "lap_number": lap_number,
                    "lap_time_ms": frame.lap_time_ms,
                    "max_speed": frame.max_speed,
                    "point_count": frame.point_count,
                    "telemetry": [
                        {
                            "distance": p.distance,
                            "speed": p.speed,
                            "throttle": p.throttle,
                            "brake": p.brake,
                            "gear": p.gear,
                            "drs": p.drs_open,
                            "x": p.x,
                            "y": p.y,
                            "z": p.z,
                        }
                        for p in frame.points
                    ]
                })
        return results

    async def get_speed_trace(
        self,
        session_id: str,
        driver_id: str,
        lap_number: int
    ) -> list[dict] | None:
        """
        Get speed trace data for plotting.

        Returns simplified telemetry for speed trace visualization.
        """
        frame = await self.get_lap_telemetry(session_id, driver_id, lap_number)
        if not frame:
            return None

        return [
            {
                "distance": p.distance,
                "speed": p.speed,
                "gear": p.gear,
                "throttle": p.throttle,
                "brake": p.brake,
            }
            for p in frame.points
        ]

    async def get_gear_changes(
        self,
        session_id: str,
        driver_id: str,
        lap_number: int
    ) -> list[dict] | None:
        """
        Get gear change points for visualization.

        Returns list of gear change events.
        """
        frame = await self.get_lap_telemetry(session_id, driver_id, lap_number)
        if not frame or not frame.points:
            return None

        changes = []
        prev_gear = frame.points[0].gear

        for point in frame.points[1:]:
            if point.gear != prev_gear:
                changes.append({
                    "distance": point.distance,
                    "from_gear": prev_gear,
                    "to_gear": point.gear,
                    "speed": point.speed,
                })
                prev_gear = point.gear

        return changes
