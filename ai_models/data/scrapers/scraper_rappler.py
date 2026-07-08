"""
scraper_rappler.py — Rappler Fact-Check Page Scraper
Scrapes: https://www.rappler.com/newsbreak/fact-check/
Method:  Selenium — clicks "Load More" button repeatedly.
         After collecting listing-page URLs, fetches each article
         to extract proper claim/verdict via JSON-LD ClaimReview.

Imported and called by scraper_runner.py.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time
import requests
from loguru import logger
from shared_utils import extract_articles_from_html, enrich_article_url, DEFAULT_HEADERS

URL         = "https://www.rappler.com/newsbreak/fact-check/"
SOURCE      = "Rappler FactCheck"
MAX_PARAM   = 999
PARAM_LABEL = "load-more clicks"

LOAD_MORE_SELECTORS = [
    "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'load more')]",
    "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'load more')]",
    "//button[contains(@class, 'load')]",
    "//div[contains(@class, 'load-more')]//button",
    "//button[contains(@class, 'more')]",
    "//*[contains(@class, 'pagination')]//a[contains(text(), 'Next')]",
]


def scrape(driver, max_clicks: int = MAX_PARAM, existing_urls: set = None) -> list:
    """
    Scrape Rappler fact-check listing page, then enrich each article URL
    with proper claim/verdict from JSON-LD ClaimReview.
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        TimeoutException, NoSuchElementException, ElementClickInterceptedException
    )

    logger.info(f"  Loading: {URL}")
    driver.get(URL)
    time.sleep(3)

    # ── Phase 1: collect all article URLs from listing page ────────────────────
    listing_articles  = []
    seen_hashes       = set()
    seen_urls         = set()
    clicks            = 0
    consecutive_empty = 0

    while clicks <= max_clicks:
        new_pairs = extract_articles_from_html(driver.page_source, SOURCE, URL)
        new = [p for p in new_pairs if p["hash"] not in seen_hashes]
        seen_hashes.update(p["hash"] for p in new)
        if existing_urls:
            new = [p for p in new if p.get("url", "") not in existing_urls]
        listing_articles.extend(new)

        # Track unique article URLs for enrichment
        for p in new:
            url = p.get("url", "")
            if url and url != URL and url.startswith("http"):
                seen_urls.add(url)

        if clicks == 0:
            logger.info(f"  Initial load: {len(new)} pairs")
        else:
            logger.info(f"  After click {clicks}: +{len(new)} new (total: {len(listing_articles)})")

        if new:
            consecutive_empty = 0
        else:
            consecutive_empty += 1
            if consecutive_empty >= 3:
                logger.info(f"  3 consecutive empty clicks. Stopping at click {clicks}.")
                break

        if clicks >= max_clicks:
            break

        clicked = False
        for xpath in LOAD_MORE_SELECTORS:
            try:
                btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(2)
                clicked = True
                clicks += 1
                break
            except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
                continue

        if not clicked:
            logger.info(f"  No more 'Load More' button after {clicks} clicks.")
            break

    logger.info(f"  Rappler listing: {len(listing_articles)} pairs, {len(seen_urls)} unique article URLs")

    # ── Phase 2: enrich each article URL with proper claim/verdict ─────────────
    article_urls = sorted(seen_urls)
    if not article_urls:
        return listing_articles

    logger.info(f"  Enriching {len(article_urls)} Rappler articles via JSON-LD...")
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    enriched_pairs = []
    enriched_hashes = set()
    enriched_urls_set = set()

    for i, url in enumerate(article_urls, 1):
        if i % 100 == 0:
            logger.info(f"    Enriched {i}/{len(article_urls)}")
        try:
            pairs = enrich_article_url(url, session)
            for p in pairs:
                if p["hash"] not in enriched_hashes:
                    enriched_hashes.add(p["hash"])
                    enriched_pairs.append(p)
                    enriched_urls_set.add(url)
        except Exception as e:
            logger.warning(f"    Enrich failed {url}: {e}")
        time.sleep(1)

    logger.info(f"  Rappler enriched: {len(enriched_pairs)} article-level pairs from {len(enriched_urls_set)} URLs")
    if not enriched_pairs and len(article_urls) >= 10:
        logger.error(
            f"  BUG SUSPECTED: enrichment produced 0 pairs from {len(article_urls)} URLs. "
            "The site's markup has probably changed (check _extract_claimreview_jsonld in "
            "shared_utils.py against a live article). Falling back to listing-page data."
        )

    # Return enriched pairs + fallback listing pairs for URLs that couldn't be enriched
    enriched_url_set = {p["url"] for p in enriched_pairs}
    fallback = [p for p in listing_articles if p.get("url") not in enriched_url_set]
    logger.info(f"  Rappler fallback (listing-page only): {len(fallback)} pairs")

    all_pairs = enriched_pairs + fallback
    logger.info(f"  Rappler total: {len(all_pairs)} pairs from {clicks} clicks")
    return all_pairs
