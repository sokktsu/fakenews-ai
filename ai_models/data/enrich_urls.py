"""
enrich_urls.py — Targeted Re-enrichment Tool
Re-fetches SPECIFIC article URLs that failed enrichment during a scraper run
(e.g. rate-limited Vera Files articles) and upgrades their rows in
datasets_scraped_ph_factcheck.csv from listing-page fallback quality to fully
enriched claim/verdict pairs.

How to use:
  1. Create a text file (e.g. failed.txt) and paste into it the failed URLs.
     Raw log lines are fine — URLs are extracted automatically, so you can
     paste lines exactly like:
       2026-07-04 16:02:33 | WARNING | shared_utils:_fetch_html:122 - Rate limited https://verafiles.org/articles/fact-check-... Waiting 180s...
  2. Run:
       python ai_models/data/enrich_urls.py failed.txt

  You can also pass URLs directly:
       python ai_models/data/enrich_urls.py https://verafiles.org/articles/...

Behaviour per URL:
  - Fetches the article and extracts the proper claim/verdict pairs
    (works for Rappler, Tsek.ph, and Vera Files URLs).
  - On success: DELETES that URL's old fallback rows from the CSV and
    appends the enriched rows.
  - On failure (still rate-limited etc.): leaves the old rows untouched
    and lists the URL at the end so you can retry later.

IMPORTANT: do not run this while runner_scraper.py is still running —
two processes hitting the same site doubles the rate limiting, and both
writing the CSV can corrupt it.
"""
import os, re, sys, time
import pandas as pd
from loguru import logger

import shared_utils
from shared_utils import enrich_article_url

OUTPUT_CSV  = "ai_models/data/datasets_scraped_ph_factcheck.csv"
URL_PATTERN = re.compile(r"https?://[^\s\"'<>|]+")
BASE_DELAY  = 10   # be extra polite — these URLs already rate-limited us once
MAX_DELAY   = 120

# Trailing junk that log lines / punctuation can glue onto a URL
_TRIM_CHARS = ".,;:)]}’”"


def extract_urls(sources: list[str]) -> list[str]:
    """Pull unique article URLs out of raw text lines / files / direct args."""
    urls, seen = [], set()
    for src in sources:
        if os.path.exists(src):
            with open(src, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        else:
            text = src
        for match in URL_PATTERN.findall(text):
            url = match.rstrip(_TRIM_CHARS)
            if any(d in url for d in ("rappler.com", "tsek.ph", "verafiles.org")):
                if url not in seen:
                    seen.add(url)
                    urls.append(url)
    return urls


def run(sources: list[str]):
    urls = extract_urls(sources)
    if not urls:
        logger.error("No Rappler/Tsek.ph/Vera Files URLs found in the input.")
        logger.error("Paste the log lines (or URLs) into a text file and pass its name.")
        sys.exit(1)

    if not os.path.exists(OUTPUT_CSV):
        logger.error(f"{OUTPUT_CSV} not found — run runner_scraper.py first.")
        sys.exit(1)

    df = pd.read_csv(OUTPUT_CSV)
    logger.info("=" * 60)
    logger.info("TARGETED RE-ENRICHMENT")
    logger.info(f"URLs to retry: {len(urls)} | CSV rows before: {len(df)}")
    logger.info("=" * 60)

    upgraded, failed = [], []
    delay = BASE_DELAY

    for i, url in enumerate(urls, 1):
        logger.info(f"[{i}/{len(urls)}] {url}")
        limits_before = shared_utils.RATE_LIMIT_COUNT
        try:
            pairs = enrich_article_url(url)
        except Exception as e:
            logger.warning(f"  Failed: {e}")
            pairs = []

        # Adaptive throttle: back off while the server is answering 429
        if shared_utils.RATE_LIMIT_COUNT > limits_before:
            delay = min(delay * 2, MAX_DELAY)
            logger.info(f"  Rate limited — backing off to {delay}s between URLs.")
        elif delay > BASE_DELAY:
            delay = max(BASE_DELAY, delay - 10)

        if pairs:
            old_rows = (df["url"] == url).sum()
            df = df[df["url"] != url]
            new_df = pd.DataFrame(pairs)
            # Don't re-add rows whose hash already exists elsewhere in the CSV
            new_df = new_df[~new_df["hash"].isin(set(df["hash"]))]
            df = pd.concat([df, new_df], ignore_index=True)
            upgraded.append(url)
            logger.info(f"  Upgraded: {old_rows} fallback row(s) -> {len(new_df)} enriched row(s)")
            # Save after every success so progress is never lost
            df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
        else:
            failed.append(url)
            logger.warning("  Still failing — old rows kept.")

        if i < len(urls):
            time.sleep(delay)

    logger.info("=" * 60)
    logger.info(f"DONE — upgraded {len(upgraded)}/{len(urls)} URLs | CSV rows now: {len(df)}")
    if failed:
        logger.warning(f"{len(failed)} URLs still failing (retry later, e.g. tomorrow):")
        for url in failed:
            logger.warning(f"  {url}")
        # Timestamped so consecutive runs never overwrite each other's lists
        retry_file = f"ai_models/data/enrich_retry_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(retry_file, "w", encoding="utf-8") as f:
            f.write("\n".join(failed))
        logger.warning(f"Saved them to {retry_file} — rerun with:")
        logger.warning(f"  python ai_models/data/enrich_urls.py {retry_file}")
    logger.info("Next step: python ai_models/data/prepare_dataset.py to rebuild combined_dataset.csv")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Usage: python ai_models/data/enrich_urls.py <file-with-urls-or-log-lines> [more files or URLs...]")
        sys.exit(1)
    run(sys.argv[1:])
