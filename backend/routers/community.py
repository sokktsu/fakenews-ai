"""
Community Posts Router
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional

from database.connection import get_db
from models import CommunityPost, Comment

router = APIRouter()


class PostCreate(BaseModel):
    title:      str
    content:    str
    category:   str = "discussion"
    source_url: Optional[str] = None
    author_name: Optional[str] = "Anonymous"


class CommentCreate(BaseModel):
    content:     str
    author_name: Optional[str] = "Anonymous"


@router.get("/")
async def list_posts(
    page:     int = Query(1, ge=1),
    per_page: int = Query(10, le=50),
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CommunityPost).where(CommunityPost.is_approved == True)
    if category:
        stmt = stmt.where(CommunityPost.category == category)
    stmt = stmt.order_by(desc(CommunityPost.created_at))
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    posts  = result.scalars().all()
    return [
        {
            "id":         p.id,
            "title":      p.title,
            "content":    p.content[:300],
            "category":   p.category,
            "source_url": p.source_url,
            "likes":      p.likes,
            "created_at": p.created_at,
        }
        for p in posts
    ]


@router.post("/")
async def create_post(body: PostCreate, db: AsyncSession = Depends(get_db)):
    post = CommunityPost(
        title      = body.title[:300],
        content    = body.content[:5000],
        category   = body.category,
        source_url = body.source_url,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return {"id": post.id, "message": "Post created successfully."}


@router.post("/{post_id}/like")
async def like_post(post_id: int, db: AsyncSession = Depends(get_db)):
    stmt   = select(CommunityPost).where(CommunityPost.id == post_id)
    result = await db.execute(stmt)
    post   = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    post.likes += 1
    await db.commit()
    return {"likes": post.likes}


@router.get("/{post_id}/comments")
async def get_comments(post_id: int, db: AsyncSession = Depends(get_db)):
    stmt   = select(Comment).where(Comment.post_id == post_id, Comment.is_approved == True)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/{post_id}/comments")
async def add_comment(post_id: int, body: CommentCreate, db: AsyncSession = Depends(get_db)):
    comment = Comment(
        post_id     = post_id,
        author_name = body.author_name or "Anonymous",
        content     = body.content[:2000],
    )
    db.add(comment)
    await db.commit()
    return {"message": "Comment added."}
