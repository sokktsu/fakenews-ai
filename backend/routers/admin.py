"""Admin Router"""
import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from database.connection import get_db
from models import AnalyzedArticle, Feedback, RetrainingData, CommunityPost, User

router = APIRouter()

# ── Admin authentication ──────────────────────────────────────────────────────
# Every route below requires a Bearer token belonging to a user whose
# users.is_admin flag is True. Non-admins get 403; missing/bad token gets 401.
_bearer    = HTTPBearer(auto_error=True)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")


async def require_admin(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token.")
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user or not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required.")
    return user


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
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
async def recent_articles(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
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
async def approve_retraining(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    stmt   = select(RetrainingData).where(RetrainingData.id == item_id)
    result = await db.execute(stmt)
    item   = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    item.verified = True
    await db.commit()
    return {"message": "Approved for retraining."}
