"""
clean_scraped.py — Junk Row Cleaner for the scraped fact-check CSV
Runs BETWEEN scraping and merging:

  runner_scraper.py  →  clean_scraped.py  →  prepare_dataset.py

Removes three kinds of noise from datasets_scraped_ph_factcheck.csv that
the scrapers can't avoid collecting:

  1. OFF-SECTION URLs (bouncer rule, deterministic)
     Rappler listing pages include sidebar/"related" links to webinars,
     FAQs and about-pages. Only /newsbreak/fact-check/ URLs are real
     fact-checks; everything else from rappler.com is dropped.

  2. META-ARTICLES (editable blocklist, heuristic)
     Yearender roundups, fact sheets, methodology/rating-system pages and
     other fact-check-industry content living at legitimate fact-check
     URLs. These aren't claim-verdict data. Extend META_SLUGS when a new
     meta format shows up — re-running this script is instant and safe.

  3. FILIPINO FALLBACK ROWS (mislabeling guard)
     "Vera Files Filipino" rows that failed enrichment were labeled by
     the ENGLISH keyword scanner, which can't read Tagalog headlines —
     ~96% defaulted to REAL regardless of the actual verdict. Enriched
     Filipino rows (correct labels via the Tagalog verdict rules) stay.

Safety: a timestamped backup of the CSV is saved before writing, and every
dropped row goes to a timestamped audit file (dropped_rows_*.csv) with the
rule that removed it — reviewable evidence for the thesis methodology.

Re-running is idempotent: already-clean files simply drop 0 rows.

Usage:
    python ai_models/data/clean_scraped.py            # clean in place
    python ai_models/data/clean_scraped.py --dry-run  # preview only, change nothing
"""
import os
import re
import sys
import shutil
import time
import pandas as pd
from loguru import logger

CSV = "ai_models/data/datasets_scraped_ph_factcheck.csv"

# Rows whose URL contains any of these slugs are meta content, not
# claim-verdict fact-checks. Editable — add new patterns as they appear.
META_SLUGS = [
    # Rappler meta / roundups (removed in the 2026-07-05 manual cleanup)
    "fact-check-rating-system",
    "rappler-fact-check-process",
    "five-things-about-fact-check",
    "fact-checkers-call-improved-mental-health",
    "updates-ifcn-talks",
    "watch-fact-checking-impact",
    "list-exaggerated-claims",
    "list-fact-checks-about",
    "common-social-media-post-fact-checked",
    "fact-check-wrap",
    "engineered-lies-how-disinformation",
    "rodrigo-duterte-playbook-disinformation",
    "non-english-speaking-countries-suffer-most-youtube",
    "open-data-helps-build-trust",
    # VERA Files meta / roundups (same category, added for consistency)
    "yearender",
    "fact-sheet",
    "what-you-want-know-about-vera-files-fact-check",
    "statement-guardians-story",
]

ENRICHED_TYPES = ["claim_article", "debunk_article"]


def find_junk(df: pd.DataFrame) -> pd.Series:
    """Return a Series of drop-reasons (empty string = keep)."""
    url = df["url"].fillna("")
    reason = pd.Series("", index=df.index)

    # Rule 1 — off-section Rappler URLs
    off_section = url.str.contains("rappler.com") & ~url.str.contains("/newsbreak/fact-check/")
    reason[off_section] = "off-section URL"

    # Rule 2 — meta-article blocklist
    meta = url.str.contains("|".join(map(re.escape, META_SLUGS)), regex=True)
    reason[meta & (reason == "")] = "meta-article slug"

    # Rule 3 — Filipino fallback rows (English keyword labels on Tagalog text)
    fil_fallback = (df["source"] == "Vera Files Filipino") & ~df["pair_type"].isin(ENRICHED_TYPES)
    reason[fil_fallback & (reason == "")] = "Filipino fallback (unreliable label)"

    return reason


def run(dry_run: bool):
    if not os.path.exists(CSV):
        logger.error(f"{CSV} not found — run runner_scraper.py first.")
        sys.exit(1)

    df = pd.read_csv(CSV)
    reason = find_junk(df)
    junk = reason != ""

    logger.info("=" * 60)
    logger.info(f"CLEAN SCRAPED CSV {'(DRY RUN — nothing will change)' if dry_run else ''}")
    logger.info("=" * 60)
    logger.info(f"rows: {len(df)} | junk found: {int(junk.sum())}")
    for why, grp in df[junk].groupby(reason[junk]):
        logger.info(f"  {why:<38} {len(grp):>5} rows ({grp['url'].nunique()} URLs)")

    if dry_run:
        for _, r in df[junk].head(15).iterrows():
            logger.info(f"    would drop: [{reason[r.name]}] {str(r['url'])[:80]}")
        logger.info("Dry run complete — re-run without --dry-run to apply.")
        return

    if not junk.any():
        logger.info("Nothing to clean — file already clean.")
        return

    stamp = time.strftime("%Y%m%d_%H%M%S")
    backup = f"ai_models/data/backup_scraped_{stamp}.csv"
    audit = f"ai_models/data/dropped_rows_{stamp}.csv"
    shutil.copy(CSV, backup)

    dropped = df[junk].copy()
    dropped["drop_reason"] = reason[junk]
    dropped.to_csv(audit, index=False, encoding="utf-8-sig")

    df[~junk].to_csv(CSV, index=False, encoding="utf-8-sig")
    logger.info(f"backup:  {backup}")
    logger.info(f"audit:   {audit} (every dropped row + its rule)")
    logger.info(f"result:  {len(df)} -> {int((~junk).sum())} rows")
    logger.info("Next step: python ai_models/data/prepare_dataset.py to rebuild combined_dataset.csv")


if __name__ == "__main__":
    run(dry_run="--dry-run" in sys.argv)
