"""
train_transformers.py — Unified Transformer Fine-tuning Script
Handles BERT, RoBERTa, and Multilingual BERT from one file.

Usage:
    python ai_models/training/train_transformers.py bert
    python ai_models/training/train_transformers.py roberta
    python ai_models/training/train_transformers.py multilingual

Each model saves to its own directory and warm-starts from its own
checkpoint independently — running one does not affect the others.

Warm-start behaviour:
  - If a previously fine-tuned model exists at the model's SAVE_PATH,
    training continues FROM those weights (not from scratch).
  - If no saved model exists, downloads from HuggingFace and trains fresh.
"""
import os, sys, json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, classification_report, precision_score,
    recall_score, f1_score, roc_auc_score, cohen_kappa_score,
)
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback,
)
import torch
from torch.utils.data import Dataset
from loguru import logger
import re

# ── Model configs ──────────────────────────────────────────────────────────────
# Add new transformer models here without touching any other code.
CONFIGS = {
    "bert": {
        "model_name": "bert-base-uncased",
        "save_path":  "ai_models/bert/saved_model",
        "label":      "BERT (English)",
        "log_dir":    "logs/bert",
    },
    "roberta": {
        "model_name": "roberta-base",
        "save_path":  "ai_models/roberta/saved_model",
        "label":      "RoBERTa (English)",
        "log_dir":    "logs/roberta",
    },
    "multilingual": {
        "model_name": "bert-base-multilingual-cased",
        "save_path":  "ai_models/bert_multilingual/saved_model",
        "label":      "Multilingual BERT (104 languages incl. Filipino)",
        "log_dir":    "logs/bert_multilingual",
    },
}

DATA_PATH  = "ai_models/data/combined_dataset.csv"
MAX_LEN    = 512
BATCH_SIZE = 8
EPOCHS     = 3
LR         = 2e-5
SEED       = 42


class FakeNewsDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len):
        self.encodings = tokenizer(
            list(texts),
            truncation=True,
            padding=True,
            max_length=max_len,
            return_tensors="pt",
        )
        self.labels = torch.tensor(list(labels), dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {k: v[idx] for k, v in self.encodings.items()}
        item["labels"] = self.labels[idx]
        return item


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {"accuracy": accuracy_score(labels, preds)}


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
    (e.g. Filipino PH content). This groups the SAME test predictions by origin
    instead of averaging them into one number."""
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


def clean_text(text: str) -> str:
    text = str(text)
    text = re.sub(r"http\S+|www\S+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_dataset():
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
        logger.info(f"Loaded dataset: {len(df)} samples")
    else:
        logger.warning("Dataset not found. Using synthetic data.")
        fake = ["SHOCKING: They don't want you to know this secret cure!"] * 200
        real = ["According to a peer-reviewed study published in the Journal of Medicine..."] * 200
        df   = pd.DataFrame({"text": fake + real, "label": [1]*200 + [0]*200})

    df = df.dropna(subset=["text", "label"])
    df["text"]  = df["text"].astype(str).apply(clean_text)
    df["label"] = pd.to_numeric(df["label"], errors="coerce").fillna(0).astype(int)
    df = df[df["text"].str.len() > 10]
    df = df.reset_index(drop=True)

    # Sanity check only — dedup (exact + near-dup) is owned by
    # prepare_dataset.py, the sole writer of combined_dataset.csv.
    dups = int(df["text"].duplicated().sum())
    if dups:
        logger.warning(f"{dups} duplicate texts found in {DATA_PATH} — "
                       f"re-run: python ai_models/data/prepare_dataset.py")
    return df


def load_model_and_tokenizer(model_name: str, save_path: str):
    """
    Load from existing fine-tuned checkpoint if available,
    otherwise download from HuggingFace and start fresh.
    AutoTokenizer / AutoModelForSequenceClassification handle
    BERT, RoBERTa, and Multilingual BERT automatically.
    """
    checkpoint = os.path.join(save_path, "config.json")
    if os.path.exists(checkpoint):
        logger.info(f"Checkpoint found at {save_path}.")
        logger.info("Loading fine-tuned weights — training will continue from last checkpoint.")
        tokenizer = AutoTokenizer.from_pretrained(save_path)
        model     = AutoModelForSequenceClassification.from_pretrained(save_path)
    else:
        logger.info(f"No checkpoint found. Starting fresh from {model_name}.")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model     = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
    return model, tokenizer


def train(model_key: str):
    if model_key not in CONFIGS:
        logger.error(f"Unknown model key: '{model_key}'. Choose from: {list(CONFIGS.keys())}")
        sys.exit(1)

    cfg = CONFIGS[model_key]
    os.makedirs(cfg["save_path"], exist_ok=True)

    logger.info(f"Starting fine-tuning: {cfg['label']}")

    df = load_dataset()

    texts  = df["text"].tolist()
    labels = df["label"].tolist()
    # Origin tag per row (added by prepare_dataset.py). Split it alongside so we
    # can report per-source accuracy on the test set. Older CSVs without the
    # column fall back to no breakdown.
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

    model, tokenizer = load_model_and_tokenizer(cfg["model_name"], cfg["save_path"])

    train_dataset = FakeNewsDataset(X_train, y_train, tokenizer, MAX_LEN)
    eval_dataset  = FakeNewsDataset(X_test,  y_test,  tokenizer, MAX_LEN)

    training_args = TrainingArguments(
        output_dir                  = cfg["save_path"],
        num_train_epochs            = EPOCHS,
        per_device_train_batch_size = BATCH_SIZE,
        per_device_eval_batch_size  = BATCH_SIZE,
        warmup_steps                = 200,
        weight_decay                = 0.01,
        learning_rate               = LR,
        eval_strategy               = "epoch",
        save_strategy               = "epoch",
        save_total_limit            = 2,
        load_best_model_at_end      = True,
        metric_for_best_model       = "accuracy",
        logging_dir                 = cfg["log_dir"],
        logging_steps               = 50,
        seed                        = SEED,
        fp16                        = torch.cuda.is_available(),
        report_to                   = "none",
    )

    trainer = Trainer(
        model           = model,
        args            = training_args,
        train_dataset   = train_dataset,
        eval_dataset    = eval_dataset,
        compute_metrics = compute_metrics,
        callbacks       = [EarlyStoppingCallback(early_stopping_patience=2)],
    )

    trainer.train()

    model.save_pretrained(cfg["save_path"])
    tokenizer.save_pretrained(cfg["save_path"])
    logger.info(f"Model saved to {cfg['save_path']}")

    preds_output = trainer.predict(eval_dataset)
    logits       = preds_output.predictions
    preds        = np.argmax(logits, axis=-1)
    # Softmax over the 2 logits → probability of the FAKE class (index 1), for AUC.
    exp          = np.exp(logits - logits.max(axis=1, keepdims=True))
    fake_probs   = exp[:, 1] / exp.sum(axis=1)
    accuracy     = accuracy_score(y_test, preds)
    report       = classification_report(y_test, preds, target_names=["REAL", "FAKE"])

    logger.info(f"\n{report}")
    logger.info(f"Test Accuracy: {accuracy:.4f}")

    log_metrics_summary(y_test, preds, fake_probs)

    if s_test is not None:
        log_per_source_breakdown(y_test, preds, s_test)

    metrics = {"accuracy": accuracy, "model": model_key}
    with open(os.path.join(cfg["save_path"], "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"{cfg['label']} fine-tuning complete!")


if __name__ == "__main__":
    key = sys.argv[1].lower() if len(sys.argv) > 1 else "bert"
    if key == "all":
        for model_key in CONFIGS:
            logger.info(f"\n{'='*60}")
            logger.info(f"Starting {CONFIGS[model_key]['label']} ({list(CONFIGS.keys()).index(model_key)+1}/{len(CONFIGS)})")
            logger.info(f"{'='*60}")
            train(model_key)
        logger.info("\nAll models trained successfully.")
    else:
        train(key)