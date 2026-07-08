"""
runner_rss.py — Daily RSS Feed Runner
Collects articles from all Philippine news RSS feeds and fact-check RSS feeds.
Run this daily via Task Scheduler.

Usage:
    python ai_models/data/runner_rss.py

Output: ai_models/data/datasets_rss_ph_real_news.csv (appends new articles — this file ONLY)
        Merging into combined_dataset.csv happens exclusively in
        prepare_dataset.py — run it after this script.
"""
import os, time, hashlib
import pandas as pd
import requests
import feedparser
from datetime import datetime
from loguru import logger

from shared_utils import (
    clean, get_hash, extract_claim_debunk,
    process_rss_entries,
)

# ── Import feed lists from per-site files ─────────────────────────────────────
from rss_feeds.rss_gma            import FEEDS as GMA_FEEDS
from rss_feeds.rss_inquirer       import FEEDS as INQUIRER_FEEDS
from rss_feeds.rss_philstar       import FEEDS as PHILSTAR_FEEDS
from rss_feeds.rss_manilatimes    import FEEDS as MANILATIMES_FEEDS
from rss_feeds.rss_manila_bulletin import FEEDS as MB_FEEDS
from rss_feeds.rss_others         import FEEDS as OTHER_FEEDS

OUTPUT_CSV = "ai_models/data/datasets_rss_ph_real_news.csv"

# INCREMENTAL = False → process all RSS entries (first run)
# INCREMENTAL = True  → skip articles already in datasets_rss_ph_real_news.csv (daily runs)
INCREMENTAL = False

RSS_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control":   "no-cache",
}


def fetch_rss(url: str, retries: int = 2) -> list:
    """Fetch RSS feed entries with retry and rate-limit handling."""
    timeout = 45 if "verafiles" in url else 20
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, headers=RSS_HEADERS, timeout=timeout,
                                verify="cnnphilippines" not in url)
            if resp.status_code == 429:
                wait = 15 * (attempt + 1)
                logger.info(f"  Rate limited. Waiting {wait}s...")
                time.sleep(wait)
                continue
            if resp.status_code in (403, 404):
                logger.warning(f"  HTTP {resp.status_code}: {url}")
                return []
            resp.raise_for_status()
            return feedparser.parse(resp.content).entries
        except requests.exceptions.SSLError:
            try:
                resp = requests.get(url, headers=RSS_HEADERS, timeout=timeout, verify=False)
                return feedparser.parse(resp.content).entries
            except Exception as e:
                logger.warning(f"  SSL fallback failed: {e}")
                return []
        except Exception as e:
            logger.warning(f"  Fetch failed: {e}")
            return []
    return []


def entries_to_real_articles(entries: list, source: str) -> list[dict]:
    """Convert RSS entries from real news feeds to labeled articles (label=0)."""
    articles = []
    for entry in entries:
        title   = clean(entry.get("title",   "")).strip()
        summary = clean(entry.get("summary", "")).strip()
        content_list = entry.get("content", [])
        content = clean(content_list[0].get("value", "") if content_list else "").strip()

        body      = content if len(content) > len(summary) else summary
        full_text = f"{title}. {body}".strip() if body and title not in body else (title or body)

        if len(full_text) < 20:
            continue

        articles.append({
            "text":         full_text,
            "label":        0,
            "pair_type":    "real_news",
            "source":       source,
            "verdict":      "real_news_source",
            "url":          entry.get("link", ""),
            "hash":         get_hash(full_text),
            "collected_at": datetime.now().isoformat(),
        })
    return articles


def save_to_csv(articles: list[dict]) -> int:
    """Append new articles to datasets_rss_ph_real_news.csv, skipping duplicates."""
    if not articles:
        return 0

    new_df = pd.DataFrame(articles)
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

    if os.path.exists(OUTPUT_CSV):
        existing_df = pd.read_csv(OUTPUT_CSV)
        for col in ["pair_type", "verdict"]:
            if col not in existing_df.columns:
                existing_df[col] = "legacy"
        existing_hashes = set(existing_df["hash"].tolist())
        new_df = new_df[~new_df["hash"].isin(existing_hashes)]
        combined = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined = new_df

    combined.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    return len(new_df)


def print_summary():
    if not os.path.exists(OUTPUT_CSV):
        return
    df = pd.read_csv(OUTPUT_CSV)
    logger.info("\n--- LABEL SUMMARY BY SOURCE ---")
    logger.info(f"  {'Source':<35} {'REAL':>6} {'FAKE':>6}")
    logger.info("  " + "-" * 52)
    for source in sorted(df["source"].unique()):
        sub  = df[df["source"] == source]
        real = (sub["label"] == 0).sum()
        fake = (sub["label"] == 1).sum()
        logger.info(f"  {source:<35} {real:>6} {fake:>6}")
    logger.info("  " + "-" * 52)
    logger.info(f"  {'TOTAL':<35} {(df['label']==0).sum():>6} {(df['label']==1).sum():>6}")


def run():
    logger.info("=" * 60)
    logger.info("RSS RUNNER — Daily Philippine News Collector")
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Mode:    {'INCREMENTAL (new articles only)' if INCREMENTAL else 'FULL'}")
    logger.info("=" * 60)

    all_articles = []
    seen_hashes  = set()

    # ── Pre-load existing hashes for incremental mode ─────────────────────────
    if INCREMENTAL and os.path.exists(OUTPUT_CSV):
        try:
            ex_df = pd.read_csv(OUTPUT_CSV)
            if "hash" in ex_df.columns:
                existing_hashes = set(ex_df["hash"].dropna().tolist())
                seen_hashes.update(existing_hashes)
                logger.info(f"Incremental mode: {len(existing_hashes)} existing articles pre-loaded — already-collected articles will be skipped.")
        except Exception as e:
            logger.warning(f"Could not load existing hashes: {e}")

    # ── Real news feeds ───────────────────────────────────────────────────────
    all_real_feeds = (
        GMA_FEEDS + INQUIRER_FEEDS + PHILSTAR_FEEDS +
        MANILATIMES_FEEDS + MB_FEEDS + OTHER_FEEDS
    )

    logger.info(f"\n--- REAL NEWS FEEDS ({len(all_real_feeds)} feeds) ---")
    for url, source in all_real_feeds:
        entries  = fetch_rss(url)
        articles = entries_to_real_articles(entries, source)
        new      = [a for a in articles if a["hash"] not in seen_hashes]
        seen_hashes.update(a["hash"] for a in new)
        all_articles.extend(new)
        if new:
            logger.info(f"  {source}: {len(new)} new articles")
        time.sleep(0.3)

    if not all_articles:
        logger.error("No articles collected. Check internet connection.")
        return

    new_count = save_to_csv(all_articles)
    print_summary()

    logger.info("\n" + "=" * 60)
    logger.info("RSS RUNNER COMPLETE")
    logger.info(f"Total fetched:    {len(all_articles)}")
    logger.info(f"New unique saved: {new_count}")
    logger.info("Next step: python ai_models/data/prepare_dataset.py to merge into combined_dataset.csv")
    logger.info("=" * 60)


if __name__ == "__main__":
    run()
