#!/usr/bin/env python3
"""
Analyze prediction errors by driver/team to calculate booster coefficients.

This script:
1. Runs backtests on historical races
2. Analyzes errors by driver and team
3. Calculates booster coefficients to improve predictions
"""

import asyncio
import sys
import json
from pathlib import Path
from collections import defaultdict

import pandas as pd
import numpy as np
import fastf1

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.prediction_service import RacePredictionService


# Driver to team mapping for recent seasons
DRIVER_TEAMS = {
    # 2024
    "VER": "Red Bull", "PER": "Red Bull",
    "LEC": "Ferrari", "SAI": "Ferrari",
    "HAM": "Mercedes", "RUS": "Mercedes",
    "NOR": "McLaren", "PIA": "McLaren",
    "ALO": "Aston Martin", "STR": "Aston Martin",
    "OCO": "Alpine", "GAS": "Alpine",
    "ALB": "Williams", "SAR": "Williams",
    "BOT": "Alfa Romeo", "ZHO": "Alfa Romeo",
    "MAG": "Haas", "HUL": "Haas",
    "TSU": "AlphaTauri", "RIC": "AlphaTauri", "DEV": "AlphaTauri", "LAW": "AlphaTauri",
    "BEA": "Ferrari",  # reserve driver
    "SHW": "Williams",  # reserve
}


async def collect_backtest_errors(service: RacePredictionService, years: list[int]) -> list[dict]:
    """Run backtests on multiple races and collect error data."""
    all_errors = []

    for year in years:
        try:
            schedule = fastf1.get_event_schedule(year)
            completed = schedule[schedule["EventDate"] < pd.Timestamp.now()]

            for _, event in completed.iterrows():
                round_num = event["RoundNumber"]
                event_name = event["EventName"]

                print(f"\nBacktesting {year} R{round_num} - {event_name}")

                try:
                    result = await service.backtest(year, round_num)

                    for pred in result["predictions"]:
                        if pred["actual_position"] is not None:
                            driver = pred["driver"]
                            team = DRIVER_TEAMS.get(driver, "Unknown")

                            # Signed error: positive = predicted too low (should be higher)
                            # negative = predicted too high (should be lower)
                            signed_error = pred["actual_position"] - pred["rank"]

                            all_errors.append({
                                "year": year,
                                "round": round_num,
                                "event": event_name,
                                "driver": driver,
                                "team": team,
                                "predicted_rank": pred["rank"],
                                "actual_position": pred["actual_position"],
                                "signed_error": signed_error,
                                "abs_error": abs(signed_error),
                                "predicted_position_raw": pred["predicted_position"],
                            })

                except Exception as e:
                    print(f"  Error: {e}")
                    continue

        except Exception as e:
            print(f"Error getting schedule for {year}: {e}")
            continue

    return all_errors


def analyze_driver_errors(errors: list[dict]) -> dict:
    """Analyze errors by driver to find systematic biases."""
    df = pd.DataFrame(errors)

    print("\n" + "="*80)
    print("DRIVER ERROR ANALYSIS")
    print("="*80)

    # Group by driver
    driver_stats = df.groupby("driver").agg({
        "signed_error": ["mean", "std", "count"],
        "abs_error": "mean"
    }).round(2)

    driver_stats.columns = ["mean_error", "std_error", "count", "mae"]
    driver_stats = driver_stats.sort_values("mean_error")

    print("\nDriver Statistics (sorted by mean error):")
    print("  Positive mean = model predicts too OPTIMISTIC (rank is better than actual)")
    print("  Negative mean = model predicts too PESSIMISTIC (rank is worse than actual)")
    print()

    for driver, row in driver_stats.iterrows():
        bias_direction = "OPTIMISTIC" if row["mean_error"] < 0 else "PESSIMISTIC"
        print(f"  {driver:4s}: Mean Error={row['mean_error']:+6.2f} ({bias_direction:11s}), "
              f"MAE={row['mae']:5.2f}, Std={row['std_error']:5.2f}, N={int(row['count'])}")

    return driver_stats.to_dict("index")


