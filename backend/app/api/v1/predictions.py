"""Prediction API endpoints."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from app.services import RacePredictionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predictions", tags=["predictions"])

# Global service instance
_prediction_service: RacePredictionService | None = None


def get_prediction_service() -> RacePredictionService:
    """Get or create the prediction service instance."""
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = RacePredictionService()
    return _prediction_service


class PredictionResponse(BaseModel):
    """Response model for race predictions."""
    driver: str
    rank: int
    predicted_position: float
    confidence: float
    fp1_position: int | None = None
    fp2_position: int | None = None
    fp3_position: int | None = None
    fp1_best_delta: float | None = None
    fp2_best_delta: float | None = None
    fp3_best_delta: float | None = None
    fp1_long_run: float | None = None
    fp2_long_run: float | None = None
    fp3_long_run: float | None = None
    actual_position: int | None = None
    position_error: int | None = None


class TrainingMetrics(BaseModel):
    """Training metrics response."""
    mae: float = Field(..., description="Mean Absolute Error")
    rmse: float = Field(..., description="Root Mean Squared Error")
    within_1_position: float = Field(..., description="% predictions within 1 position")
    within_3_positions: float = Field(..., description="% predictions within 3 positions")
    within_5_positions: float = Field(..., description="% predictions within 5 positions")
    training_samples: int
    top_features: dict[str, float]


class BacktestMetrics(BaseModel):
    """Backtest metrics."""
    mae: float
    within_1_position: float
    within_3_positions: float
    within_5_positions: float
    podium_correct: int
    winner_correct: bool


class BacktestResponse(BaseModel):
    """Backtest response with predictions and metrics."""
    predictions: list[PredictionResponse]
    metrics: BacktestMetrics


class ModelInfoResponse(BaseModel):
    """Model information response."""
    status: str
    feature_count: int | None = None
    features: list[str] | None = None
    model_type: str | None = None


@router.get("/race/{year}/{event}")
async def predict_race(
    year: int,
    event: str,
) -> list[PredictionResponse]:
    """
    Predict race finishing order based on practice sessions.

    Args:
        year: Season year
        event: Event name or round number

    Returns:
        List of predictions sorted by predicted position
    """
    service = get_prediction_service()

    try:
        # Try to parse event as int (round number)
        try:
            event_id: str | int = int(event)
        except ValueError:
            event_id = event

        predictions = await service.predict_race(year, event_id)
        return [PredictionResponse(**p) for p in predictions]

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/backtest/{year}/{event}")
async def backtest_race(
    year: int,
    event: str,
) -> BacktestResponse:
    """
    Backtest predictions against actual race results.

    Args:
        year: Season year
        event: Event name or round number

    Returns:
        Predictions with actual results and metrics
    """
    service = get_prediction_service()

    try:
        try:
            event_id: str | int = int(event)
        except ValueError:
            event_id = event

        result = await service.backtest(year, event_id)
        return BacktestResponse(
            predictions=[PredictionResponse(**p) for p in result["predictions"]],
            metrics=BacktestMetrics(**result["metrics"])
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


@router.post("/train")
async def train_model(
    background_tasks: BackgroundTasks,
    start_year: int = Query(2022, ge=2018, le=2024),
    end_year: int = Query(2024, ge=2018, le=2024),
) -> dict[str, str]:
    """
    Train the prediction model on historical data.

    This is a long-running operation that will run in the background.

    Args:
        start_year: First season to include in training
        end_year: Last season to include in training

    Returns:
        Status message
    """
    service = get_prediction_service()

    async def train_task():
        try:
            metrics = await service.train_model(start_year=start_year, end_year=end_year)
            logger.info(f"Training completed: {metrics}")
        except Exception as e:
            logger.error(f"Training failed: {e}")

    background_tasks.add_task(train_task)

    return {"status": "Training started in background", "start_year": str(start_year), "end_year": str(end_year)}


@router.post("/train/sync")
async def train_model_sync(
    start_year: int = Query(2022, ge=2018, le=2024),
    end_year: int = Query(2024, ge=2018, le=2024),
) -> TrainingMetrics:
    """
    Train the prediction model synchronously (waits for completion).

    Args:
        start_year: First season to include in training
        end_year: Last season to include in training

    Returns:
        Training metrics
    """
    service = get_prediction_service()

    try:
        metrics = await service.train_model(start_year=start_year, end_year=end_year)
        return TrainingMetrics(**metrics)
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.get("/model/info")
async def get_model_info() -> ModelInfoResponse:
    """
    Get information about the trained model.

    Returns:
        Model status and details
    """
    service = get_prediction_service()
    info = service.get_model_info()
    return ModelInfoResponse(**info)


@router.post("/collect-data")
async def collect_training_data(
    background_tasks: BackgroundTasks,
    start_year: int = Query(2022, ge=2018, le=2024),
    end_year: int = Query(2024, ge=2018, le=2024),
) -> dict[str, str]:
    """
    Collect training data from historical races.

    This downloads practice and race data from FastF1 for the specified seasons.
    This is a long-running operation that will run in the background.

    Args:
        start_year: First season to collect
        end_year: Last season to collect

    Returns:
        Status message
    """
    service = get_prediction_service()

    async def collect_task():
        try:
            df = await service.collect_training_data(start_year, end_year)
            logger.info(f"Collected {len(df)} training samples")
        except Exception as e:
            logger.error(f"Data collection failed: {e}")

    background_tasks.add_task(collect_task)

    return {"status": "Data collection started in background", "start_year": str(start_year), "end_year": str(end_year)}
