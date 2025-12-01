"""Lap service - business logic for lap operations."""

from datetime import timedelta

from app.domain.enums import TireCompound
from app.domain.models import Lap
from app.repositories.interfaces import ILapRepository


class LapService:
    """
    Service for lap-related operations.

    Implements business logic for querying and analyzing lap data.
    """

    def __init__(self, lap_repo: ILapRepository):
        """
        Initialize the service with repository.

        Args:
            lap_repo: Lap repository implementation
        """
        self._lap_repo = lap_repo

    async def get_session_laps(self, session_id: str) -> list[Lap]:
        """Get all laps for a session."""
        return await self._lap_repo.get_by_session(session_id)

    async def get_driver_laps(
        self, session_id: str, driver_id: str
    ) -> list[Lap]:
        """Get all laps for a driver in a session."""
        return await self._lap_repo.get_by_session_and_driver(
            session_id, driver_id
        )

    async def get_laps_by_compound(
        self, session_id: str, compound: TireCompound
    ) -> list[Lap]:
        """Get all laps on a specific tire compound."""
        return await self._lap_repo.get_by_compound(session_id, compound)

    async def get_fastest_laps(
        self, session_id: str, top_n: int = 10
    ) -> list[Lap]:
        """Get the fastest laps in a session."""
        return await self._lap_repo.get_fastest_laps(session_id, top_n)

    async def get_valid_laps(self, session_id: str) -> list[Lap]:
        """Get all valid laps for analysis."""
        return await self._lap_repo.get_valid_laps(session_id)

    async def get_personal_bests(self, session_id: str) -> list[Lap]:
        """Get personal best lap for each driver."""
        return await self._lap_repo.get_personal_bests(session_id)

    async def get_stint_laps(
        self, session_id: str, driver_id: str, stint_number: int
    ) -> list[Lap]:
        """Get all laps in a specific stint."""
        return await self._lap_repo.get_by_stint(
            session_id, driver_id, stint_number
        )

    async def save_laps(self, laps: list[Lap]) -> list[Lap]:
        """Save multiple laps."""
        return await self._lap_repo.add_many(laps)

    async def get_lap_time_distribution(
        self, session_id: str
    ) -> dict[str, list[float]]:
        """
        Get lap time distribution by driver.

        Returns dict mapping driver_id to list of lap times in seconds.
        """
        laps = await self._lap_repo.get_valid_laps(session_id)

        distribution: dict[str, list[float]] = {}
        for lap in laps:
            if lap.lap_time is None:
                continue
            if lap.driver_id not in distribution:
                distribution[lap.driver_id] = []
            distribution[lap.driver_id].append(lap.lap_time.total_seconds())

        return distribution

    async def get_compound_performance(
        self, session_id: str
    ) -> dict[str, dict]:
        """
        Get performance statistics by tire compound.

        Returns dict with compound performance metrics including:
        - Raw fastest/average times
        - Fuel-corrected times (normalized to start-of-race fuel)
        - Degradation-adjusted times (normalized to fresh tire)

        Fuel correction assumes:
        - 110kg fuel at race start, ~0.03s/lap/kg fuel effect
        - Total fuel effect ~3.3s from full to empty over race distance

        Degradation is estimated by averaging first 3 laps of each stint
        to get the "fresh tire" baseline for each compound.
        """
        all_laps = await self._lap_repo.get_valid_laps(session_id)

        if not all_laps:
            return {}

        # Determine total race laps (max lap number in session)
        total_laps = max(lap.lap_number for lap in all_laps)

        # Fuel correction constant (seconds saved per lap of fuel burned)
        # Approximately 3.3s total over a 56 lap race = ~0.059s per lap
        fuel_effect_per_lap = 3.3 / total_laps if total_laps > 0 else 0.059

        performance: dict[str, dict] = {}
        for compound in TireCompound:
            compound_laps = [
                lap for lap in all_laps
                if lap.compound == compound and lap.lap_time is not None
            ]
            if not compound_laps:
                continue

            times = [lap.lap_time.total_seconds() for lap in compound_laps]

            # Calculate fuel-corrected times
            # Normalize all laps to "start of race" fuel load
            # Correction = (total_laps - lap_number) * fuel_effect_per_lap
            # A lap at the end of race is faster due to less fuel, so we ADD time
            fuel_corrected_times = []
            for lap in compound_laps:
                raw_time = lap.lap_time.total_seconds()
                # Laps burned = lap_number - 1 (lap 1 has full fuel)
                laps_of_fuel_burned = lap.lap_number - 1
                # Time benefit from burned fuel that we need to add back
                fuel_correction = laps_of_fuel_burned * fuel_effect_per_lap
                corrected_time = raw_time + fuel_correction
                fuel_corrected_times.append(corrected_time)

            # Calculate degradation-adjusted times
            # Use fresh tire baseline (average of tyre_life 1-3 laps) for each compound
            fresh_tire_laps = [
                lap for lap in compound_laps
                if lap.tyre_life <= 3 and lap.tyre_life >= 1
            ]

            # Get baseline pace on fresh tires (fuel-corrected)
            if fresh_tire_laps:
                fresh_times = []
                for lap in fresh_tire_laps:
                    raw_time = lap.lap_time.total_seconds()
                    fuel_correction = (lap.lap_number - 1) * fuel_effect_per_lap
                    fresh_times.append(raw_time + fuel_correction)
                fresh_baseline = sum(fresh_times) / len(fresh_times)
            else:
                # Fallback: use fastest fuel-corrected time as baseline
                fresh_baseline = min(fuel_corrected_times)

            # Find the fastest lap info
            fastest_lap = min(compound_laps, key=lambda l: l.lap_time.total_seconds())
            fastest_lap_info = {
                "driver": fastest_lap.driver_id,
                "lap_number": fastest_lap.lap_number,
                "time": fastest_lap.lap_time.total_seconds(),
                "tyre_life": fastest_lap.tyre_life,
            }

            # Calculate fastest fuel-corrected time
            fastest_fuel_corrected = min(fuel_corrected_times)

            performance[compound.value] = {
                "count": len(times),
                "fastest": min(times),
                "average": sum(times) / len(times),
                "slowest": max(times),
                "fastest_fuel_corrected": fastest_fuel_corrected,
                "average_fuel_corrected": sum(fuel_corrected_times) / len(fuel_corrected_times),
                "fresh_tire_pace": fresh_baseline,
                "fastest_lap": fastest_lap_info,
            }

        return performance

    async def compare_drivers(
        self,
        session_id: str,
        driver1_id: str,
        driver2_id: str
    ) -> dict:
        """
        Compare two drivers' performance.

        Returns comparison metrics.
        """
        driver1_laps = await self.get_driver_laps(session_id, driver1_id)
        driver2_laps = await self.get_driver_laps(session_id, driver2_id)

        def get_stats(laps: list[Lap]) -> dict | None:
            valid = [l for l in laps if l.lap_time and l.is_valid_for_analysis]
            if not valid:
                return None
            times = [l.lap_time.total_seconds() for l in valid]
            return {
                "lap_count": len(times),
                "fastest": min(times),
                "average": sum(times) / len(times),
                "median": sorted(times)[len(times) // 2],
            }

        return {
            driver1_id: get_stats(driver1_laps),
            driver2_id: get_stats(driver2_laps),
        }
