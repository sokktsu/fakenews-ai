"""
Feedback Router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from database.connection import get_db
from models import Feedback, RetrainingData, AnalyzedArticle

router = APIRouter()


class FeedbackRequest(BaseModel):
    article_id:    int
    was_accurate:  bool
    correct_label: Optional[str] = None
    comment:       Optional[str] = None


@router.post("/")
async def submit_feedback(body: FeedbackRequest, db: AsyncSession = Depends(get_db)):
    # Verify article exists
    stmt = select(AnalyzedArticle).where(AnalyzedArticle.id == body.article_id)
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found.")

    fb = Feedback(
        article_id    = body.article_id,
        was_accurate  = body.was_accurate,
        correct_label = body.correct_label,
        comment       = body.comment,
    )
    db.add(fb)

    # If prediction was wrong and a correct label is given, add to retraining pool
    if not body.was_accurate and body.correct_label and article.raw_text:
        rt = RetrainingData(
            text    = article.raw_text[:5000],
            label   = body.correct_label,
            source  = "feedback",
            verified = False,
        )
        db.add(rt)

    await db.commit()
    return {"message": "Thank you for your feedback! It helps improve the AI."}


@router.get("/stats")
async def feedback_stats(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import func
    total = await db.scalar(select(func.count(Feedback.id)))
    accurate = await db.scalar(select(func.count(Feedback.id)).where(Feedback.was_accurate == True))
    return {
        "total_feedback": total or 0,
        "accurate_predictions": accurate or 0,
        "accuracy_rate": round((accurate or 0) / max(total or 1, 1) * 100, 1),
    }
