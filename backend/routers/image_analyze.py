"""
/analyze-image endpoint
OCR text extraction + fake news detection
"""
from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address
import os, uuid
from loguru import logger

from database.connection import get_db
from services.ensemble_service import ensemble_predict, get_suspicious_keywords
from services.sentiment_service import analyze_sentiment
from services.ocr_service import extract_text_from_image
from models import AnalyzedArticle, UploadedImage

limiter = Limiter(key_func=get_remote_address)
router  = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp"}
MAX_SIZE_MB   = int(os.getenv("MAX_UPLOAD_SIZE_MB", 10))


@router.post("/")
@limiter.limit("10/minute")
async def analyze_image(
    request: Request,
    file:    UploadFile = File(...),
    db:      AsyncSession = Depends(get_db),
):
    # ── Validate file ─────────────────────────────────────────────────────────
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=422, detail="Only image files are supported.")

    content = await file.read()
    if len(content) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large. Max {MAX_SIZE_MB}MB.")

    # ── Save file ─────────────────────────────────────────────────────────────
    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    os.makedirs(upload_dir, exist_ok=True)
    ext       = os.path.splitext(file.filename or "image.jpg")[1] or ".jpg"
    unique_fn = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(upload_dir, unique_fn)

    with open(file_path, "wb") as f:
        f.write(content)

    # ── OCR ───────────────────────────────────────────────────────────────────
    extracted_text = extract_text_from_image(file_path)
    if not extracted_text or len(extracted_text.strip()) < 5:
        return {
            "label":          "INCONCLUSIVE",
            "confidence":     0.0,
            "extracted_text": "",
            "message":        "No readable text found in image.",
        }

    # ── AI Inference ──────────────────────────────────────────────────────────
    prediction = ensemble_predict(extracted_text)
    sentiment  = analyze_sentiment(extracted_text)
    keywords   = get_suspicious_keywords(extracted_text)

    # ── Persist ───────────────────────────────────────────────────────────────
    article = AnalyzedArticle(
        input_type              = "image",
        raw_text                = extracted_text[:10000],
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

    image_record = UploadedImage(
        filename       = file.filename,
        file_path      = file_path,
        extracted_text = extracted_text,
        article_id     = article.id,
    )
    db.add(image_record)
    await db.commit()

    return {
        "article_id":            article.id,
        "label":                 prediction["label"],
        "confidence":            prediction["confidence"],
        "ensemble_score":        prediction["ensemble_score"],
        "bert_score":            prediction["bert_score"],
        "roberta_score":         prediction["roberta_score"],
        "bert_multilingual_score": prediction["bert_multilingual_score"],
        "lstm_score":            prediction["lstm_score"],
        "logistic_score":        prediction["logistic_score"],
        "sentiment":             sentiment["label"],
        "extracted_text":        extracted_text[:500],
        "suspicious_keywords":   keywords,
        "image_url":             f"/uploads/{unique_fn}",
    }
