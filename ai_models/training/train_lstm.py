"""
BiLSTM Training Script (PyTorch)
Usage: python ai_models/training/train_lstm.py

Rewrote from TensorFlow/Keras to PyTorch so GPU training works on Windows
via the same CUDA setup already used by BERT — no WSL2 or DirectML needed.

Architecture is equivalent to the original TF version:
  Embedding(50000, 128)
  → SpatialDropout(0.2)
  → BiLSTM(128, return_sequences=True)  + inter-LSTM dropout(0.2)
  → BiLSTM(64,  return_sequences=False)
  → Dense(64, ReLU) → Dropout(0.3) → Dense(1, Sigmoid)

Warm-start behaviour:
  - If model.pt + tokenizer.pkl exist at SAVE_PATH, training continues
    from those weights with the existing vocabulary.
  - If no checkpoint exists, builds fresh from scratch.

Note: tokenizer.pkl is now a SimpleTokenizer (pure Python, no TF dependency).
      If you have an old Keras tokenizer.pkl from the TF version, delete it
      so a fresh vocabulary is built by this script on first run.
"""
import os, json, pickle
import numpy as np
import pandas as pd
from collections import Counter
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, classification_report, precision_score,
    recall_score, f1_score, roc_auc_score, cohen_kappa_score,
)
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from loguru import logger
import re

SAVE_PATH  = "ai_models/lstm/saved_model"
DATA_PATH  = "ai_models/data/combined_dataset.csv"
MAX_WORDS  = 50000
MAX_LEN    = 200
EMBED_DIM  = 128
LSTM_UNITS = 128
BATCH_SIZE = 64
EPOCHS     = 10
SEED       = 42
LR         = 1e-3

MODEL_FILE     = os.path.join(SAVE_PATH, "model.pt")
TOKENIZER_FILE = os.path.join(SAVE_PATH, "tokenizer.pkl")

os.makedirs(SAVE_PATH, exist_ok=True)
torch.manual_seed(SEED)
np.random.seed(SEED)

# ── GPU detection ──────────────────────────────────────────────────────────────
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)
    logger.info(f"GPU detected: {torch.cuda.get_device_name(0)} — LSTM will train on GPU.")
else:
    logger.warning("No CUDA GPU detected — training on CPU.")


# ══════════════════════════════════════════════════════════════════════════════
# TOKENIZER  (pure Python, no TF dependency)
# ══════════════════════════════════════════════════════════════════════════════

class SimpleTokenizer:
    """
    Lightweight word tokenizer that mirrors the Keras Tokenizer API.
    Index 0 = padding, index 1 = <OOV>.
    """
    def __init__(self, num_words: int = None, oov_token: str = "<OOV>"):
        self.num_words  = num_words
        self.oov_token  = oov_token
        self.word_index: dict = {}

    def fit_on_texts(self, texts: list[str]):
        counter = Counter()
        for text in texts:
            counter.update(text.split())
        limit = (self.num_words - 2) if self.num_words else None
        self.word_index = {self.oov_token: 1}
        for i, (word, _) in enumerate(counter.most_common(limit), start=2):
            self.word_index[word] = i

    def texts_to_sequences(self, texts: list[str]) -> list[list[int]]:
        oov = self.word_index.get(self.oov_token, 1)
        return [
            [self.word_index.get(w, oov) for w in text.split()]
            for text in texts
        ]


def pad_sequences(sequences: list[list[int]], maxlen: int) -> np.ndarray:
    """Post-pad / post-truncate sequences to maxlen. Index 0 = pad."""
    out = np.zeros((len(sequences), maxlen), dtype=np.int64)
    for i, seq in enumerate(sequences):
        seq = seq[:maxlen]
        out[i, :len(seq)] = seq
    return out


# ══════════════════════════════════════════════════════════════════════════════
# DATASET
# ══════════════════════════════════════════════════════════════════════════════

class TextDataset(Dataset):
    def __init__(self, sequences: np.ndarray, labels: list[int]):
        self.x = torch.tensor(sequences, dtype=torch.long)
        self.y = torch.tensor(labels,    dtype=torch.float32)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        return self.x[idx], self.y[idx]


# ══════════════════════════════════════════════════════════════════════════════
# MODEL
# ══════════════════════════════════════════════════════════════════════════════

class SpatialDropout(nn.Module):
    """Drops entire embedding feature maps (equivalent to Keras SpatialDropout1D)."""
    def __init__(self, p: float):
        super().__init__()
        self.p = p

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, embed_dim)
        if not self.training or self.p == 0:
            return x
        # Drop whole channels across the sequence dimension
        mask = torch.ones(x.size(0), 1, x.size(2), device=x.device)
        mask = torch.nn.functional.dropout(mask, p=self.p, training=True)
        return x * mask


