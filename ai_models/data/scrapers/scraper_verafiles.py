"""
scraper_verafiles.py — Vera Files Archive Scraper
Scrapes: https://verafiles.org/issues-archive/2035  (English)
         https://verafiles.org/issues-archive/2617  (Filipino)
Method:  Plain requests — numbered pagination up to 500 pages.
         After collecting listing-page URLs, fetches each article
         to extract proper claim/verdict via JSON-LD ClaimReview
         or WHAT WAS CLAIMED / OUR VERDICT HTML blocks.
         Non-fact-check articles (no ClaimReview) are kept as REAL (label=0).

Imported and called by scraper_runner.py.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import re, time
import requests
from bs4 import BeautifulSoup
from loguru import logger
from shared_utils import (
    clean, extract_claim_debunk, enrich_article_url,
    DEFAULT_HEADERS, get_hash
)
from datetime import datetime

ARCHIVE_ENGLISH  = "https://verafiles.org/issues-archive/2035"
ARCHIVE_FILIPINO = "https://verafiles.org/issues-archive/2617"
SOURCE_EN        = "Vera Files"
SOURCE_FIL       = "Vera Files Filipino"
MAX_PARAM        = 500
PARAM_LABEL      = "pages"

SESSION = requests.Session()
SESSION.headers.update({**DEFAULT_HEADERS, "Cache-Control": "no-cache"})


def _fetch(url: str, retries: int = 3) -> BeautifulSoup | None:
    for attempt in range(retries + 1):
        try:
            resp = SESSION.get(url, timeout=20)
            if resp.status_code == 429:
                wait = 180 * (attempt + 1)
                logger.info(f"  Rate limited (attempt {attempt+1}). Waiting {wait}s...")
                time.sleep(wait)
                continue
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except requests.exceptions.Timeout:
            logger.warning(f"  Timeout attempt {attempt+1}")
            time.sleep(3)
        except Exception as e:
            logger.warning(f"  Error: {e}")
            time.sleep(3)
    return None


def _extract_cards(soup: BeautifulSoup, source: str) -> list:
    """
    Extract article cards from Vera Files listing page.
    Returns list of dicts with text, label, pair_type, source, url, hash, collected_at.
    Only stores URL and title at this stage — article-level enrichment happens later.
    """
    articles = []
    headings = soup.find_all("h2", class_=re.compile(r"article-title"))
    if not headings:
        headings = soup.find_all("h2")

    for h in headings:
        title = clean(h.get_text())
        if len(title) < 10:
            continue

        # Get summary
        summary   = ""
        container = h.parent
        for _ in range(4):
            if container is None:
                break
            p = container.find("p", class_=re.compile(r"line-clamp"))
            if p:
                summary = clean(p.get_text())
                break
            container = container.parent

        if not summary and h.parent:
            p = h.parent.find("p")
            if p:
                summary = clean(p.get_text())

        if not summary:
            summary = title

        # Get article URL
        url = ""
        link_container = h.parent
        for _ in range(4):
            if link_container is None:
                break
            a = link_container.find("a", href=True)
            if a and a["href"] and a["href"] != "#":
                url = a["href"]
                break
            link_container = link_container.parent

        if url.startswith("/"):
            url = "https://verafiles.org" + url

        pairs = extract_claim_debunk(title, summary, source, url)
        articles.extend(pairs)

    return articles


def _scrape_section_urls(base_url: str, source: str, max_pages: int,
                         existing_urls: set = None) -> tuple:
    """
    Scrape listing pages and return (listing_articles, unique_article_urls).
    """
    all_articles      = []
    seen_hashes       = set()
    seen_urls         = set()
    consecutive_empty = 0
    page_num          = 1

    for page_num in range(1, max_pages + 1):
        url  = base_url if page_num == 1 else f"{base_url}/page/{page_num}"
        soup = _fetch(url)

        if soup is None:
            logger.info(f"  [{source}] Page {page_num}: 404/error. Stopping.")
            break

        if any(x in soup.get_text().lower() for x in ["nothing found", "no posts"]):
            logger.info(f"  [{source}] Page {page_num}: Nothing found. Stopping.")
            break

        articles = _extract_cards(soup, source)
        new = [a for a in articles if a["hash"] not in seen_hashes]
        seen_hashes.update(a["hash"] for a in new)
        if existing_urls:
            new = [a for a in new if a.get("url", "") not in existing_urls]
        all_articles.extend(new)

        # Collect unique article URLs
        for a in new:
            article_url = a.get("url", "")
            if article_url and article_url.startswith("http") and "verafiles.org/articles" in article_url:
                seen_urls.add(article_url)

        if new:
            consecutive_empty = 0
            if page_num % 20 == 0 or page_num <= 3:
                logger.info(f"  [{source}] Page {page_num}/{max_pages}: +{len(new)} new (total: {len(all_articles)})")
        else:
            consecutive_empty += 1
            logger.info(f"  [{source}] Page {page_num}: 0 new ({consecutive_empty} consecutive empty)")
            if consecutive_empty >= 3:
                logger.info("  3 consecutive empty pages. Stopping.")
                break

        time.sleep(8)

    logger.info(f"  [{source}] Listing: {len(all_articles)} pairs, {len(seen_urls)} article URLs")
    return all_articles, sorted(seen_urls)


def _enrich_urls(article_urls: list, source: str) -> tuple:
    """
    Fetch each article URL and extract proper claim/verdict.
    Returns (enriched_pairs, enriched_url_set).

    Adaptive throttling: the delay between articles starts at BASE_DELAY,
    doubles every time the server answers 429 (rate limited), and slowly
    recovers after a streak of clean fetches. This avoids the old failure
    mode where the loop waited out a 429 penalty and then immediately
    resumed at full speed — earning the next penalty right away.
    """
    import shared_utils

    BASE_DELAY     = 8
    MAX_DELAY      = 120
    RECOVER_AFTER  = 25   # clean fetches before speeding back up

    enriched_pairs   = []
    enriched_hashes  = set()
    enriched_url_set = set()

    logger.info(f"  [{source}] Enriching {len(article_urls)} articles...")
    enrich_session = requests.Session()
    enrich_session.headers.update(DEFAULT_HEADERS)

    delay        = BASE_DELAY
    clean_streak = 0

    for i, url in enumerate(article_urls, 1):
        if i % 50 == 0:
            logger.info(f"    [{source}] Enriched {i}/{len(article_urls)} (current pace: {delay}s/article)")

        limits_before = shared_utils.RATE_LIMIT_COUNT
        try:
            pairs = enrich_article_url(url, enrich_session, source=source)
            for p in pairs:
                if p["hash"] not in enriched_hashes:
                    enriched_hashes.add(p["hash"])
                    enriched_pairs.append(p)
                    enriched_url_set.add(url)
        except Exception as e:
            logger.warning(f"    Enrich failed {url}: {e}")

        if shared_utils.RATE_LIMIT_COUNT > limits_before:
            delay        = min(delay * 2, MAX_DELAY)
            clean_streak = 0
            logger.info(f"    [{source}] Rate limited — backing off to {delay}s between articles.")
        else:
            clean_streak += 1
            if clean_streak >= RECOVER_AFTER and delay > BASE_DELAY:
                delay        = max(BASE_DELAY, delay // 2)
                clean_streak = 0
                logger.info(f"    [{source}] Stable again — recovering to {delay}s between articles.")

        time.sleep(delay)

    logger.info(f"  [{source}] Enriched: {len(enriched_pairs)} pairs from {len(enriched_url_set)} URLs")
    if not enriched_pairs and len(article_urls) >= 10:
        logger.error(
            f"  [{source}] BUG SUSPECTED: enrichment produced 0 pairs from {len(article_urls)} URLs. "
            "The site's markup has probably changed (check the extraction helpers in shared_utils.py "
            "against a live article). Falling back to listing-page data."
        )
    return enriched_pairs, enriched_url_set


# Which archive(s) a scrape() call covers. The runner passes section=
# "english" or "filipino" so each archive can be run/reset independently.
ARCHIVES = {
    "english":  [(ARCHIVE_ENGLISH, SOURCE_EN)],
    "filipino": [(ARCHIVE_FILIPINO, SOURCE_FIL)],
    "all":      [(ARCHIVE_ENGLISH, SOURCE_EN), (ARCHIVE_FILIPINO, SOURCE_FIL)],
}


def scrape(driver=None, max_pages: int = MAX_PARAM, existing_urls: set = None,
           section: str = "all") -> list:
    """
    Scrape the Vera Files archive(s) selected by `section`
    ("english", "filipino", or "all").
    Phase 1: collect article URLs from listing pages.
    Phase 2: fetch each article and extract proper claim/verdict.
    Falls back to listing-page data for articles that can't be enriched.

    driver param is accepted but not used — kept for consistent interface.
    existing_urls: set of URLs already in datasets_scraped_ph_factcheck.csv.
    """
    all_pairs   = []
    seen_hashes = set()

    for base_url, source in ARCHIVES[section]:
        logger.info(f"  Scraping {source} archive (up to {max_pages} pages)...")

        # Phase 1: listing pages
        listing_articles, article_urls = _scrape_section_urls(
            base_url, source, max_pages, existing_urls
        )

        # Phase 2: article-level enrichment
        if article_urls:
            enriched_pairs, enriched_url_set = _enrich_urls(article_urls, source)
        else:
            enriched_pairs, enriched_url_set = [], set()

        # Combine: enriched pairs + fallback for unenriched URLs
        enriched_urls_done = {p["url"] for p in enriched_pairs}
        fallback = [p for p in listing_articles if p.get("url") not in enriched_urls_done]

        combined = enriched_pairs + fallback
        new = [p for p in combined if p["hash"] not in seen_hashes]
        seen_hashes.update(p["hash"] for p in new)
        all_pairs.extend(new)

        logger.info(f"  [{source}] Total: {len(new)} pairs (enriched: {len(enriched_pairs)}, fallback: {len(fallback)})")

    return all_pairs
