"""
Ensemble AI Service
Combines BERT (30%) + RoBERTa (25%) + Multilingual BERT (20%)
         + LSTM (15%) + Logistic Regression (10%)

Weights are read from .env so you can tune them without touching this file.
Add these to your .env:
    BERT_WEIGHT=0.30
    ROBERTA_WEIGHT=0.25
    BERT_MULTILINGUAL_WEIGHT=0.20
    LSTM_WEIGHT=0.15
    LOGISTIC_WEIGHT=0.10
"""
from __future__ import annotations
import os, re, pickle
import numpy as np
import torch
import torch.nn as nn
from typing import Optional
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

BERT_WEIGHT              = float(os.getenv("BERT_WEIGHT",              0.30))
ROBERTA_WEIGHT           = float(os.getenv("ROBERTA_WEIGHT",           0.25))
BERT_MULTILINGUAL_WEIGHT = float(os.getenv("BERT_MULTILINGUAL_WEIGHT", 0.20))
LSTM_WEIGHT              = float(os.getenv("LSTM_WEIGHT",              0.15))
LOGISTIC_WEIGHT          = float(os.getenv("LOGISTIC_WEIGHT",          0.10))

# ── SimpleTokenizer ───────────────────────────────────────────────────────────
# Defined here (not just in train_lstm.py) so pickle can always find it
# regardless of which script is running as __main__.

class SimpleTokenizer:
    """Lightweight word tokenizer matching the one used in train_lstm.py."""
    def __init__(self, num_words=None, oov_token="<OOV>"):
        self.num_words  = num_words
        self.oov_token  = oov_token
        self.word_index: dict = {}

    def fit_on_texts(self, texts):
        from collections import Counter
        counter = Counter()
        for text in texts:
            counter.update(text.split())
        limit = (self.num_words - 2) if self.num_words else None
        self.word_index = {self.oov_token: 1}
        for i, (word, _) in enumerate(counter.most_common(limit), start=2):
            self.word_index[word] = i

    def texts_to_sequences(self, texts):
        oov = self.word_index.get(self.oov_token, 1)
        return [[self.word_index.get(w, oov) for w in text.split()] for text in texts]


# ── LSTM architecture (must match train_lstm.py exactly) ─────────────────────
_EMBED_DIM  = 128
_LSTM_UNITS = 128
_MAX_WORDS  = 50000
_MAX_LEN    = 200


class _SpatialDropout(nn.Module):
    def __init__(self, p):
        super().__init__()
        self.p = p

    def forward(self, x):
        if not self.training or self.p == 0:
            return x
        mask = torch.ones(x.size(0), 1, x.size(2), device=x.device)
        mask = nn.functional.dropout(mask, p=self.p, training=True)
        return x * mask


