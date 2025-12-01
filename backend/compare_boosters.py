#!/usr/bin/env python3
"""
Compare prediction accuracy with and without boosters.
"""

import asyncio
import sys
from pathlib import Path

import pandas as pd
import numpy as np
import fastf1

sys.path.insert(0, str(Path(__file__).parent))

from app.services.prediction_service import RacePredictionService


async def compare_backtests(service: RacePredictionService, year: int, rounds: list[int]):
    """Run backtests with and without boosters and compare."""

    results_with_boosters = []
    results_without_boosters = []

    for round_num in rounds:
        try:
            schedule = fastf1.get_event_schedule(year)
            event_row = schedule[schedule["RoundNumber"] == round_num]
            if event_row.empty:
                continue
            event_name = event_row["EventName"].iloc[0]

            print(f"\n{year} R{round_num} - {event_name}")
            print("-" * 50)

            # Test WITH boosters
            service._use_boosters = True
            result_with = await service.backtest(year, round_num)
            metrics_with = result_with["metrics"]

            # Test WITHOUT boosters
            service._use_boosters = False
            result_without = await service.backtest(year, round_num)
            metrics_without = result_without["metrics"]

            print(f"  With Boosters:    MAE={metrics_with['mae']:.2f}, "
                  f"≤3pos={metrics_with['within_3_positions']:.0f}%, "
                  f"Winner={'✓' if metrics_with['winner_correct'] else '✗'}")
            print(f"  Without Boosters: MAE={metrics_without['mae']:.2f}, "
                  f"≤3pos={metrics_without['within_3_positions']:.0f}%, "
                  f"Winner={'✓' if metrics_without['winner_correct'] else '✗'}")

            improvement = metrics_without['mae'] - metrics_with['mae']
            print(f"  MAE Improvement: {improvement:+.2f} positions")

            results_with_boosters.append({
                "year": year,
                "round": round_num,
                "event": event_name,
                **metrics_with
            })
            results_without_boosters.append({
                "year": year,
                "round": round_num,
                "event": event_name,
                **metrics_without
            })

        except Exception as e:
            print(f"  Error: {e}")
            continue

    # Re-enable boosters
    service._use_boosters = True

    return results_with_boosters, results_without_boosters


async def main():
    print("=" * 60)
    print("BOOSTER COMPARISON - BACKTEST ANALYSIS")
    print("=" * 60)

    service = RacePredictionService()

    if service._model is None:
        print("ERROR: Model not trained.")
        return

    print(f"\nBoosters loaded: {len(service._boosters.get('drivers', {}))} drivers, "
          f"{len(service._boosters.get('teams', {}))} teams")

    # Test on a sample of 2024 races
    test_rounds = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # First 10 rounds of 2024

    results_with, results_without = await compare_backtests(service, 2024, test_rounds)

    if not results_with:
        print("\nNo results collected!")
        return

    # Summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)

    df_with = pd.DataFrame(results_with)
    df_without = pd.DataFrame(results_without)

    print(f"\nWith Boosters:")
    print(f"  Average MAE: {df_with['mae'].mean():.2f}")
    print(f"  Avg ≤1 position: {df_with['within_1_position'].mean():.1f}%")
    print(f"  Avg ≤3 positions: {df_with['within_3_positions'].mean():.1f}%")
    print(f"  Avg ≤5 positions: {df_with['within_5_positions'].mean():.1f}%")
    print(f"  Winners correct: {df_with['winner_correct'].sum()}/{len(df_with)}")
    print(f"  Avg podium correct: {df_with['podium_correct'].mean():.1f}/3")

    print(f"\nWithout Boosters:")
    print(f"  Average MAE: {df_without['mae'].mean():.2f}")
    print(f"  Avg ≤1 position: {df_without['within_1_position'].mean():.1f}%")
    print(f"  Avg ≤3 positions: {df_without['within_3_positions'].mean():.1f}%")
    print(f"  Avg ≤5 positions: {df_without['within_5_positions'].mean():.1f}%")
    print(f"  Winners correct: {df_without['winner_correct'].sum()}/{len(df_without)}")
    print(f"  Avg podium correct: {df_without['podium_correct'].mean():.1f}/3")

    print("\n" + "=" * 60)
    print("IMPROVEMENT WITH BOOSTERS")
    print("=" * 60)

    mae_improvement = df_without['mae'].mean() - df_with['mae'].mean()
    within3_improvement = df_with['within_3_positions'].mean() - df_without['within_3_positions'].mean()
    winner_improvement = df_with['winner_correct'].sum() - df_without['winner_correct'].sum()

    print(f"  MAE Improvement: {mae_improvement:+.2f} positions")
    print(f"  ≤3 positions accuracy: {within3_improvement:+.1f}%")
    print(f"  Additional winners correct: {winner_improvement:+d}")

    if mae_improvement > 0:
        print(f"\n✓ Boosters IMPROVED accuracy by {mae_improvement:.2f} MAE")
    else:
        print(f"\n✗ Boosters did not improve accuracy ({mae_improvement:.2f} MAE)")


if __name__ == "__main__":
    asyncio.run(main())