class BiLSTMClassifier(nn.Module):
    """
    Bidirectional LSTM classifier.

    Layer sizes match the original TF version exactly:
      Embedding   → (batch, seq, 128)
      BiLSTM-1    → (batch, seq, 256)   [128 units × 2 directions]
      BiLSTM-2    → (batch, seq, 128)   [64  units × 2 directions]
      last step   → (batch, 128)
      Linear+ReLU → (batch, 64)
      Linear+Sig  → (batch, 1)
    """
    def __init__(self, vocab_size: int):
        super().__init__()
        self.embedding      = nn.Embedding(vocab_size, EMBED_DIM, padding_idx=0)
        self.spatial_drop   = SpatialDropout(0.2)
        self.lstm1          = nn.LSTM(EMBED_DIM,      LSTM_UNITS,      batch_first=True, bidirectional=True)
        self.lstm1_drop     = nn.Dropout(0.2)
        self.lstm2          = nn.LSTM(LSTM_UNITS * 2, LSTM_UNITS // 2, batch_first=True, bidirectional=True)
        self.fc1            = nn.Linear(LSTM_UNITS, 64)   # LSTM_UNITS//2 * 2 directions = LSTM_UNITS
        self.relu           = nn.ReLU()
        self.dropout        = nn.Dropout(0.3)
        self.fc2            = nn.Linear(64, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        emb       = self.spatial_drop(self.embedding(x))  # (B, S, 128)
        out, _    = self.lstm1(emb)                        # (B, S, 256)
        out       = self.lstm1_drop(out)
        out, _    = self.lstm2(out)                        # (B, S, 128)
        out       = out[:, -1, :]                          # last timestep (B, 128)
        out       = self.dropout(self.relu(self.fc1(out))) # (B, 64)
        out       = self.fc2(out)                          # (B, 1)
        return torch.sigmoid(out).squeeze(1)


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def preprocess_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"http\S+|www\S+", "", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_dataset():
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
        logger.info(f"Loaded dataset: {len(df)} samples")
    else:
        logger.warning("Dataset not found. Using synthetic data.")
        fake = ["shocking exposed conspiracy urgent banned secret truth"] * 1000
        real = ["research published experts confirm official statement data"] * 1000
        df   = pd.DataFrame({"text": fake + real, "label": [1]*1000 + [0]*1000})

    df = df.dropna(subset=["text", "label"])
    df["text"]  = df["text"].astype(str).apply(preprocess_text)
    df["label"] = pd.to_numeric(df["label"], errors="coerce").fillna(0).astype(int)
    df = df[df["text"].str.len() > 5].reset_index(drop=True)
    return df


def load_checkpoint(X_train: list):
    """Load existing checkpoint or build fresh. Returns (model, tokenizer, vocab_size)."""
    if os.path.exists(MODEL_FILE) and os.path.exists(TOKENIZER_FILE):
        logger.info(f"Checkpoint found — continuing from {SAVE_PATH}.")
        logger.info("Note: new words not in the saved vocabulary will map to <OOV>.")
        with open(TOKENIZER_FILE, "rb") as f:
            tokenizer = pickle.load(f)
        if not isinstance(tokenizer, SimpleTokenizer):
            logger.warning("Old Keras tokenizer detected — rebuilding vocabulary with SimpleTokenizer.")
            tokenizer = SimpleTokenizer(num_words=MAX_WORDS, oov_token="<OOV>")
            tokenizer.fit_on_texts(X_train)
            with open(TOKENIZER_FILE, "wb") as f:
                pickle.dump(tokenizer, f)
        vocab_size = min(len(tokenizer.word_index) + 1, MAX_WORDS)
        model = BiLSTMClassifier(vocab_size).to(DEVICE)
        model.load_state_dict(torch.load(MODEL_FILE, map_location=DEVICE))
    else:
        logger.info("No checkpoint found — building fresh model.")
        tokenizer = SimpleTokenizer(num_words=MAX_WORDS, oov_token="<OOV>")
        tokenizer.fit_on_texts(X_train)
        with open(TOKENIZER_FILE, "wb") as f:
            pickle.dump(tokenizer, f)
        vocab_size = min(len(tokenizer.word_index) + 1, MAX_WORDS)
        model = BiLSTMClassifier(vocab_size).to(DEVICE)

    return model, tokenizer, vocab_size


# ══════════════════════════════════════════════════════════════════════════════
# TRAINING LOOP
# ══════════════════════════════════════════════════════════════════════════════

def run_epoch(model, loader, criterion, optimizer=None, train=True):
    model.train(train)
    total_loss, correct, total = 0.0, 0, 0
    with torch.set_grad_enabled(train):
        for xb, yb in loader:
            xb, yb = xb.to(DEVICE), yb.to(DEVICE)
            preds = model(xb)
            loss  = criterion(preds, yb)
            if train:
                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
            total_loss += loss.item() * len(yb)
            correct    += ((preds >= 0.5).float() == yb).sum().item()
            total      += len(yb)
    return total_loss / total, correct / total


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
    logger.info("Starting BiLSTM training (PyTorch)...")
    logger.info(f"Device: {DEVICE}")

    df = load_dataset()

    texts  = df["text"].tolist()
    labels = df["label"].tolist()
    # Origin tag per row (added by prepare_dataset.py). Split it alongside the
    # test set so we can report per-source accuracy. The train/val split below
    # doesn't need it. Older CSVs without the column skip the breakdown.
    sources = df["source"].tolist() if "source" in df.columns else None

    if sources is not None:
        X_train, X_test, y_train, y_test, _s_train, s_test = train_test_split(
            texts, labels, sources, test_size=0.2, random_state=SEED, stratify=labels
        )
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.2, random_state=SEED, stratify=labels
        )
        s_test = None
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.15, random_state=SEED, stratify=y_train
    )
    logger.info(f"Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")

    model, tokenizer, vocab_size = load_checkpoint(X_train)
    logger.info(f"Vocab size: {vocab_size} | Model params: {sum(p.numel() for p in model.parameters()):,}")

    def encode(texts_list):
        return pad_sequences(tokenizer.texts_to_sequences(texts_list), MAX_LEN)

    train_loader = DataLoader(TextDataset(encode(X_train), y_train),
                              batch_size=BATCH_SIZE, shuffle=True,  num_workers=0)
    val_loader   = DataLoader(TextDataset(encode(X_val),   y_val),
                              batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    test_loader  = DataLoader(TextDataset(encode(X_test),  y_test),
                              batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", factor=0.5, patience=2
    )

    best_val_acc  = 0.0
    best_state    = None
    patience_ctr  = 0
    PATIENCE      = 3
    val_acc_history = []

    for epoch in range(1, EPOCHS + 1):
        tr_loss, tr_acc = run_epoch(model, train_loader, criterion, optimizer, train=True)
        vl_loss, vl_acc = run_epoch(model, val_loader,   criterion, train=False)
        scheduler.step(vl_acc)
        val_acc_history.append(vl_acc)

        logger.info(
            f"Epoch {epoch:02d}/{EPOCHS} | "
            f"train_loss={tr_loss:.4f} train_acc={tr_acc:.4f} | "
            f"val_loss={vl_loss:.4f} val_acc={vl_acc:.4f}"
        )

        if vl_acc > best_val_acc:
            best_val_acc = vl_acc
            best_state   = {k: v.clone() for k, v in model.state_dict().items()}
            torch.save(best_state, os.path.join(SAVE_PATH, "best_model.pt"))
            patience_ctr = 0
        else:
            patience_ctr += 1
            if patience_ctr >= PATIENCE:
                logger.info(f"Early stopping at epoch {epoch} (no val_acc improvement for {PATIENCE} epochs).")
                break

    # Restore best weights
    if best_state:
        model.load_state_dict(best_state)
    torch.save(model.state_dict(), MODEL_FILE)
    logger.info(f"Model saved to {MODEL_FILE}")

    # ── Test evaluation ────────────────────────────────────────────────────────
    model.eval()
    all_preds, all_probs = [], []
    with torch.no_grad():
        for xb, _ in test_loader:
            probs = model(xb.to(DEVICE)).cpu().numpy()
            all_probs.extend(probs.tolist())
            all_preds.extend((probs >= 0.5).astype(int).tolist())

    accuracy = accuracy_score(y_test, all_preds)
    report   = classification_report(y_test, all_preds, target_names=["REAL", "FAKE"])
    logger.info(f"\n{report}")
    logger.info(f"Test Accuracy: {accuracy:.4f}")

    log_metrics_summary(y_test, all_preds, all_probs)

    if s_test is not None:
        log_per_source_breakdown(y_test, all_preds, s_test)

    metrics = {
        "accuracy":     round(accuracy, 4),
        "best_val_acc": round(best_val_acc, 4),
    }
    with open(os.path.join(SAVE_PATH, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info("BiLSTM (PyTorch) training complete!")


if __name__ == "__main__":
    train()