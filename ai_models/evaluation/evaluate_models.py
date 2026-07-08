"""
Evaluate all models and ensemble on test data
Usage: python ai_models/evaluation/evaluate_models.py
       (can be run from any directory)
"""
import os, sys, json
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, classification_report,
    confusion_matrix, cohen_kappa_score
)
from sklearn.model_selection import train_test_split
from loguru import logger

# ── Resolve project root regardless of where the script is called from ────────
# Script is at: <project_root>/ai_models/evaluation/evaluate_models.py
_SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

# ── Set absolute model paths BEFORE importing ensemble_service ────────────────
# This ensures paths always resolve correctly regardless of .env location.
_AI = os.path.join(PROJECT_ROOT, "ai_models")
os.environ.setdefault("BERT_MODEL_PATH",              os.path.join(_AI, "bert",                 "saved_model"))
os.environ.setdefault("ROBERTA_MODEL_PATH",           os.path.join(_AI, "roberta",              "saved_model"))
os.environ.setdefault("BERT_MULTILINGUAL_MODEL_PATH", os.path.join(_AI, "bert_multilingual",    "saved_model"))
os.environ.setdefault("LSTM_MODEL_PATH",              os.path.join(_AI, "lstm",                 "saved_model"))
os.environ.setdefault("LOGISTIC_MODEL_PATH",          os.path.join(_AI, "logistic_regression",  "saved_model"))

from services.ensemble_service import (
    predict_bert, predict_roberta, predict_bert_multilingual,
    predict_lstm, predict_logistic, ensemble_predict
)

BERT_W         = 0.30
ROBERTA_W      = 0.25
MULTILINGUAL_W = 0.20
LSTM_W         = 0.15
LOGISTIC_W     = 0.10
DATA_PATH      = "ai_models/data/combined_dataset.csv"
SEED       = 42


def evaluate():
    logger.info("Starting model evaluation...")

    if not os.path.exists(DATA_PATH):
        logger.error(f"Dataset not found at {DATA_PATH}. Run training scripts first.")
        return

    df = pd.read_csv(DATA_PATH).dropna(subset=["text", "label"])
    df["label"] = df["label"].astype(int)

    _, test_df = train_test_split(df, test_size=0.2, random_state=SEED, stratify=df["label"])
    test_df = test_df.sample(min(500, len(test_df)), random_state=SEED) #Cap for speed
    logger.info(f"Evaluating on {len(test_df)} test samples...")

    texts  = test_df["text"].tolist()
    labels = test_df["label"].tolist()

    bert_probs, roberta_probs, multilingual_probs, lstm_probs, logreg_probs, ensemble_probs = [], [], [], [], [], []

    for i, text in enumerate(texts):
        if (i + 1) % 50 == 0:
            logger.info(f"Progress: {i+1}/{len(texts)}")
        b  = predict_bert(text)
        ro = predict_roberta(text)
        mu = predict_bert_multilingual(text)
        l  = predict_lstm(text)
        r  = predict_logistic(text)
        e  = BERT_W * b + ROBERTA_W * ro + MULTILINGUAL_W * mu + LSTM_W * l + LOGISTIC_W * r
        bert_probs.append(b)
        roberta_probs.append(ro)
        multilingual_probs.append(mu)
        lstm_probs.append(l)
        logreg_probs.append(r)
        ensemble_probs.append(e)

    def get_metrics(probs, threshold=0.5):
        preds = [1 if p >= threshold else 0 for p in probs]
        return {
            "accuracy":  round(accuracy_score(labels, preds), 4),
            "precision": round(precision_score(labels, preds, zero_division=0), 4),
            "recall":    round(recall_score(labels, preds, zero_division=0), 4),
            "f1":        round(f1_score(labels, preds, zero_division=0), 4),
            "auc":       round(roc_auc_score(labels, probs), 4),
            "kappa":     round(cohen_kappa_score(labels, preds), 4),
        }

    results = {
        "bert":              get_metrics(bert_probs),
        "roberta":           get_metrics(roberta_probs),
        "bert_multilingual": get_metrics(multilingual_probs),
        "lstm":              get_metrics(lstm_probs),
        "logistic":          get_metrics(logreg_probs),
        "ensemble":          get_metrics(ensemble_probs),
        "ensemble_weights": {
            "bert":              BERT_W,
            "roberta":           ROBERTA_W,
            "bert_multilingual": MULTILINGUAL_W,
            "lstm":              LSTM_W,
            "logistic":          LOGISTIC_W,
        },
        "test_size": len(test_df),
    }

    logger.info("\n" + "="*60)
    logger.info("EVALUATION RESULTS")
    logger.info("="*60)
    for model, metrics in results.items():
        if isinstance(metrics, dict) and "accuracy" in metrics:
            logger.info(f"\n{model.upper()}")
            for k, v in metrics.items():
                logger.info(f"  {k:12}: {v}")

    os.makedirs("ai_models/evaluation", exist_ok=True)
    with open("ai_models/evaluation/results.json", "w") as f:
        json.dump(results, f, indent=2)
    logger.info("\nResults saved to ai_models/evaluation/results.json")

    # Ensemble confusion matrix
    ens_preds = [1 if p >= 0.5 else 0 for p in ensemble_probs]
    cm = confusion_matrix(labels, ens_preds)
    logger.info(f"\nEnsemble Confusion Matrix:\n{cm}")

    return results


if __name__ == "__main__":
    evaluate()