class _BiLSTMClassifier(nn.Module):
    def __init__(self, vocab_size):
        super().__init__()
        self.embedding    = nn.Embedding(vocab_size, _EMBED_DIM, padding_idx=0)
        self.spatial_drop = _SpatialDropout(0.2)
        self.lstm1        = nn.LSTM(_EMBED_DIM,      _LSTM_UNITS,      batch_first=True, bidirectional=True)
        self.lstm1_drop   = nn.Dropout(0.2)
        self.lstm2        = nn.LSTM(_LSTM_UNITS * 2, _LSTM_UNITS // 2, batch_first=True, bidirectional=True)
        self.fc1          = nn.Linear(_LSTM_UNITS, 64)
        self.relu         = nn.ReLU()
        self.dropout      = nn.Dropout(0.3)
        self.fc2          = nn.Linear(64, 1)

    def forward(self, x):
        emb    = self.spatial_drop(self.embedding(x))
        out, _ = self.lstm1(emb)
        out    = self.lstm1_drop(out)
        out, _ = self.lstm2(out)
        out    = out[:, -1, :]
        out    = self.dropout(self.relu(self.fc1(out)))
        return torch.sigmoid(self.fc2(out)).squeeze(1)


# ── Lazy singletons ───────────────────────────────────────────────────────────
_bert_pipeline              = None
_roberta_pipeline           = None
_bert_multilingual_pipeline = None
_lstm_model                 = None
_lstm_tokenizer             = None
_logistic_model             = None
_tfidf_vectorizer           = None


def _get_bert():
    global _bert_pipeline
    if _bert_pipeline is None:
        try:
            from transformers import pipeline
            path = os.getenv("BERT_MODEL_PATH", "ai_models/bert/saved_model")
            if os.path.exists(path):
                _bert_pipeline = pipeline("text-classification", model=path,
                                          tokenizer=path, device=-1,
                                          truncation=True, max_length=512)
                logger.info("BERT loaded.")
            else:
                _bert_pipeline = pipeline("text-classification",
                                          model="mrm8488/bert-tiny-finetuned-fake-news",
                                          device=-1, truncation=True, max_length=512)
                logger.info("BERT loaded from HuggingFace Hub (fallback).")
        except Exception as e:
            logger.warning(f"BERT load failed: {e}")
    return _bert_pipeline


def _get_roberta():
    global _roberta_pipeline
    if _roberta_pipeline is None:
        try:
            from transformers import pipeline
            path = os.getenv("ROBERTA_MODEL_PATH", "ai_models/roberta/saved_model")
            if os.path.exists(path):
                _roberta_pipeline = pipeline("text-classification", model=path,
                                             tokenizer=path, device=-1,
                                             truncation=True, max_length=512)
                logger.info("RoBERTa loaded.")
            else:
                logger.warning("RoBERTa model not found — falling back to heuristic.")
        except Exception as e:
            logger.warning(f"RoBERTa load failed: {e}")
    return _roberta_pipeline


def _get_bert_multilingual():
    global _bert_multilingual_pipeline
    if _bert_multilingual_pipeline is None:
        try:
            from transformers import pipeline
            path = os.getenv("BERT_MULTILINGUAL_MODEL_PATH",
                             "ai_models/bert_multilingual/saved_model")
            if os.path.exists(path):
                _bert_multilingual_pipeline = pipeline(
                    "text-classification", model=path,
                    tokenizer=path, device=-1,
                    truncation=True, max_length=512
                )
                logger.info("Multilingual BERT loaded.")
            else:
                logger.warning("Multilingual BERT model not found — falling back to heuristic.")
        except Exception as e:
            logger.warning(f"Multilingual BERT load failed: {e}")
    return _bert_multilingual_pipeline


def _get_lstm():
    global _lstm_model, _lstm_tokenizer
    if _lstm_model is None:
        try:
            path           = os.getenv("LSTM_MODEL_PATH", "ai_models/lstm/saved_model")
            model_file     = os.path.join(path, "model.pt")
            tokenizer_file = os.path.join(path, "tokenizer.pkl")

            if os.path.exists(model_file) and os.path.exists(tokenizer_file):
                # Inject SimpleTokenizer into __main__ so pickle can find it
                # regardless of which script is running as __main__
                import __main__
                if not hasattr(__main__, "SimpleTokenizer"):
                    __main__.SimpleTokenizer = SimpleTokenizer

                with open(tokenizer_file, "rb") as f:
                    _lstm_tokenizer = pickle.load(f)
                vocab_size  = min(len(_lstm_tokenizer.word_index) + 1, _MAX_WORDS)
                _lstm_model = _BiLSTMClassifier(vocab_size)
                _lstm_model.load_state_dict(
                    torch.load(model_file, map_location=torch.device("cpu"))
                )
                _lstm_model.eval()
                logger.info("LSTM (PyTorch) loaded.")
            else:
                logger.warning("LSTM model.pt not found — falling back to heuristic.")
        except Exception as e:
            logger.warning(f"LSTM load failed: {e}")
    return _lstm_model, _lstm_tokenizer


def _get_logistic():
    global _logistic_model, _tfidf_vectorizer
    if _logistic_model is None:
        try:
            import joblib
            path       = os.getenv("LOGISTIC_MODEL_PATH",
                                   "ai_models/logistic_regression/saved_model")
            model_file = os.path.join(path, "model.joblib")
            tfidf_file = os.path.join(path, "tfidf.joblib")
            if os.path.exists(model_file):
                _logistic_model   = joblib.load(model_file)
                _tfidf_vectorizer = joblib.load(tfidf_file)
                logger.info("Logistic Regression loaded.")
        except Exception as e:
            logger.warning(f"LogReg load failed: {e}")
    return _logistic_model, _tfidf_vectorizer


# ── Heuristic fallback ────────────────────────────────────────────────────────
FAKE_KEYWORDS = [
    "breaking", "shocking", "you won't believe", "secret", "exposed",
    "hidden truth", "mainstream media", "cover-up", "they don't want you",
    "urgent", "unbelievable", "miracle", "cure", "hoax", "conspiracy",
    "wake up", "sheeple", "share before removed", "banned", "suppressed",
    "deep state", "globalist", "cabal", "new world order", "plandemic",
    "must see", "viral", "100%", "guaranteed", "proof", "bombshell",
]

CREDIBLE_INDICATORS = [
    "according to", "study shows", "research indicates", "published in",
    "peer-reviewed", "experts say", "official statement", "confirmed by",
    "data shows", "statistics", "journal", "university", "professor",
]


def heuristic_score(text: str) -> float:
    text_lower   = text.lower()
    fake_hits    = sum(1 for kw in FAKE_KEYWORDS if kw in text_lower)
    cred_hits    = sum(1 for kw in CREDIBLE_INDICATORS if kw in text_lower)
    word_count   = max(len(text.split()), 1)
    exclamations = text.count("!")
    caps_ratio   = sum(1 for c in text if c.isupper()) / max(len(text), 1)

    score  = 0.5
    score += min(fake_hits  * 0.05, 0.30)
    score -= min(cred_hits  * 0.04, 0.20)
    score += min(exclamations * 0.02, 0.10)
    score += min(caps_ratio * 0.3,  0.10)
    if word_count < 30:
        score += 0.05
    return float(np.clip(score, 0.0, 1.0))


# ── Shared label normalizer for all pipeline-based models ────────────────────
def _pipeline_to_fake_prob(result: dict) -> float:
    label = result["label"].upper()
    score = result["score"]
    if label in ("LABEL_1", "FAKE", "MISLEADING", "1"):
        return float(score)
    return float(1.0 - score)


# ── Individual model predictions ─────────────────────────────────────────────

def predict_bert(text: str) -> float:
    p = _get_bert()
    if p is None:
        return heuristic_score(text)
    try:
        return _pipeline_to_fake_prob(p(text[:512])[0])
    except Exception as e:
        logger.warning(f"BERT inference error: {e}")
        return heuristic_score(text)


def predict_roberta(text: str) -> float:
    p = _get_roberta()
    if p is None:
        return heuristic_score(text)
    try:
        return _pipeline_to_fake_prob(p(text[:512])[0])
    except Exception as e:
        logger.warning(f"RoBERTa inference error: {e}")
        return heuristic_score(text)


def predict_bert_multilingual(text: str) -> float:
    p = _get_bert_multilingual()
    if p is None:
        return heuristic_score(text)
    try:
        return _pipeline_to_fake_prob(p(text[:512])[0])
    except Exception as e:
        logger.warning(f"Multilingual BERT inference error: {e}")
        return heuristic_score(text)


def predict_lstm(text: str) -> float:
    model, tokenizer = _get_lstm()
    if model is None or tokenizer is None:
        return heuristic_score(text)
    try:
        # Preprocess to match train_lstm.py's preprocess_text()
        clean = re.sub(r"http\S+|www\S+", "", text.lower())
        clean = re.sub(r"[^a-z\s]", " ", clean)
        clean = re.sub(r"\s+", " ", clean).strip()

        oov = tokenizer.word_index.get("<OOV>", 1)
        seq = [tokenizer.word_index.get(w, oov) for w in clean.split()]
        seq = seq[:_MAX_LEN]
        padded = [0] * _MAX_LEN
        padded[:len(seq)] = seq

        x = torch.tensor([padded], dtype=torch.long)
        with torch.no_grad():
            prob = model(x).item()
        return float(prob)
    except Exception as e:
        logger.warning(f"LSTM inference error: {e}")
        return heuristic_score(text)


def predict_logistic(text: str) -> float:
    model, vectorizer = _get_logistic()
    if model is None or vectorizer is None:
        return heuristic_score(text)
    try:
        vec  = vectorizer.transform([text])
        prob = model.predict_proba(vec)[0]
        return float(prob[1])
    except Exception as e:
        logger.warning(f"LogReg inference error: {e}")
        return heuristic_score(text)


# ── Ensemble ──────────────────────────────────────────────────────────────────

def ensemble_predict(text: str) -> dict:
    """
    Run all five models and combine with weighted ensemble.
    If a model hasn't been trained yet its path won't exist,
    and it will automatically fall back to the heuristic score
    without crashing the other models.
    """
    bert_score         = predict_bert(text)
    roberta_score      = predict_roberta(text)
    multilingual_score = predict_bert_multilingual(text)
    lstm_score         = predict_lstm(text)
    logistic_score     = predict_logistic(text)

    ensemble_score = (
        BERT_WEIGHT              * bert_score         +
        ROBERTA_WEIGHT           * roberta_score      +
        BERT_MULTILINGUAL_WEIGHT * multilingual_score +
        LSTM_WEIGHT              * lstm_score         +
        LOGISTIC_WEIGHT          * logistic_score
    )

    label      = "FAKE" if ensemble_score >= 0.5 else "REAL"
    confidence = ensemble_score if label == "FAKE" else (1.0 - ensemble_score)

    return {
        "label":                   label,
        "confidence":              round(confidence * 100, 2),
        "ensemble_score":          round(ensemble_score, 4),
        "bert_score":              round(bert_score, 4),
        "roberta_score":           round(roberta_score, 4),
        "bert_multilingual_score": round(multilingual_score, 4),
        "lstm_score":              round(lstm_score, 4),
        "logistic_score":          round(logistic_score, 4),
        "weights": {
            "bert":              BERT_WEIGHT,
            "roberta":           ROBERTA_WEIGHT,
            "bert_multilingual": BERT_MULTILINGUAL_WEIGHT,
            "lstm":              LSTM_WEIGHT,
            "logistic":          LOGISTIC_WEIGHT,
        },
    }


def get_suspicious_keywords(text: str) -> list[str]:
    return [kw for kw in FAKE_KEYWORDS if kw in text.lower()]


def get_credibility_indicators(text: str) -> list[str]:
    return [kw for kw in CREDIBLE_INDICATORS if kw in text.lower()]