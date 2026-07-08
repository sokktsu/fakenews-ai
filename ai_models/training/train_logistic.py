"""
TF-IDF + Logistic Regression Training Script
Usage: python ai_models/training/train_logistic.py

Warm-start behaviour:
  - If a previously trained model exists at SAVE_PATH, it is loaded and
    training continues from its existing coefficients (warm_start=True).
  - TF-IDF is always refit on the full current dataset so the vocabulary
    stays up to date. Because max_features=100000 caps the output at a
    fixed dimension, the loaded model's coefficient shape stays compatible.
  - If no saved model exists, trains from scratch as before.

GPU note: scikit-learn is CPU-only. LogisticRegression with TF-IDF on
~100k samples typically finishes in under 60 seconds on CPU — GPU
acceleration is not needed here and offers no practical benefit.
"""
import os, json
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, classification_report, roc_auc_score,
    precision_score, recall_score, f1_score, cohen_kappa_score,
)
from loguru import logger
import re

SAVE_PATH = "ai_models/logistic_regression/saved_model"
DATA_PATH = "ai_models/data/combined_dataset.csv"
SEED      = 42

MODEL_FILE = os.path.join(SAVE_PATH, "model.joblib")
TFIDF_FILE = os.path.join(SAVE_PATH, "tfidf.joblib")

os.makedirs(SAVE_PATH, exist_ok=True)

try:
    import nltk
    nltk.download("stopwords", quiet=True)
    from nltk.corpus import stopwords
    STOPWORDS = set(stopwords.words("english"))
except:
    STOPWORDS = set()


def clean_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"http\S+|www\S+", "", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    words = text.split()
    words = [w for w in words if w not in STOPWORDS and len(w) > 2]
    return " ".join(words)


def load_dataset():
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
        logger.info(f"Loaded dataset: {len(df)} samples")
    else:
        logger.warning("Dataset not found. Using synthetic data.")
        fake = ["shocking exposed cover up conspiracy breaking urgent banned secret truth hidden mainstream"] * 500
        real = ["according research published experts confirm official statement data shows university journal"] * 500
        df   = pd.DataFrame({"text": fake + real, "label": [1]*500 + [0]*500})

    df = df.dropna(subset=["text", "label"])
    df["text"]  = df["text"].astype(str).apply(clean_text)
    df["label"] = pd.to_numeric(df["label"], errors="coerce").fillna(0).astype(int)
    df = df[df["text"].str.len() > 5]
    df = df.reset_index(drop=True)
    return df


def load_classifier() -> LogisticRegression:
    """
    Load existing model for warm-start if available, otherwise create fresh.
    warm_start=True tells sklearn to initialize from the loaded model's
    coefficients instead of random weights on the next .fit() call.
    """
    if os.path.exists(MODEL_FILE):
        logger.info(f"Checkpoint found at {MODEL_FILE}.")
        logger.info("Loading existing classifier — training will continue from last coefficients.")
        clf = joblib.load(MODEL_FILE)
        clf.warm_start = True
        # Bump max_iter slightly on retrain to allow the optimizer more room
        # to converge from the existing coefficient starting point
        clf.max_iter = max(clf.max_iter, 500)
    else:
        logger.info("No checkpoint found. Training fresh Logistic Regression.")
        clf = LogisticRegression(
            C            = 5.0,
            max_iter     = 1000,
            solver       = "lbfgs",
            class_weight = "balanced",
            random_state = SEED,
            warm_start   = True,
        )
    return clf


def log_metrics_summary(y_true, y_pred, y_prob=None):
    """Compact headline-metrics block (FAKE = positive class), including Cohen's
    kappa (agreement corrected for chance). Mirrors evaluate_models.py so the
    numbers are directly comparable between training and evaluation."""
    logger.info("\n--- METRICS SUMMARY (FAKE = positive) ---")
    logger.info(f"  accuracy : {accuracy_score(y_true, y_pred):.4f}")
    logger.info(f"  precision: {precision_score(y_true, y_pred, zero_division=0):.4f}")
    logger.info(f"  recall   : {recall_score(y_true, y_pred, zero_division=0):.4f}")
    logger.info(f"  f1       : {f1_score(y_true, y_pred, zero_division=0):.4f}")
    if y_prob is not None:
        logger.info(f"  auc      : {roc_auc_score(y_true, y_prob):.4f}")
    logger.info(f"  kappa    : {cohen_kappa_score(y_true, y_pred):.4f}")


