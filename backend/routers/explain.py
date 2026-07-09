"""
/explain-result endpoint
Generates human-readable explanations for predictions
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from database.connection import get_db
from models import AnalyzedArticle, Explanation
from services.ensemble_service import get_suspicious_keywords, get_credibility_indicators

router = APIRouter()

EMOTIONAL_WORDS = [
    "outrage", "shocking", "disgusting", "terrifying", "horrifying",
    "unbelievable", "amazing", "incredible", "devastating", "explosive",
    "alarming", "stunning", "jaw-dropping", "horrific", "insane",
]

MISLEADING_PATTERNS = [
    "they don't want you to know",
    "mainstream media won't tell you",
    "share before deleted",
    "banned from",
    "the truth about",
    "what they're hiding",
    "wake up",
    "open your eyes",
]


def _find_suspicious_sentences(text: str, keywords: list) -> list[str]:
    import re
    sentences = re.split(r"[.!?]+", text)
    suspicious = []
    for sent in sentences:
        sent_lower = sent.lower()
        if any(kw in sent_lower for kw in keywords):
            stripped = sent.strip()
            if stripped and len(stripped) > 10:
                suspicious.append(stripped[:200])
    return suspicious[:5]


def _generate_explanation(article: AnalyzedArticle) -> dict:
    text  = article.raw_text or ""
    lower = text.lower()

    suspicious_words = get_suspicious_keywords(text)
    credibility      = get_credibility_indicators(text)
    emotional_words  = [w for w in EMOTIONAL_WORDS if w in lower]
    misleading       = [p for p in MISLEADING_PATTERNS if p in lower]
    highlighted      = _find_suspicious_sentences(text, suspicious_words + emotional_words)

    # Build narrative explanation
    label      = article.label
    confidence = article.confidence
    parts      = []

    if label == "FAKE":
        parts.append(
            f"This article has been classified as **FAKE** with {confidence:.1f}% confidence "
            f"based on the ensemble model (BERT 60% + LSTM 25% + Logistic Regression 15%)."
        )
        if suspicious_words:
            parts.append(
                f"**Suspicious Keywords Detected:** The article contains {len(suspicious_words)} "
                f"suspicious keywords commonly found in fake news: {', '.join(suspicious_words[:8])}."
            )
        if emotional_words:
            parts.append(
                f"**Emotional Manipulation:** The article uses {len(emotional_words)} emotionally "
                f"charged words designed to provoke reactions rather than inform: {', '.join(emotional_words[:5])}."
            )
        if misleading:
            parts.append(
                f"**Misleading Language Patterns:** Detected {len(misleading)} common fake-news "
                f"phrases that signal unverified or sensationalist claims."
            )
        if not credibility:
            parts.append(
                "**Lack of Credibility Indicators:** The article does not cite studies, "
                "experts, or official sources — a hallmark of misinformation."
            )
        parts.append(
            f"**Model Scores:** BERT: {article.bert_score:.2%} | "
            f"RoBERTa: {(article.roberta_score or 0):.2%} | "
            f"mBERT: {(article.bert_multilingual_score or 0):.2%} | "
            f"LSTM: {article.lstm_score:.2%} | "
            f"Logistic Regression: {article.logistic_score:.2%}"
        )
    else:
        parts.append(
            f"This article has been classified as **REAL** with {confidence:.1f}% confidence."
        )
        if credibility:
            parts.append(
                f"**Credibility Indicators Found:** The article contains {len(credibility)} "
                f"credibility markers: {', '.join(credibility[:5])}."
            )
        if not suspicious_words:
            parts.append("**No Suspicious Keywords** commonly associated with fake news were detected.")
        if not emotional_words:
            parts.append("**Objective Language:** The article uses measured, factual language without excessive emotional manipulation.")
        parts.append(
            f"**Model Scores:** BERT: {article.bert_score:.2%} | "
            f"RoBERTa: {(article.roberta_score or 0):.2%} | "
            f"mBERT: {(article.bert_multilingual_score or 0):.2%} | "
            f"LSTM: {article.lstm_score:.2%} | "
            f"Logistic Regression: {article.logistic_score:.2%}"
        )

    return {
        "suspicious_words":     suspicious_words,
        "emotional_words":      emotional_words,
        "misleading_phrases":   misleading,
        "credibility_indicators": credibility,
        "highlighted_sentences": highlighted,
        "full_explanation":     "\n\n".join(parts),
    }


@router.get("/{article_id}")
async def explain_result(article_id: int, db: AsyncSession = Depends(get_db)):
    # Check for cached explanation
    stmt = select(Explanation).where(Explanation.article_id == article_id)
    result = await db.execute(stmt)
    cached = result.scalar_one_or_none()
    if cached:
        return {
            "article_id":          article_id,
            "suspicious_words":    cached.suspicious_words,
            "emotional_words":     cached.emotional_words,
            "misleading_phrases":  cached.misleading_phrases,
            "credibility_indicators": cached.credibility_indicators,
            "highlighted_sentences": cached.highlighted_sentences,
            "full_explanation":    cached.full_explanation,
        }

    # Generate new explanation
    stmt2   = select(AnalyzedArticle).where(AnalyzedArticle.id == article_id)
    result2 = await db.execute(stmt2)
    article = result2.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found.")

    explanation_data = _generate_explanation(article)

    exp = Explanation(
        article_id             = article_id,
        suspicious_words       = explanation_data["suspicious_words"],
        emotional_words        = explanation_data["emotional_words"],
        misleading_phrases     = explanation_data["misleading_phrases"],
        credibility_indicators = explanation_data["credibility_indicators"],
        highlighted_sentences  = explanation_data["highlighted_sentences"],
        full_explanation       = explanation_data["full_explanation"],
    )
    db.add(exp)
    await db.commit()

    return {"article_id": article_id, **explanation_data}
