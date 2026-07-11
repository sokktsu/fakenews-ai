"""
FAKE NEWS AI — FastAPI Backend
Main application entry point
"""
print(">>> [boot] main.py loaded, importing dependencies...", flush=True)
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

# ── Download trained models from Hugging Face Hub (BACKGROUND, non-blocking) ────
# The Space ships without model weights (too big for git). We pull them in a
# daemon thread so the API can bind port 7860 immediately instead of blocking
# startup for minutes (which made HF think the app never came up).
import shutil, threading
from huggingface_hub import snapshot_download

load_dotenv()  # load .env early so the download guard below sees *_MODEL_PATH


def _boot(msg):
    print(f"[boot] {msg}", flush=True)


def _download_models():
    _boot("Ensuring models are present...")
    try:
        for repo, env_var, dest in [
            ("sokktsu/fakenews-bert",              "BERT_MODEL_PATH",              "ai_models/bert/saved_model"),
            ("sokktsu/fakenews-roberta",           "ROBERTA_MODEL_PATH",           "ai_models/roberta/saved_model"),
            ("sokktsu/fakenews-bert-multilingual", "BERT_MULTILINGUAL_MODEL_PATH", "ai_models/bert_multilingual/saved_model"),
        ]:
            # Skip if the model already exists at the configured path (local dev
            # with locally-trained models) or at the default download destination.
            configured = os.getenv(env_var, dest)
            if os.path.exists(os.path.join(configured, "config.json")) or \
               os.path.exists(os.path.join(dest, "config.json")):
                continue
            _boot(f"Downloading {repo}")
            snapshot_download(repo, local_dir=dest)
            _boot(f"Done {repo}")

        # LSTM + LogReg share one repo (lstm/ and logistic_regression/ subfolders);
        # copy each subfolder's files into the saved_model/ path the loader expects.
        lstm_configured = os.getenv("LSTM_MODEL_PATH", "ai_models/lstm/saved_model")
        if not (os.path.exists(os.path.join(lstm_configured, "model.pt")) or
                os.path.exists("ai_models/lstm/saved_model/model.pt")):
            _boot("Downloading sokktsu/fakenews-small-models")
            small = snapshot_download("sokktsu/fakenews-small-models")
            for sub, dest in [("lstm", "ai_models/lstm/saved_model"),
                              ("logistic_regression", "ai_models/logistic_regression/saved_model")]:
                os.makedirs(dest, exist_ok=True)
                for f in os.listdir(os.path.join(small, sub)):
                    shutil.copy2(os.path.join(small, sub, f), os.path.join(dest, f))
        _boot("Models ready.")
    except Exception as e:
        _boot(f"MODEL DOWNLOAD ERROR: {e!r}")


threading.Thread(target=_download_models, daemon=True).start()
_boot("Background model download started; continuing app startup.")

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

_boot("All imports done (routers, DB, models). Building app...")
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
    # Ensure tables exist, but NEVER let a slow/unreachable DB block startup.
    # (Tables are also created by database/schema.sql in Supabase, so this is
    # a best-effort convenience.) A hang here would keep the whole Space in
    # APP_STARTING forever, so we time-box it and continue regardless.
    import asyncio

    async def _init_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    try:
        await asyncio.wait_for(_init_db(), timeout=15)
        logger.info("Database tables ready.")
    except Exception as e:
        logger.error(f"DB init skipped, app continues anyway: {e!r}")


# GET + HEAD so uptime monitors (which ping with HEAD) get 200, not 405.
@app.api_route("/", methods=["GET", "HEAD"], tags=["Health"])
async def root():
    return {
        "status": "ok",
        "message": "Fake News AI API is running",
        "docs": "/api/docs",
    }


@app.api_route("/health", methods=["GET", "HEAD"], tags=["Health"])
async def health():
    return {"status": "healthy", "version": "1.0.0"}


@app.api_route("/health/db", methods=["GET", "HEAD"], tags=["Health"])
async def health_db():
    """Runs SELECT 1 so an uptime monitor pinging this keeps Supabase awake
    (free tier auto-pauses after ~1 week with no DB activity)."""
    from sqlalchemy import text
    from fastapi import HTTPException
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "db ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"db unreachable: {e!r}"[:200])
