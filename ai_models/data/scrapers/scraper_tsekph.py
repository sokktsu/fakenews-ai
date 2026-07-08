"""
scraper_tsekph.py — Tsek.ph Fact-Check Page Scraper
Scrapes: https://www.tsek.ph/category/fact-checks/
Method:  Selenium — navigates numbered pagination (up to 300 pages).
         After collecting listing-page URLs, fetches each article
         to extract verdict from articleSection JSON-LD.

Imported and called by scraper_runner.py.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time
import requests
from loguru import logger
from shared_utils import (
    extract_articles_from_html, enrich_article_url,
    DEFAULT_HEADERS, get_hash, clean
)

BASE_URL    = "https://www.tsek.ph/category/fact-checks/"
SOURCE      = "Tsek.ph"
MAX_PARAM   = 300
PARAM_LABEL = "pages"


def scrape(driver, max_pages: int = MAX_PARAM, existing_urls: set = None) -> list:
    """
    Scrape Tsek.ph listing pages, then enrich each article URL
    with proper verdict from articleSection JSON-LD.
    """
    listing_articles  = []
    seen_hashes       = set()
    seen_urls         = set()
    page_num          = 1
    consecutive_empty = 0

    # ── Phase 1: collect all article URLs from listing pages ───────────────────
    for page_num in range(1, max_pages + 1):
        url = BASE_URL if page_num == 1 else f"{BASE_URL}page/{page_num}/"

        driver.get(url)
        time.sleep(2)

        if "404" in driver.title or "Page not found" in driver.page_source:
            logger.info(f"  Page {page_num}: Not found. Stopping.")
            break

        new_pairs = extract_articles_from_html(driver.page_source, SOURCE, url)
        new = [p for p in new_pairs if p["hash"] not in seen_hashes]
        seen_hashes.update(p["hash"] for p in new)
        if existing_urls:
            new = [p for p in new if p.get("url", "") not in existing_urls]
        listing_articles.extend(new)

        # Track unique article URLs
        for p in new:
            article_url = p.get("url", "")
            if article_url and article_url != url and article_url.startswith("http"):
                seen_urls.add(article_url)

        if new:
            consecutive_empty = 0
            if page_num % 20 == 0 or page_num <= 3:
                logger.info(f"  Page {page_num}/{max_pages}: +{len(new)} new (total: {len(listing_articles)})")
        else:
            consecutive_empty += 1
            logger.info(f"  Page {page_num}: 0 new pairs ({consecutive_empty} consecutive empty)")
            if consecutive_empty >= 3:
                logger.info("  3 consecutive empty pages. Stopping.")
                break

        time.sleep(1)

    logger.info(f"  Tsek.ph listing: {len(listing_articles)} pairs, {len(seen_urls)} unique article URLs")

    # ── Phase 2: enrich each article URL ──────────────────────────────────────
    article_urls = sorted(seen_urls)
    if not article_urls:
        return listing_articles

    logger.info(f"  Enriching {len(article_urls)} Tsek.ph articles...")
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    enriched_pairs  = []
    enriched_hashes = set()
    enriched_url_set = set()

    for i, url in enumerate(article_urls, 1):
        if i % 100 == 0:
            logger.info(f"    Enriched {i}/{len(article_urls)}")
        try:
            pairs = enrich_article_url(url, session)
            for p in pairs:
                if p["hash"] not in enriched_hashes:
                    enriched_hashes.add(p["hash"])
                    enriched_pairs.append(p)
                    enriched_url_set.add(url)
        except Exception as e:
            logger.warning(f"    Enrich failed {url}: {e}")
        time.sleep(1)

    logger.info(f"  Tsek.ph enriched: {len(enriched_pairs)} article-level pairs from {len(enriched_url_set)} URLs")

    # Fallback: listing-page pairs for URLs that couldn't be enriched
    enriched_urls_done = {p["url"] for p in enriched_pairs}
    fallback = [p for p in listing_articles if p.get("url") not in enriched_urls_done]
    logger.info(f"  Tsek.ph fallback (listing-page only): {len(fallback)} pairs")

    all_pairs = enriched_pairs + fallback
    logger.info(f"  Tsek.ph total: {len(all_pairs)} pairs from {page_num} pages")
    return all_pairs
