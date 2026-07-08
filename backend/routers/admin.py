"""Admin Router"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from database.connection import get_db
from models import AnalyzedArticle, Feedback, RetrainingData, CommunityPost

router = APIRouter()


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    total_articles = await db.scalar(select(func.count(AnalyzedArticle.id)))
    fake_count = await db.scalar(
        select(func.count(AnalyzedArticle.id)).where(AnalyzedArticle.label == "FAKE")
    )
    real_count = await db.scalar(
        select(func.count(AnalyzedArticle.id)).where(AnalyzedArticle.label == "REAL")
    )
    total_feedback = await db.scalar(select(func.count(Feedback.id)))
    retraining_pool = await db.scalar(
        select(func.count(RetrainingData.id)).where(RetrainingData.verified == False)
    )
    return {
        "total_articles":  total_articles or 0,
        "fake_count":      fake_count or 0,
        "real_count":      real_count or 0,
        "total_feedback":  total_feedback or 0,
        "retraining_pool": retraining_pool or 0,
        "fake_percentage": round((fake_count or 0) / max(total_articles or 1, 1) * 100, 1),
    }


@router.get("/recent-articles")
async def recent_articles(db: AsyncSession = Depends(get_db)):
    stmt = select(AnalyzedArticle).order_by(desc(AnalyzedArticle.created_at)).limit(20)
    result = await db.execute(stmt)
    articles = result.scalars().all()
    return [
        {
            "id":         a.id,
            "label":      a.label,
            "confidence": a.confidence,
            "input_type": a.input_type,
            "text_preview": (a.raw_text or "")[:100],
            "created_at": a.created_at,
        }
        for a in articles
    ]


@router.post("/approve-retraining/{item_id}")
async def approve_retraining(item_id: int, db: AsyncSession = Depends(get_db)):
    stmt   = select(RetrainingData).where(RetrainingData.id == item_id)
    result = await db.execute(stmt)
    item   = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    item.verified = True
    await db.commit()
    return {"message": "Approved for retraining."}
