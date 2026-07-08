"""
FAKE NEWS AI — FastAPI Backend
Main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
from dotenv import load_dotenv
from loguru import logger

from routers import (
    analyze,
    image_analyze,
    explain,
    feedback,
    community,
    resources,
    auth,
    admin,
    news_feed,
)
from database.connection import engine, Base
import models  # ensure all models are imported for table creation

load_dotenv()

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Fake News AI API",
    description="NLP + Deep Learning ensemble for fake news detection",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────────────────────
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ── Static files (uploads) ────────────────────────────────────────────────────
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,          prefix="/auth",            tags=["Auth"])
app.include_router(analyze.router,       prefix="/analyze-text",    tags=["Text Analysis"])
app.include_router(image_analyze.router, prefix="/analyze-image",   tags=["Image Analysis"])
app.include_router(explain.router,       prefix="/explain-result",  tags=["Explainability"])
app.include_router(feedback.router,      prefix="/feedback",        tags=["Feedback"])
app.include_router(community.router,     prefix="/community-posts", tags=["Community"])
app.include_router(resources.router,     prefix="/resources",       tags=["Resources"])
app.include_router(admin.router,         prefix="/admin",           tags=["Admin"])
app.include_router(news_feed.router,     prefix="/news-feed",       tags=["News Feed"])

# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Fake News AI backend...")
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready.")


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "message": "Fake News AI API is running",
        "docs": "/api/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "version": "1.0.0"}
