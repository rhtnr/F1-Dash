"""Strategy service - tire strategy analysis."""

from app.domain.enums import TireCompound
from app.domain.models import TireStint, Lap
from app.repositories.interfaces import IStintRepository, ILapRepository


class StrategyService:
    """
    Service for tire strategy analysis.

    Provides business logic for analyzing tire strategies,
    stint performance, and pit stop timing.
    """

    def __init__(
        self,
        stint_repo: IStintRepository,
        lap_repo: ILapRepository
    ):
        """
        Initialize the service with repositories.

        Args:
            stint_repo: Stint repository implementation
            lap_repo: Lap repository implementation
        """
        self._stint_repo = stint_repo
        self._lap_repo = lap_repo

    async def get_session_stints(self, session_id: str) -> list[TireStint]:
        """Get all tire stints for a session."""
        return await self._stint_repo.get_by_session(session_id)

    async def get_driver_stints(
        self, session_id: str, driver_id: str
    ) -> list[TireStint]:
        """Get all stints for a driver in a session."""
        return await self._stint_repo.get_by_driver(session_id, driver_id)

    async def get_compound_stints(
        self, session_id: str, compound: TireCompound
    ) -> list[TireStint]:
        """Get all stints on a specific compound."""
        return await self._stint_repo.get_by_compound(session_id, compound)

    async def save_stints(self, stints: list[TireStint]) -> list[TireStint]:
        """Save multiple stints."""
        result = []
        for stint in stints:
            saved = await self._stint_repo.add(stint)
            result.append(saved)
        return result

    async def get_strategy_summary(
        self, session_id: str
    ) -> list[dict]:
        """
        Get strategy summary for all drivers.

        Returns list of driver strategies with compounds used.
        """
        stints = await self._stint_repo.get_by_session(session_id)

        # Group by driver
        by_driver: dict[str, list[TireStint]] = {}
        for stint in stints:
            if stint.driver_id not in by_driver:
                by_driver[stint.driver_id] = []
            by_driver[stint.driver_id].append(stint)

        summaries = []
        for driver_id, driver_stints in by_driver.items():
            sorted_stints = sorted(driver_stints, key=lambda s: s.stint_number)
            summaries.append({
                "driver_id": driver_id,
                "total_stints": len(sorted_stints),
                "compounds": [s.compound.value for s in sorted_stints],
                "pit_stops": len(sorted_stints) - 1,
                "stints": [
                    {
                        "stint_number": s.stint_number,
                        "compound": s.compound.value,
                        "start_lap": s.start_lap,
                        "end_lap": s.end_lap,
                        "total_laps": s.total_laps,
                        "avg_lap_time": s.avg_lap_time_seconds,
                        "degradation_rate": s.degradation_rate,
                    }
                    for s in sorted_stints
                ]
            })

        return summaries

    async def get_optimal_compound(
        self, session_id: str
    ) -> dict[str, dict]:
        """
        Analyze which compound performed best.

        Returns performance metrics by compound.
        """
        stints = await self._stint_repo.get_by_session(session_id)

        by_compound: dict[str, list[TireStint]] = {}
        for stint in stints:
            compound = stint.compound.value
            if compound not in by_compound:
                by_compound[compound] = []
            by_compound[compound].append(stint)

        analysis = {}
        for compound, compound_stints in by_compound.items():
            valid_times = [
                s.avg_lap_time_seconds for s in compound_stints
                if s.avg_lap_time_seconds is not None
            ]
            valid_deg = [
                s.degradation_rate for s in compound_stints
                if s.degradation_rate is not None
            ]

            analysis[compound] = {
                "stint_count": len(compound_stints),
                "total_laps": sum(s.total_laps for s in compound_stints),
                "avg_lap_time": sum(valid_times) / len(valid_times) if valid_times else None,
                "avg_degradation": sum(valid_deg) / len(valid_deg) if valid_deg else None,
            }

        return analysis

    async def calculate_stint_degradation(
        self, session_id: str, driver_id: str, stint_number: int
    ) -> dict | None:
        """
        Calculate detailed degradation for a specific stint.

        Returns lap-by-lap performance data.
        """
        laps = await self._lap_repo.get_by_stint(
            session_id, driver_id, stint_number
        )
        if not laps:
            return None

        sorted_laps = sorted(laps, key=lambda l: l.lap_number)
        valid_laps = [l for l in sorted_laps if l.is_valid_for_analysis and l.lap_time]

        if len(valid_laps) < 2:
            return None

        lap_data = []
        for i, lap in enumerate(valid_laps):
            lap_data.append({
                "lap_number": lap.lap_number,
                "lap_in_stint": i + 1,
                "lap_time": lap.lap_time.total_seconds(),
                "tyre_life": lap.tyre_life,
            })

        # Calculate degradation
        if len(lap_data) >= 3:
            times = [l["lap_time"] for l in lap_data]
            n = len(times)
            x_mean = (n + 1) / 2
            y_mean = sum(times) / n
            numerator = sum((i + 1 - x_mean) * (t - y_mean) for i, t in enumerate(times))
            denominator = sum((i + 1 - x_mean) ** 2 for i in range(n))
            degradation = numerator / denominator if denominator > 0 else 0
        else:
            degradation = 0

        return {
            "driver_id": driver_id,
            "stint_number": stint_number,
            "compound": sorted_laps[0].compound.value if sorted_laps else None,
            "total_laps": len(valid_laps),
            "degradation_per_lap": degradation,
            "laps": lap_data,
        }