def analyze_team_errors(errors: list[dict]) -> dict:
    """Analyze errors by team to find systematic biases."""
    df = pd.DataFrame(errors)

    print("\n" + "="*80)
    print("TEAM ERROR ANALYSIS")
    print("="*80)

    # Group by team
    team_stats = df.groupby("team").agg({
        "signed_error": ["mean", "std", "count"],
        "abs_error": "mean"
    }).round(2)

    team_stats.columns = ["mean_error", "std_error", "count", "mae"]
    team_stats = team_stats.sort_values("mean_error")

    print("\nTeam Statistics (sorted by mean error):")
    print()

    for team, row in team_stats.iterrows():
        bias_direction = "OPTIMISTIC" if row["mean_error"] < 0 else "PESSIMISTIC"
        print(f"  {team:15s}: Mean Error={row['mean_error']:+6.2f} ({bias_direction:11s}), "
              f"MAE={row['mae']:5.2f}, Std={row['std_error']:5.2f}, N={int(row['count'])}")

    return team_stats.to_dict("index")


def calculate_booster_coefficients(driver_stats: dict, team_stats: dict) -> dict:
    """
    Calculate booster coefficients to correct for systematic biases.

    The booster is applied to the predicted position:
    adjusted_position = predicted_position + booster

    If a driver is consistently over-predicted (finishes worse than predicted),
    we add a positive booster to push them down.
    If a driver is consistently under-predicted (finishes better than predicted),
    we add a negative booster to push them up.
    """
    print("\n" + "="*80)
    print("BOOSTER COEFFICIENTS")
    print("="*80)

    boosters = {
        "drivers": {},
        "teams": {}
    }

    # Calculate driver boosters (direct from mean error with dampening)
    print("\nDriver Boosters:")
    for driver, stats in driver_stats.items():
        mean_error = stats["mean_error"]
        count = stats["count"]

        # Apply dampening for low sample sizes (confidence weighting)
        # More samples = more confident in the correction
        confidence = min(1.0, count / 15)  # Full confidence at 15+ samples

        # The booster is the negative of mean error (to correct for it)
        # with dampening applied
        booster = -mean_error * confidence * 0.7  # 70% correction strength

        if abs(booster) > 0.3:  # Only apply meaningful corrections
            boosters["drivers"][driver] = round(booster, 2)
            direction = "↑ improve" if booster < 0 else "↓ worsen"
            print(f"  {driver:4s}: {booster:+5.2f} ({direction} prediction by {abs(booster):.1f} positions)")

    # Calculate team boosters
    print("\nTeam Boosters:")
    for team, stats in team_stats.items():
        mean_error = stats["mean_error"]
        count = stats["count"]

        confidence = min(1.0, count / 30)  # Full confidence at 30+ samples
        booster = -mean_error * confidence * 0.5  # 50% correction strength (less than driver)

        if abs(booster) > 0.3:
            boosters["teams"][team] = round(booster, 2)
            direction = "↑ improve" if booster < 0 else "↓ worsen"
            print(f"  {team:15s}: {booster:+5.2f} ({direction} prediction by {abs(booster):.1f} positions)")

    return boosters


def save_boosters(boosters: dict, path: Path):
    """Save booster coefficients to JSON file."""
    with open(path, "w") as f:
        json.dump(boosters, f, indent=2)
    print(f"\nSaved boosters to {path}")


async def main():
    print("="*80)
    print("PREDICTION ERROR ANALYSIS")
    print("="*80)

    # Initialize service
    service = RacePredictionService()

    if service._model is None:
        print("ERROR: Model not trained. Please train the model first.")
        return

    # Collect errors from backtests
    print("\nCollecting backtest data for 2023-2024...")
    errors = await collect_backtest_errors(service, [2023, 2024])

    if not errors:
        print("No error data collected!")
        return

    print(f"\nCollected {len(errors)} prediction results")

    # Analyze errors
    driver_stats = analyze_driver_errors(errors)
    team_stats = analyze_team_errors(errors)

    # Calculate boosters
    boosters = calculate_booster_coefficients(driver_stats, team_stats)

    # Save boosters
    model_dir = Path("data/models")
    model_dir.mkdir(parents=True, exist_ok=True)
    save_boosters(boosters, model_dir / "boosters.json")

    # Save full analysis
    df = pd.DataFrame(errors)
    df.to_csv(model_dir / "error_analysis.csv", index=False)
    print(f"Saved detailed error analysis to {model_dir / 'error_analysis.csv'}")

    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total predictions analyzed: {len(errors)}")
    print(f"Overall MAE: {df['abs_error'].mean():.2f}")
    print(f"Overall Mean Signed Error: {df['signed_error'].mean():+.2f}")
    print(f"Drivers with boosters: {len(boosters['drivers'])}")
    print(f"Teams with boosters: {len(boosters['teams'])}")


if __name__ == "__main__":
    asyncio.run(main())
