"""
/analyze-text endpoint
Handles text, headline, and URL input for fake news detection
"""
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
import httpx
from loguru import logger

from database.connection import get_db
from services.ensemble_service import ensemble_predict, get_suspicious_keywords
from services.sentiment_service import analyze_sentiment
from models import AnalyzedArticle

limiter = Limiter(key_func=get_remote_address)
router  = APIRouter()


class TextAnalysisRequest(BaseModel):
    text:     Optional[str] = None
    url:      Optional[str] = None
    headline: Optional[str] = None


class TextAnalysisResponse(BaseModel):
    article_id:             int
    label:                  str
    confidence:             float
    ensemble_score:         float
    bert_score:             float
    roberta_score:          float
    bert_multilingual_score: float
    lstm_score:             float
    logistic_score:         float
    sentiment:              str
    sentiment_score:        float
    suspicious_keywords:    list[str]
    text_preview:           str
    source_title:           Optional[str] = None


async def fetch_url_text(url: str) -> tuple[str, str]:
    """Extract article text and title from URL using newspaper3k."""
    try:
        from newspaper import Article
        article = Article(url)
        article.download()
        article.parse()
        return article.text or "", article.title or ""
    except Exception as e:
        logger.warning(f"newspaper3k failed: {e}. Falling back to httpx.")
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, follow_redirects=True)
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "lxml")
                paragraphs = soup.find_all("p")
                text  = " ".join(p.get_text() for p in paragraphs)
                title = soup.find("title")
                return text[:5000], (title.get_text() if title else "")
        except Exception as e2:
            raise HTTPException(status_code=422, detail=f"Could not fetch URL: {e2}")


@router.post("/", response_model=TextAnalysisResponse)
@limiter.limit("30/minute")
async def analyze_text(
    request: Request,
    body:    TextAnalysisRequest,
    db:      AsyncSession = Depends(get_db),
):
    # ── Resolve input ─────────────────────────────────────────────────────────
    source_title = None
    source_url   = None

    if body.url:
        text, source_title = await fetch_url_text(body.url)
        source_url = body.url
        input_type = "url"
    elif body.text:
        text       = body.text.strip()
        input_type = "text"
    elif body.headline:
        text       = body.headline.strip()
        input_type = "text"
    else:
        raise HTTPException(status_code=422, detail="Provide text, url, or headline.")

    if len(text) < 5:
        raise HTTPException(status_code=422, detail="Text too short to analyze.")

    # ── AI Inference ──────────────────────────────────────────────────────────
    prediction = ensemble_predict(text)
    sentiment  = analyze_sentiment(text)
    keywords   = get_suspicious_keywords(text)

    # ── Persist to DB ─────────────────────────────────────────────────────────
    article = AnalyzedArticle(
        input_type              = input_type,
        raw_text                = text[:10000],
        source_url              = source_url,
        title                   = source_title,
        label                   = prediction["label"],
        confidence              = prediction["confidence"],
        bert_score              = prediction["bert_score"],
        roberta_score           = prediction["roberta_score"],
        bert_multilingual_score = prediction["bert_multilingual_score"],
        lstm_score              = prediction["lstm_score"],
        logistic_score          = prediction["logistic_score"],
        ensemble_score          = prediction["ensemble_score"],
        sentiment               = sentiment["label"],
        sentiment_score         = sentiment["score"],
        keywords                = keywords,
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)

    return TextAnalysisResponse(
        article_id              = article.id,
        label                   = prediction["label"],
        confidence              = prediction["confidence"],
        ensemble_score          = prediction["ensemble_score"],
        bert_score              = prediction["bert_score"],
        roberta_score           = prediction["roberta_score"],
        bert_multilingual_score = prediction["bert_multilingual_score"],
        lstm_score              = prediction["lstm_score"],
        logistic_score          = prediction["logistic_score"],
        sentiment               = sentiment["label"],
        sentiment_score         = sentiment["score"],
        suspicious_keywords     = keywords,
        text_preview            = text[:300],
        source_title            = source_title,
    )
