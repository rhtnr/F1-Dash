"""Race prediction service - ML-based race finishing order prediction."""

import json
import logging
from datetime import timedelta
from pathlib import Path
from typing import Any
import pickle

import numpy as np
import pandas as pd
import fastf1
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
import joblib

from app.config import get_settings

logger = logging.getLogger(__name__)

# Driver to team mapping (2023-2024 seasons)
DRIVER_TEAMS = {
    "VER": "Red Bull", "PER": "Red Bull",
    "LEC": "Ferrari", "SAI": "Ferrari",
    "HAM": "Mercedes", "RUS": "Mercedes",
    "NOR": "McLaren", "PIA": "McLaren",
    "ALO": "Aston Martin", "STR": "Aston Martin",
    "OCO": "Alpine", "GAS": "Alpine",
    "ALB": "Williams", "SAR": "Williams", "COL": "Williams",
    "BOT": "Alfa Romeo", "ZHO": "Alfa Romeo",
    "MAG": "Haas", "HUL": "Haas", "BEA": "Haas",
    "TSU": "AlphaTauri", "RIC": "AlphaTauri", "DEV": "AlphaTauri", "LAW": "AlphaTauri",
}


class RacePredictionService:
    """
    Service for predicting race finishing order from practice session data.

    Uses XGBoost/Gradient Boosting to predict race positions based on:
    - Practice session lap times (FP1, FP2, FP3)
    - Historical driver/team performance
    - Track characteristics
    """

    def __init__(self, cache_dir: Path | None = None):
        """Initialize the prediction service."""
        settings = get_settings()
        self._cache_dir = cache_dir or Path(settings.data_dir) / "fastf1_cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        fastf1.Cache.enable_cache(str(self._cache_dir))

        self._model_dir = Path(settings.data_dir) / "models"
        self._model_dir.mkdir(parents=True, exist_ok=True)

        self._model: XGBRegressor | None = None
        self._scaler: StandardScaler | None = None
        self._feature_columns: list[str] = []
        self._boosters: dict = {"drivers": {}, "teams": {}}
        self._use_boosters: bool = False  # Disabled - outlier removal made model accurate enough

        # Try to load existing model and boosters
        self._load_model()
        self._load_boosters()

    def _load_model(self) -> bool:
        """Load trained model from disk."""
        model_path = self._model_dir / "race_predictor.joblib"
        scaler_path = self._model_dir / "scaler.joblib"
        features_path = self._model_dir / "features.joblib"

        if model_path.exists() and scaler_path.exists() and features_path.exists():
            try:
                self._model = joblib.load(model_path)
                self._scaler = joblib.load(scaler_path)
                self._feature_columns = joblib.load(features_path)
                logger.info("Loaded existing prediction model")
                return True
            except Exception as e:
                logger.warning(f"Failed to load model: {e}")
        return False

    def _load_boosters(self) -> bool:
        """Load booster coefficients from disk."""
        boosters_path = self._model_dir / "boosters.json"

        if boosters_path.exists():
            try:
                with open(boosters_path) as f:
                    self._boosters = json.load(f)
                logger.info(f"Loaded boosters: {len(self._boosters.get('drivers', {}))} drivers, "
                           f"{len(self._boosters.get('teams', {}))} teams")
                return True
            except Exception as e:
                logger.warning(f"Failed to load boosters: {e}")
        return False

    def _get_booster(self, driver: str) -> float:
        """
        Get total booster adjustment for a driver.

        The booster adjusts the predicted position to correct for systematic biases.
        Positive booster = push prediction down (worse position)
        Negative booster = push prediction up (better position)
        """
        if not self._use_boosters:
            return 0.0

        driver_boost = self._boosters.get("drivers", {}).get(driver, 0.0)
        team = DRIVER_TEAMS.get(driver, "Unknown")
        team_boost = self._boosters.get("teams", {}).get(team, 0.0)

        # Combine driver and team boosters
        # Driver booster takes priority, team is a fallback/additional adjustment
        total_boost = driver_boost + team_boost * 0.3  # Team contributes 30%

        return total_boost

    def _save_model(self):
        """Save trained model to disk."""
        if self._model is None:
            return

        joblib.dump(self._model, self._model_dir / "race_predictor.joblib")
        joblib.dump(self._scaler, self._model_dir / "scaler.joblib")
        joblib.dump(self._feature_columns, self._model_dir / "features.joblib")
        logger.info("Saved prediction model")

    def _extract_practice_features(
        self,
        year: int,
        event: str | int,
        driver: str
    ) -> dict[str, float] | None:
        """
        Extract features from practice sessions for a driver.

        Features include:
        - Best lap time in each practice session (normalized to session fastest)
        - Average lap time in each session
        - Consistency (std dev of lap times)
        - Long run pace (average of 5+ lap stints)
        - Position in each session
        """
        features = {}

        for session_type in ["FP1", "FP2", "FP3"]:
            try:
                session = fastf1.get_session(year, event, session_type)
                session.load(laps=True, telemetry=False, weather=False, messages=False)

                laps = session.laps
                if laps.empty:
                    continue

                # Filter to valid quick laps (exclude pit laps, in/out laps)
                valid_laps = laps[
                    (laps["IsAccurate"] == True) &
                    (laps["LapTime"].notna()) &
                    (laps["PitOutTime"].isna()) &
                    (laps["PitInTime"].isna())
                ].copy()

                if valid_laps.empty:
                    continue

                # Convert lap times to seconds for outlier detection
                valid_laps["LapTimeSeconds"] = valid_laps["LapTime"].apply(
                    lambda x: x.total_seconds()
                )

                # Remove outliers using 107% rule (common F1 threshold)
                # Laps > 107% of fastest are likely traffic/issues
                session_fastest_raw = valid_laps["LapTimeSeconds"].min()
                max_valid_time = session_fastest_raw * 1.07
                valid_laps = valid_laps[valid_laps["LapTimeSeconds"] <= max_valid_time]

                # Also remove outliers using IQR method for remaining laps
                if len(valid_laps) > 4:
                    q1 = valid_laps["LapTimeSeconds"].quantile(0.25)
                    q3 = valid_laps["LapTimeSeconds"].quantile(0.75)
                    iqr = q3 - q1
                    upper_bound = q3 + 1.5 * iqr
                    valid_laps = valid_laps[valid_laps["LapTimeSeconds"] <= upper_bound]

                if valid_laps.empty:
                    continue

                # Session fastest time for normalization (after outlier removal)
                session_fastest = valid_laps["LapTimeSeconds"].min()

                # Get driver's laps
                driver_laps = valid_laps[valid_laps["Driver"] == driver]

                if driver_laps.empty:
                    # No data for this driver in this session
                    features[f"{session_type}_best_delta"] = 2.0  # Penalty for missing
                    features[f"{session_type}_avg_delta"] = 2.0
                    features[f"{session_type}_consistency"] = 1.0
                    features[f"{session_type}_position"] = 20
                    continue

                # Use pre-computed lap times in seconds
                driver_times = driver_laps["LapTimeSeconds"]

                # Best lap delta to session fastest
                best_time = driver_times.min()
                features[f"{session_type}_best_delta"] = best_time - session_fastest

                # Average lap delta
                avg_time = driver_times.mean()
                features[f"{session_type}_avg_delta"] = avg_time - session_fastest

                # Consistency (std dev)
                features[f"{session_type}_consistency"] = driver_times.std() if len(driver_times) > 1 else 0.5

                # Position in session (rank by best lap)
                driver_bests = valid_laps.groupby("Driver")["LapTimeSeconds"].min().sort_values()
                position = list(driver_bests.index).index(driver) + 1 if driver in driver_bests.index else 20
                features[f"{session_type}_position"] = position

                # Long run pace (laps on same tyre >= 5 laps)
                long_run_laps = []
                for stint in driver_laps["Stint"].unique():
                    stint_laps = driver_laps[driver_laps["Stint"] == stint]
                    if len(stint_laps) >= 5:
                        # Take laps 3-end to avoid fuel effect at start
                        long_run_times = stint_laps["LapTimeSeconds"].iloc[2:]
                        long_run_laps.extend(long_run_times.tolist())

                if long_run_laps:
                    features[f"{session_type}_long_run_delta"] = np.mean(long_run_laps) - session_fastest
                else:
                    features[f"{session_type}_long_run_delta"] = features.get(f"{session_type}_avg_delta", 2.0)

            except Exception as e:
                logger.warning(f"Failed to extract features from {session_type}: {e}")
                # Set default values for missing session
                features[f"{session_type}_best_delta"] = 2.0
                features[f"{session_type}_avg_delta"] = 2.0
                features[f"{session_type}_consistency"] = 1.0
                features[f"{session_type}_position"] = 20
                features[f"{session_type}_long_run_delta"] = 2.0

        if not features:
            return None

        return features

    def _get_race_result(self, year: int, event: str | int, driver: str) -> int | None:
        """Get race finishing position for a driver."""
        try:
            session = fastf1.get_session(year, event, "R")
            session.load(laps=False, telemetry=False, weather=False, messages=False)

            results = session.results
            driver_result = results[results["Abbreviation"] == driver]

            if not driver_result.empty:
                position = driver_result["Position"].iloc[0]
                if pd.notna(position):
                    return int(position)
        except Exception as e:
            logger.warning(f"Failed to get race result: {e}")

        return None

    async def collect_training_data(
        self,
        start_year: int = 2022,
        end_year: int = 2024
    ) -> pd.DataFrame:
        """
        Collect historical training data from multiple seasons.

        Returns DataFrame with features and target (race position).
        """
        logger.info(f"Collecting training data from {start_year} to {end_year}")

        all_data = []

        for year in range(start_year, end_year + 1):
            try:
                schedule = fastf1.get_event_schedule(year)
                # Filter to events that have already happened
                completed_events = schedule[schedule["EventDate"] < pd.Timestamp.now()]

                for _, event in completed_events.iterrows():
                    event_name = event["EventName"]
                    round_num = event["RoundNumber"]

                    logger.info(f"Processing {year} {event_name}")

                    try:
                        # Get race session to find drivers
                        race = fastf1.get_session(year, round_num, "R")
                        race.load(laps=False, telemetry=False, weather=False, messages=False)

                        drivers = race.results["Abbreviation"].tolist()

                        for driver in drivers:
                            if not driver:
                                continue

                            features = self._extract_practice_features(year, round_num, driver)
                            if features is None:
                                continue

                            race_position = self._get_race_result(year, round_num, driver)
                            if race_position is None:
                                continue

                            features["year"] = year
                            features["round"] = round_num
                            features["driver"] = driver
                            features["race_position"] = race_position

                            all_data.append(features)

                    except Exception as e:
                        logger.warning(f"Failed to process {year} {event_name}: {e}")
                        continue

            except Exception as e:
                logger.warning(f"Failed to get schedule for {year}: {e}")
                continue

        if not all_data:
            raise ValueError("No training data collected")

        df = pd.DataFrame(all_data)
        logger.info(f"Collected {len(df)} training samples")

        # Save training data
        df.to_csv(self._model_dir / "training_data.csv", index=False)

        return df

    async def train_model(
        self,
        training_data: pd.DataFrame | None = None,
        start_year: int = 2022,
        end_year: int = 2024
    ) -> dict[str, float]:
        """
        Train the race prediction model.

        Returns training metrics (MAE, RMSE, accuracy within positions).
        """
        logger.info("Training race prediction model")

        # Collect or load training data
        if training_data is None:
            data_path = self._model_dir / "training_data.csv"
            if data_path.exists():
                training_data = pd.read_csv(data_path)
            else:
                training_data = await self.collect_training_data(start_year, end_year)

        # Define feature columns (exclude metadata and target)
        metadata_cols = ["year", "round", "driver", "race_position"]
        self._feature_columns = [c for c in training_data.columns if c not in metadata_cols]

        # Prepare features and target
        X = training_data[self._feature_columns].fillna(training_data[self._feature_columns].median())
        y = training_data["race_position"]

        # Scale features
        self._scaler = StandardScaler()
        X_scaled = self._scaler.fit_transform(X)

        # Train XGBoost model
        self._model = XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            objective="reg:squarederror"
        )

        self._model.fit(X_scaled, y)

        # Calculate training metrics
        predictions = self._model.predict(X_scaled)

        mae = np.mean(np.abs(predictions - y))
        rmse = np.sqrt(np.mean((predictions - y) ** 2))
        within_1 = np.mean(np.abs(predictions - y) <= 1) * 100
        within_3 = np.mean(np.abs(predictions - y) <= 3) * 100
        within_5 = np.mean(np.abs(predictions - y) <= 5) * 100

        # Feature importance
        importance = dict(zip(self._feature_columns, self._model.feature_importances_))
        top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]

        metrics = {
            "mae": mae,
            "rmse": rmse,
            "within_1_position": within_1,
            "within_3_positions": within_3,
            "within_5_positions": within_5,
            "training_samples": len(y),
            "top_features": {k: float(v) for k, v in top_features}
        }

        logger.info(f"Model trained - MAE: {mae:.2f}, RMSE: {rmse:.2f}")
        logger.info(f"Accuracy within 1 pos: {within_1:.1f}%, within 3: {within_3:.1f}%")

        # Save model
        self._save_model()

        return metrics

    async def predict_race(
        self,
        year: int,
        event: str | int
    ) -> list[dict[str, Any]]:
        """
        Predict race finishing order for an upcoming/current event.

        Returns list of predictions sorted by predicted position.
        """
        if self._model is None:
            raise ValueError("Model not trained. Call train_model() first.")

        logger.info(f"Predicting race order for {year} {event}")

        # Get list of drivers from practice sessions
        drivers = set()
        for session_type in ["FP1", "FP2", "FP3"]:
            try:
                session = fastf1.get_session(year, event, session_type)
                session.load(laps=True, telemetry=False, weather=False, messages=False)
                drivers.update(session.laps["Driver"].unique())
            except Exception:
                continue

        if not drivers:
            raise ValueError(f"No practice data available for {year} {event}")

        predictions = []

        for driver in drivers:
            if not driver or pd.isna(driver):
                continue

            features = self._extract_practice_features(year, event, driver)
            if features is None:
                continue

            # Build feature vector
            feature_vector = []
            for col in self._feature_columns:
                feature_vector.append(features.get(col, 0))

            # Scale and predict
            X = np.array([feature_vector])
            X_scaled = self._scaler.transform(X)
            raw_predicted_position = self._model.predict(X_scaled)[0]

            # Apply booster coefficient to adjust for driver/team biases
            booster = self._get_booster(driver)
            adjusted_position = raw_predicted_position - booster

            # Get confidence based on practice consistency
            consistency = np.mean([
                features.get("FP1_consistency", 1),
                features.get("FP2_consistency", 1),
                features.get("FP3_consistency", 1)
            ])
            confidence = max(0, min(100, 100 - consistency * 50))

            predictions.append({
                "driver": driver,
                "predicted_position": float(adjusted_position),
                "predicted_position_raw": float(raw_predicted_position),
                "booster": float(booster),
                "confidence": float(confidence),
                "fp1_position": features.get("FP1_position"),
                "fp2_position": features.get("FP2_position"),
                "fp3_position": features.get("FP3_position"),
                "fp1_best_delta": features.get("FP1_best_delta"),
                "fp2_best_delta": features.get("FP2_best_delta"),
                "fp3_best_delta": features.get("FP3_best_delta"),
                "fp1_long_run": features.get("FP1_long_run_delta"),
                "fp2_long_run": features.get("FP2_long_run_delta"),
                "fp3_long_run": features.get("FP3_long_run_delta"),
            })

        # Sort by predicted position and assign actual ranks
        predictions.sort(key=lambda x: x["predicted_position"])
        for i, pred in enumerate(predictions, 1):
            pred["rank"] = i

        return predictions

    async def backtest(
        self,
        year: int,
        event: str | int
    ) -> dict[str, Any]:
        """
        Backtest the model on a historical race.

        Returns predictions vs actual results comparison.
        """
        if self._model is None:
            raise ValueError("Model not trained. Call train_model() first.")

        # Get predictions
        predictions = await self.predict_race(year, event)

        # Get actual results
        try:
            race = fastf1.get_session(year, event, "R")
            race.load(laps=False, telemetry=False, weather=False, messages=False)

            results = race.results[["Abbreviation", "Position"]].copy()
            results.columns = ["driver", "actual_position"]
            results_dict = dict(zip(results["driver"], results["actual_position"]))
        except Exception as e:
            raise ValueError(f"Failed to get race results: {e}")

        # Match predictions with actual results
        comparison = []
        for pred in predictions:
            driver = pred["driver"]
            actual = results_dict.get(driver)

            if actual is not None and not pd.isna(actual):
                pred["actual_position"] = int(actual)
                pred["position_error"] = abs(pred["rank"] - int(actual))
            else:
                pred["actual_position"] = None
                pred["position_error"] = None

            comparison.append(pred)

        # Calculate metrics
        valid_preds = [c for c in comparison if c["actual_position"] is not None]
        if valid_preds:
            errors = [c["position_error"] for c in valid_preds]
            mae = np.mean(errors)
            within_1 = sum(1 for e in errors if e <= 1) / len(errors) * 100
            within_3 = sum(1 for e in errors if e <= 3) / len(errors) * 100
            within_5 = sum(1 for e in errors if e <= 5) / len(errors) * 100

            # Check podium accuracy
            top3_predicted = [c["driver"] for c in comparison[:3]]
            top3_actual = [c["driver"] for c in sorted(valid_preds, key=lambda x: x["actual_position"])[:3]]
            podium_correct = len(set(top3_predicted) & set(top3_actual))

            # Check winner
            winner_predicted = comparison[0]["driver"] if comparison else None
            winner_actual = min(valid_preds, key=lambda x: x["actual_position"])["driver"] if valid_preds else None
            winner_correct = winner_predicted == winner_actual
        else:
            mae = within_1 = within_3 = within_5 = 0
            podium_correct = 0
            winner_correct = False

        return {
            "predictions": comparison,
            "metrics": {
                "mae": mae,
                "within_1_position": within_1,
                "within_3_positions": within_3,
                "within_5_positions": within_5,
                "podium_correct": podium_correct,
                "winner_correct": winner_correct
            }
        }

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the trained model."""
        if self._model is None:
            return {"status": "not_trained"}

        booster_info = {
            "enabled": self._use_boosters,
            "driver_count": len(self._boosters.get("drivers", {})),
            "team_count": len(self._boosters.get("teams", {})),
            "drivers": self._boosters.get("drivers", {}),
            "teams": self._boosters.get("teams", {}),
        }

        return {
            "status": "trained",
            "feature_count": len(self._feature_columns),
            "features": self._feature_columns,
            "model_type": "XGBoost Regressor",
            "model_params": self._model.get_params(),
            "boosters": booster_info
        }
