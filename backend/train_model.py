#!/usr/bin/env python3
"""Script to train the race prediction model on historical data."""

import asyncio
import logging
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.prediction_service import RacePredictionService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Train the model on historical data."""
    logger.info("Initializing prediction service...")
    service = RacePredictionService()

    # Check if we have training data already
    data_path = service._model_dir / "training_data.csv"

    if not data_path.exists():
        logger.info("Collecting training data from 2022-2024...")
        logger.info("This will take a while as it downloads data from FastF1...")
        df = await service.collect_training_data(start_year=2022, end_year=2024)
        logger.info(f"Collected {len(df)} training samples")
    else:
        logger.info(f"Using existing training data from {data_path}")

    # Train the model
    logger.info("Training model...")
    metrics = await service.train_model(start_year=2022, end_year=2024)

    logger.info("=" * 50)
    logger.info("TRAINING COMPLETE")
    logger.info("=" * 50)
    logger.info(f"Mean Absolute Error: {metrics['mae']:.2f} positions")
    logger.info(f"Root Mean Squared Error: {metrics['rmse']:.2f}")
    logger.info(f"Accuracy within 1 position: {metrics['within_1_position']:.1f}%")
    logger.info(f"Accuracy within 3 positions: {metrics['within_3_positions']:.1f}%")
    logger.info(f"Accuracy within 5 positions: {metrics['within_5_positions']:.1f}%")
    logger.info(f"Training samples: {metrics['training_samples']}")
    logger.info("")
    logger.info("Top features:")
    for feature, importance in metrics['top_features'].items():
        logger.info(f"  {feature}: {importance:.4f}")

    # Run a backtest on 2024 Bahrain GP
    logger.info("")
    logger.info("=" * 50)
    logger.info("BACKTEST: 2024 Bahrain GP")
    logger.info("=" * 50)

    try:
        backtest = await service.backtest(2024, 1)
        logger.info(f"MAE: {backtest['metrics']['mae']:.2f} positions")
        logger.info(f"Within 1 position: {backtest['metrics']['within_1_position']:.1f}%")
        logger.info(f"Within 3 positions: {backtest['metrics']['within_3_positions']:.1f}%")
        logger.info(f"Podium correct: {backtest['metrics']['podium_correct']}/3")
        logger.info(f"Winner correct: {backtest['metrics']['winner_correct']}")

        logger.info("")
        logger.info("Predictions vs Actual:")
        for pred in backtest['predictions'][:10]:
            actual = pred.get('actual_position', '?')
            error = pred.get('position_error', '-')
            logger.info(f"  {pred['rank']:2}. {pred['driver']:3} (Actual: {actual}, Error: {error})")
    except Exception as e:
        logger.warning(f"Backtest failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