def log_per_source_breakdown(y_true, y_pred, sources):
    """Accuracy and FAKE-recall split by source, so a headline score carried by
    one source (e.g. English foreign data) can't hide weakness on another
    (e.g. Filipino PH content). Groups the SAME test predictions by origin."""
    dfm = pd.DataFrame({"true": list(y_true), "pred": list(y_pred), "source": list(sources)})
    logger.info("\n--- ACCURACY BY SOURCE (test set) ---")
    logger.info(f"  {'Source':<26}{'N':>7}{'Accuracy':>10}{'FAKE recall':>13}")
    logger.info("  " + "-" * 54)
    for src, g in dfm.groupby("source"):
        acc     = (g["true"] == g["pred"]).mean()
        fake_g  = g[g["true"] == 1]
        fake_rc = (fake_g["pred"] == 1).mean() if len(fake_g) else float("nan")
        rc_str  = f"{fake_rc:.1%}" if len(fake_g) else "  n/a"
        logger.info(f"  {src:<26}{len(g):>7}{acc:>9.1%}{rc_str:>13}")


def train():
    logger.info("Starting Logistic Regression training...")

    df = load_dataset()

    texts  = df["text"].tolist()
    labels = df["label"].tolist()
    # Origin tag per row (added by prepare_dataset.py). Split it alongside so we
    # can report per-source accuracy. Older CSVs without it skip the breakdown.
    sources = df["source"].tolist() if "source" in df.columns else None

    if sources is not None:
        X_train, X_test, y_train, y_test, _s_train, s_test = train_test_split(
            texts, labels, sources,
            test_size=0.2, random_state=SEED, stratify=labels
        )
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels,
            test_size=0.2, random_state=SEED, stratify=labels
        )
        s_test = None
    logger.info(f"Train: {len(X_train)} | Test: {len(X_test)}")

    # TF-IDF is always refit on the full current dataset.
    # max_features=100000 keeps output dimension fixed so the loaded
    # model's coefficient shape stays compatible across retrains.
    vectorizer = TfidfVectorizer(
        max_features  = 100000,
        ngram_range   = (1, 3),
        sublinear_tf  = True,
        min_df        = 2,
        max_df        = 0.95,
        strip_accents = "unicode",
    )

    clf = load_classifier()

    logger.info("Fitting TF-IDF vectorizer on full training set...")
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec  = vectorizer.transform(X_test)

    logger.info("Training Logistic Regression classifier...")
    clf.fit(X_train_vec, y_train)

    joblib.dump(clf,        MODEL_FILE)
    joblib.dump(vectorizer, TFIDF_FILE)
    logger.info(f"Model saved to {SAVE_PATH}")

    y_pred   = clf.predict(X_test_vec)
    y_prob   = clf.predict_proba(X_test_vec)[:, 1]
    accuracy = accuracy_score(y_test, y_pred)
    auc      = roc_auc_score(y_test, y_prob)
    report   = classification_report(y_test, y_pred, target_names=["REAL", "FAKE"])

    logger.info(f"\n{report}")
    logger.info(f"Test Accuracy: {accuracy:.4f} | AUC: {auc:.4f}")

    log_metrics_summary(y_test, y_pred, y_prob)

    if s_test is not None:
        log_per_source_breakdown(y_test, y_pred, s_test)

    metrics = {"accuracy": accuracy, "auc": auc}
    with open(os.path.join(SAVE_PATH, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info("Logistic Regression training complete!")


if __name__ == "__main__":
    train()