"""
Scheduled Retraining Pipeline
Collects verified feedback data and retrains models.

Each training script now warm-starts from its last saved checkpoint,
so retraining continues from where you left off rather than starting
from scratch. New verified feedback is appended to combined_dataset.csv
before the scripts are invoked.

NOTE: Run manually by an admin or schedule via cron after sufficient
verified feedback has accumulated (minimum 50 new verified samples).

Usage: python ai_models/training/retrain_pipeline.py
"""
import os, sys, json, asyncio
from datetime import datetime
from loguru import logger

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))


async def collect_retraining_data():
    """Fetch verified feedback from database."""
    from database.connection import AsyncSessionLocal
    from sqlalchemy import select
    from models import RetrainingData

    async with AsyncSessionLocal() as db:
        stmt   = select(RetrainingData).where(
            RetrainingData.verified == True,
            RetrainingData.used     == False,
        )
        result = await db.execute(stmt)
        items  = result.scalars().all()

        data = [
            {"text": item.text, "label": 1 if item.label == "FAKE" else 0}
            for item in items
        ]
        logger.info(f"Found {len(data)} verified samples for retraining.")

        for item in items:
            item.used = True
        await db.commit()

    return data


async def run_pipeline():
    logger.info("=" * 60)
    logger.info(f"Retraining Pipeline — {datetime.now().isoformat()}")
    logger.info("Warm-start: each model continues from its last checkpoint.")
    logger.info("=" * 60)

    # 1. Collect verified data
    new_data = await collect_retraining_data()
    if len(new_data) < 50:
        logger.warning(
            f"Only {len(new_data)} new samples — need ≥50 to retrain. Skipping."
        )
        return

    import pandas as pd
    existing_path = "ai_models/data/combined_dataset.csv"
    new_df        = pd.DataFrame(new_data)

    if os.path.exists(existing_path):
        existing_df = pd.read_csv(existing_path)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=["text"])
    else:
        combined_df = new_df

    combined_df.to_csv(existing_path, index=False)
    logger.info(
        f"Dataset updated: {len(combined_df)} total samples "
        f"(+{len(new_df)} new, after dedup)."
    )

    # 2. Retrain models — each script warm-starts from its own saved checkpoint
    logger.info("\nRetraining Logistic Regression (CPU, ~60s, warm-starts from coefficients)...")
    os.system("python ai_models/training/train_logistic.py")

    logger.info("\nRetraining LSTM (warm-starts from saved model.pt)...")    
    os.system("python ai_models/training/train_lstm.py")

    logger.info("\nRetraining BERT/RoBERTa/Multilingual BERT (warm-starts from saved fine-tuned weights, needs GPU)...")
    os.system("python ai_models/training/train_transformers.py all")

    # 3. Evaluate
    logger.info("\nRunning evaluation...")
    os.system("python ai_models/evaluation/evaluate_models.py")

    # 4. Log completion
    log_entry = {
        "timestamp":   datetime.now().isoformat(),
        "new_samples": len(new_data),
        "total":       len(combined_df),
        "warm_start":  True,
    }
    with open("ai_models/retraining_log.json", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    logger.info("\nRetraining pipeline complete!")


if __name__ == "__main__":
    asyncio.run(run_pipeline())